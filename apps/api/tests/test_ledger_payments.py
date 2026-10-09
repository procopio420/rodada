from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import FulfillmentStation, Product
from modules.cash.models import CashMovement, CashPoint
from modules.ledger.models import Charge, Payment, PaymentMethod, PaymentStatus, Refund, RefundStatus
from modules.ordering.models import Tab, TabState
from modules.venue.models import Venue


class LedgerPaymentTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Financeiro", slug="financeiro")
        self.cashier = StaffMember.objects.create(display_name="Caixa", login_identifier="caixa")
        self.cashier.set_pin("1234")
        self.cashier.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.cashier, role=StaffRole.CASHIER)
        self.client = APIClient()
        response = self.client.post("/auth/login/", {"venue_slug": self.venue.slug, "login_identifier": "caixa", "pin": "1234", "installation_id": "ledger-test", "platform": "WEB"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.json()["access_token"])
        self.product = Product.objects.create(venue=self.venue, name="Brahma", price_cents=1200, fulfillment_station=FulfillmentStation.BAR)

    def order_tab(self):
        tab = self.client.post("/tabs/", {"display_label": "Financeiro"}, format="json").json()
        order = self.client.post(f"/tabs/{tab['id']}/orders/confirm/", {"idempotency_key": f"order-{tab['id']}", "lines": [{"product_id": str(self.product.id), "quantity": 2}]}, format="json")
        self.assertEqual(order.status_code, 201)
        return tab

    def test_confirmation_is_exactly_once_and_exposure_is_persisted(self):
        tab = self.order_tab()
        self.assertEqual(Charge.objects.count(), 1)
        detail = self.client.get(f"/tabs/{tab['id']}/").json()
        self.assertEqual(detail["charges_cents"], 2400)
        self.assertEqual(detail["exposure_cents"], 2400)

    def test_partial_payment_then_close_requires_zero_balance(self):
        tab = self.order_tab()
        early = self.client.post(f"/tabs/{tab['id']}/close/", {}, format="json")
        self.assertEqual(early.status_code, 409)
        partial = self.client.post(f"/tabs/{tab['id']}/payments/", {"amount_cents": 1000, "method": "CARD", "idempotency_key": "p1"}, format="json")
        self.assertEqual(partial.status_code, 201)
        self.assertEqual(partial.json()["exposure_cents"], 1400)
        final = self.client.post(f"/tabs/{tab['id']}/payments/", {"amount_cents": 1400, "method": "CARD", "idempotency_key": "p2"}, format="json")
        self.assertEqual(final.json()["exposure_cents"], 0)
        closed = self.client.post(f"/tabs/{tab['id']}/close/", {}, format="json")
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.json()["state"], TabState.CLOSED)

    def test_payment_replay_is_idempotent_and_overpayment_rejected(self):
        tab = self.order_tab()
        payload = {"amount_cents": 1200, "method": "PIX", "idempotency_key": "same"}
        first = self.client.post(f"/tabs/{tab['id']}/payments/", payload, format="json")
        second = self.client.post(f"/tabs/{tab['id']}/payments/", payload, format="json")
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(Payment.objects.count(), 1)
        excess = self.client.post(f"/tabs/{tab['id']}/payments/", {"amount_cents": 1300, "method": "CASH", "idempotency_key": "excess"}, format="json")
        self.assertEqual(excess.status_code, 409)

    def test_provider_payment_method_cannot_be_manually_confirmed(self):
        tab = self.order_tab()
        response = self.client.post(
            f"/tabs/{tab['id']}/payments/",
            {"amount_cents": 1000, "method": "TAP_TO_PAY", "idempotency_key": "tap-1"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "PAYMENT_METHOD_UNAVAILABLE")
        self.assertEqual(Payment.objects.count(), 0)

    def test_committed_payment_replay_after_close_recovers_original_receipt(self):
        tab = self.order_tab()
        path = f"/tabs/{tab['id']}/payments/"
        payload = {"amount_cents": 2400, "method": "EXTERNAL_TERMINAL", "idempotency_key": "settled"}
        first = self.client.post(path, payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.client.post(f"/tabs/{tab['id']}/close/", {}, format="json").status_code, 200)
        replay = self.client.post(path, payload, format="json")
        self.assertEqual(replay.status_code, 201, replay.json())
        self.assertEqual(replay.json()["id"], first.json()["id"])
        conflict = self.client.post(path, {**payload, "amount_cents": 1200}, format="json")
        self.assertEqual(conflict.json()["code"], "IDEMPOTENCY_CONFLICT")
        new = self.client.post(path, {**payload, "idempotency_key": "new"}, format="json")
        self.assertEqual(new.json()["code"], "TAB_CLOSED")
        self.assertEqual(Payment.objects.count(), 1)

    def test_invalid_manual_payment_payload_cannot_truncate_cents_or_crash(self):
        tab = self.order_tab()
        payload = {"amount_cents": 1200, "method": "EXTERNAL_TERMINAL", "idempotency_key": "invalid"}
        invalid = [1.9, True, 2147483648, "nan", None]
        bodies = [{**payload, "amount_cents": amount} for amount in invalid]
        bodies += [{**payload, "idempotency_key": []}, {**payload, "cash_point_id": "bad"}, []]
        for body in bodies:
            with self.subTest(body=body):
                response = self.client.post(f"/tabs/{tab['id']}/payments/", body, format="json")
                self.assertEqual(response.status_code, 400, response.json())
                self.assertEqual(response.json()["code"], "INVALID_PAYMENT")
        self.assertFalse(Payment.objects.exists())

    def manager_client(self):
        manager = StaffMember.objects.create(display_name="Gerente", login_identifier="gerente")
        manager.set_pin("4321")
        manager.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=manager, role=StaffRole.MANAGER)
        client = APIClient()
        response = client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": "gerente",
                "pin": "4321",
                "installation_id": "refund-manager-test",
                "platform": "WEB",
            },
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION="Bearer " + response.json()["access_token"])
        return manager, client

    def test_invalid_refund_payload_cannot_truncate_cents_or_crash(self):
        tab = self.order_tab()
        payment = self.client.post(
            f"/tabs/{tab['id']}/payments/",
            {"amount_cents": 1200, "method": "EXTERNAL_TERMINAL", "idempotency_key": "refund-source"},
            format="json",
        ).json()
        _, manager = self.manager_client()
        manager.post("/auth/reauthenticate/", {"pin": "4321"}, format="json")
        payload = {"amount_cents": 100, "idempotency_key": "invalid-refund", "reason": "QA"}
        bodies = [{**payload, "amount_cents": amount} for amount in (1.9, True, 2147483648, None)]
        bodies += [[], {**payload, "cash_point_id": "bad"}]
        for body in bodies:
            response = manager.post(f"/payments/{payment['id']}/refunds/", body, format="json")
            self.assertEqual(response.status_code, 400, response.json())
            self.assertEqual(response.json()["code"], "INVALID_REFUND")
        self.assertFalse(Refund.objects.exists())

    def test_only_confirmed_money_counts_and_authorized_refund_is_append_only(self):
        tab = self.order_tab()
        collected = self.client.post(
            f"/tabs/{tab['id']}/payments/",
            {"amount_cents": 1200, "method": "OTHER", "idempotency_key": "manual-1"},
            format="json",
        )
        self.assertEqual(collected.status_code, 201)
        self.assertEqual(collected.json()["status"], PaymentStatus.CONFIRMED)

        Payment.objects.create(
            tab_id=tab["id"],
            amount_cents=500,
            method=PaymentMethod.TAP_TO_PAY,
            idempotency_key="provider-pending",
            status=PaymentStatus.CONFIRMATION_PENDING,
            received_by=self.cashier,
        )
        before_refund = self.client.get(f"/tabs/{tab['id']}/").json()
        self.assertEqual(before_refund["payments_cents"], 1200)
        self.assertEqual(before_refund["refunds_cents"], 0)
        self.assertEqual(before_refund["exposure_cents"], 1200)

        forbidden = self.client.post(
            f"/payments/{collected.json()['id']}/refunds/",
            {"amount_cents": 500, "idempotency_key": "r1", "reason": "Item indisponível"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 403)

        manager, manager_client = self.manager_client()
        payload = {"amount_cents": 500, "idempotency_key": "r1", "reason": "Item indisponível"}
        reauth_required = manager_client.post(
            f"/payments/{collected.json()['id']}/refunds/", payload, format="json"
        )
        self.assertEqual(reauth_required.status_code, 403)
        self.assertEqual(reauth_required.json()["code"], "REAUTH_REQUIRED")
        reauth = manager_client.post("/auth/reauthenticate/", {"pin": "4321"}, format="json")
        self.assertEqual(reauth.status_code, 200, reauth.json())
        first = manager_client.post(f"/payments/{collected.json()['id']}/refunds/", payload, format="json")
        replay = manager_client.post(f"/payments/{collected.json()['id']}/refunds/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()["id"], replay.json()["id"])
        self.assertEqual(Refund.objects.count(), 1)
        self.assertEqual(first.json()["payments_cents"], 1200)
        self.assertEqual(first.json()["refunds_cents"], 500)
        self.assertEqual(first.json()["exposure_cents"], 1700)

        payment = Payment.objects.get(pk=collected.json()["id"])
        self.assertEqual(payment.status, PaymentStatus.PARTIALLY_REFUNDED)
        audit = AuditEvent.objects.get(event_type="payment.refunded")
        self.assertEqual(audit.actor_staff_id, manager.id)
        self.assertIsNotNone(audit.actor_session_id)
        self.assertEqual(audit.metadata["payment_id"], str(payment.id))

        over_refund = manager_client.post(
            f"/payments/{payment.id}/refunds/",
            {"amount_cents": 701, "idempotency_key": "r2", "reason": "too much"},
            format="json",
        )
        self.assertEqual(over_refund.status_code, 409)
        self.assertEqual(over_refund.json()["code"], "REFUND_EXCEEDS_PAYMENT")

    def test_cash_payment_requires_active_drawer_and_creates_movement_atomically(self):
        tab = self.order_tab()
        missing = self.client.post(
            f"/tabs/{tab['id']}/payments/",
            {"amount_cents": 1200, "method": "CASH", "idempotency_key": "cash-missing"},
            format="json",
        )
        self.assertEqual(missing.status_code, 409)
        self.assertEqual(missing.json()["code"], "CASH_POINT_REQUIRED")
        self.assertEqual(Payment.objects.count(), 0)

        point = CashPoint.objects.create(venue=self.venue, label="Gaveta")
        opened = self.client.post(
            "/cash/shifts/",
            {
                "cash_point_id": str(point.id),
                "opening_float_cents": 5000,
                "business_date": "2026-10-07",
                "idempotency_key": "open-gaveta",
            },
            format="json",
        )
        self.assertEqual(opened.status_code, 201, opened.json())
        paid = self.client.post(
            f"/tabs/{tab['id']}/payments/",
            {
                "amount_cents": 1200,
                "amount_tendered_cents": 2000,
                "cash_point_id": str(point.id),
                "method": "CASH",
                "idempotency_key": "cash-drawer",
            },
            format="json",
        )
        self.assertEqual(paid.status_code, 201, paid.json())
        payment = Payment.objects.get(pk=paid.json()["id"])
        movement = CashMovement.objects.get(payment=payment)
        self.assertEqual(movement.amount_cents, 1200)
        self.assertEqual(payment.cash_tender_detail.change_given_cents, 800)

    def test_cash_shift_detail_is_a_complete_recovery_snapshot(self):
        point = CashPoint.objects.create(venue=self.venue, label="Gaveta de recuperação")
        opened = self.client.post(
            "/cash/shifts/",
            {
                "cash_point_id": str(point.id),
                "opening_float_cents": 5000,
                "business_date": "2026-10-07",
                "idempotency_key": "open-recovery-snapshot",
            },
            format="json",
        )
        self.assertEqual(opened.status_code, 201, opened.json())

        # A client that loses the open response must be able to parse this as
        # the same snapshot returned by the opening command, not just a close
        # preview. This is the native recovery boundary after process death.
        detail = self.client.get(f"/cash/shifts/{opened.json()['id']}/")
        self.assertEqual(detail.status_code, 200, detail.json())
        payload = detail.json()
        self.assertEqual(payload["id"], opened.json()["id"])
        self.assertEqual(payload["cash_point_id"], str(point.id))
        self.assertEqual(payload["opening_float_cents"], 5000)
        self.assertEqual(payload["expected_cents"], 5000)
        self.assertEqual(payload["movements"][0]["kind"], "OPENING_FLOAT")

    def test_cash_discrepancy_review_requires_manager_reauthentication(self):
        point = CashPoint.objects.create(venue=self.venue, label="Gaveta revisão")
        opened = self.client.post(
            "/cash/shifts/",
            {
                "cash_point_id": str(point.id),
                "opening_float_cents": 5000,
                "business_date": "2026-10-07",
                "idempotency_key": "open-review",
            },
            format="json",
        )
        self.assertEqual(opened.status_code, 201, opened.json())
        shift_id = opened.json()["id"]
        counting = self.client.post(f"/cash/shifts/{shift_id}/count/start/", {}, format="json")
        self.assertEqual(counting.status_code, 200, counting.json())
        closed = self.client.post(
            f"/cash/shifts/{shift_id}/close/",
            {"counted_amount_cents": 4900, "expected_version": counting.json()["version"]},
            format="json",
        )
        self.assertEqual(closed.status_code, 200, closed.json())
        self.assertEqual(closed.json()["review_status"], "PENDING")

        points = self.client.get("/cash/points/")
        self.assertEqual(points.status_code, 200, points.json())
        review_shift = points.json()["results"][0]["pending_review_shift"]
        self.assertEqual(review_shift["id"], shift_id)
        self.assertEqual(review_shift["review_status"], "PENDING")

        _, manager_client = self.manager_client()
        payload = {"reason": "Diferença conferida com o cofre."}
        required = manager_client.post(f"/cash/shifts/{shift_id}/review/", payload, format="json")
        self.assertEqual(required.status_code, 403)
        self.assertEqual(required.json()["code"], "REAUTH_REQUIRED")
        self.assertEqual(
            manager_client.post("/auth/reauthenticate/", {"pin": "4321"}, format="json").status_code,
            200,
        )
        reviewed = manager_client.post(f"/cash/shifts/{shift_id}/review/", payload, format="json")
        self.assertEqual(reviewed.status_code, 200, reviewed.json())
        self.assertEqual(reviewed.json()["review_status"], "REVIEWED")

    def test_pending_refund_does_not_change_exposure(self):
        tab = self.order_tab()
        payment = Payment.objects.create(
            tab_id=tab["id"],
            amount_cents=1000,
            method=PaymentMethod.CASH,
            idempotency_key="confirmed-manual",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.cashier,
        )
        Refund.objects.create(
            payment=payment,
            amount_cents=400,
            idempotency_key="provider-refund-pending",
            status=RefundStatus.PENDING,
            created_by=self.cashier,
        )
        detail = self.client.get(f"/tabs/{tab['id']}/").json()
        self.assertEqual(detail["payments_cents"], 1000)
        self.assertEqual(detail["refunds_cents"], 0)
        self.assertEqual(detail["exposure_cents"], 1400)
