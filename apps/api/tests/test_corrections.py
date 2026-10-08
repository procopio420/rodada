from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import FulfillmentStation, Product
from modules.corrections.models import (
    CorrectionKind,
    CorrectionStatus,
    FinancialDisposition,
    OrderCorrection,
    WasteKind,
    WasteMarker,
)
from modules.corrections.services import (
    CorrectionServiceError,
    cancel_before_fulfillment,
    create_post_production_correction,
)
from modules.ledger.models import Charge, LedgerAdjustment, Payment, PaymentMethod, PaymentStatus
from modules.ledger.services import reverse_open_responsibility, totals
from modules.ordering.models import Order, OrderItem, OrderItemState, OrderSource, Tab
from modules.venue.models import Venue


class CorrectionFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Correções", slug="corrections-bar")
        self.other_venue = Venue.objects.create(name="Outro", slug="corrections-other")
        self.staff = StaffMember.objects.create(
            display_name="Ana", login_identifier="corrections-ana"
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.STAFF
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "corrections-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.actor = ActorContext.from_session(StaffSession.objects.get(venue=self.venue))

    def item(self, *, state=OrderItemState.ACCEPTED, venue=None, tab=None, name="Cerveja"):
        venue = venue or self.venue
        tab = tab or Tab.objects.create(venue=venue, display_label="Ana")
        product = Product.objects.create(
            venue=venue,
            name=name,
            price_cents=1200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        order = Order.objects.create(tab=tab, source=OrderSource.STAFF)
        return OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            unit_price_cents=product.price_cents,
            quantity=1,
            state=state,
            accepted_at=timezone.now() if state == OrderItemState.ACCEPTED else None,
        )

    def cancel(self, item, *, key="cancel-1", reason_code="WRONG_ENTRY", hook=None):
        return cancel_before_fulfillment(
            item_id=item.id,
            kind=CorrectionKind.WRONG_ITEM_ENTERED,
            reason_code=reason_code,
            reason_text="Lançamento duplicado",
            idempotency_key=key,
            actor=self.actor,
            financial_reversal_hook=hook,
        )

    def test_cancel_preserves_snapshot_and_records_append_only_correction_after_reversal_hook(self):
        item = self.item()
        hook_calls = []

        def append_real_reversal(correction, hooked_item, actor):
            hook_calls.append((correction.id, hooked_item.id, actor.staff_id))

        correction = self.cancel(item, hook=append_real_reversal)
        item.refresh_from_db()

        assert correction.status == CorrectionStatus.APPLIED
        assert correction.stage_at_request == OrderItemState.ACCEPTED
        assert correction.kind == CorrectionKind.WRONG_ITEM_ENTERED
        assert correction.financial_disposition == FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY
        assert correction.requested_by_id == self.staff.id
        assert correction.approved_by_id == self.staff.id
        assert correction.applied_at is not None
        assert hook_calls == [(correction.id, item.id, self.staff.id)]
        assert item.state == OrderItemState.CANCELLED
        assert item.cancelled_at is not None
        assert item.product_name_snapshot == "Cerveja"
        assert item.unit_price_cents == 1200
        assert AuditEvent.objects.filter(
            event_type="order_item.cancelled", entity_id=str(correction.id), reason="WRONG_ENTRY"
        ).exists()

    def test_same_idempotency_key_replays_without_second_reversal_or_correction(self):
        item = self.item()
        hook_calls = []

        def hook(*args):
            hook_calls.append(args[0].id)

        first = self.cancel(item, key="replay-cancel", hook=hook)
        replay = self.cancel(item, key="replay-cancel", hook=hook)

        assert replay.id == first.id
        assert replay._idempotency_replay is True
        assert hook_calls == [first.id]
        assert OrderCorrection.objects.filter(original_order_item=item).count() == 1
        assert AuditEvent.objects.filter(event_type="order_item.cancelled").count() == 1

    def test_same_idempotency_key_with_different_intent_is_rejected(self):
        item = self.item()
        self.cancel(item, key="fixed-key", hook=lambda *_: None)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, key="fixed-key", reason_code="CUSTOMER_LEFT", hook=lambda *_: None)

        assert captured.exception.code == "IDEMPOTENCY_CONFLICT"

    def test_no_canonical_cancellation_occurs_without_ledger_reversal_hook(self):
        item = self.item()

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=None)

        assert captured.exception.code == "FINANCIAL_REVERSAL_INTEGRATION_REQUIRED"
        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED
        assert not OrderCorrection.objects.filter(original_order_item=item).exists()

    def test_real_reversal_is_append_only_and_offsets_open_exposure_once(self):
        item = self.item()
        charge = Charge.objects.create(
            tab=item.order.tab,
            order_item=item,
            amount_cents=item.line_total_cents,
        )

        correction = self.cancel(item, key="real-reversal", hook=reverse_open_responsibility)
        item.refresh_from_db()

        adjustment = LedgerAdjustment.objects.get(pk=correction.financial_adjustment_id)
        assert adjustment.order_item_id == item.id
        assert adjustment.amount_cents == -1200
        assert adjustment.created_by_id == self.staff.id
        assert Charge.objects.get(pk=charge.id).amount_cents == 1200
        assert totals(item.order.tab)["charges_cents"] == 1200
        assert totals(item.order.tab)["adjustments_cents"] == -1200
        assert totals(item.order.tab)["exposure_cents"] == 0
        assert item.state == OrderItemState.CANCELLED
        assert AuditEvent.objects.filter(
            event_type="charge.reversed", entity_id=str(adjustment.id)
        ).exists()

        replay = self.cancel(item, key="real-reversal", hook=reverse_open_responsibility)
        assert replay.id == correction.id
        assert LedgerAdjustment.objects.filter(order_item=item).count() == 1

    def test_staff_endpoint_cancels_unpaid_item_with_canonical_reversal(self):
        item = self.item()
        Charge.objects.create(tab=item.order.tab, order_item=item, amount_cents=1200)
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "corrections-unpaid-api-device",
                "platform": "WEB",
            },
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        body = {
            "kind": CorrectionKind.CANCEL_ITEM,
            "reason_code": "DUPLICATE_ENTRY",
            "reason_text": "Pedido repetido",
            "idempotency_key": "unpaid-cancel-request",
        }

        first = self.client.post(f"/order-items/{item.id}/corrections/cancel/", body, format="json")
        replay = self.client.post(f"/order-items/{item.id}/corrections/cancel/", body, format="json")
        item.refresh_from_db()

        assert first.status_code == 201, first.json()
        assert replay.status_code == 200, replay.json()
        assert first.json()["id"] == replay.json()["id"]
        assert first.json()["order_item_state"] == OrderItemState.CANCELLED
        assert first.json()["adjustments_cents"] == -1200
        assert first.json()["exposure_cents"] == 0
        assert item.state == OrderItemState.CANCELLED
        assert LedgerAdjustment.objects.filter(order_item=item).count() == 1

    def test_failed_reversal_rolls_back_correction_and_operational_cancellation(self):
        item = self.item()

        def failed_reversal(*args):
            raise RuntimeError("ledger unavailable")

        with self.assertRaises(RuntimeError):
            self.cancel(item, hook=failed_reversal)

        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED
        assert not OrderCorrection.objects.filter(original_order_item=item).exists()
        assert not AuditEvent.objects.filter(event_type="order_item.cancelled").exists()

    def test_preparing_item_requires_later_manager_correction_path(self):
        item = self.item(state=OrderItemState.PREPARING)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=lambda *_: None)

        assert captured.exception.code == "CORRECTION_STAGE_REQUIRES_APPROVAL"
        item.refresh_from_db()
        assert item.state == OrderItemState.PREPARING

    def test_confirmed_money_requires_refund_or_courtesy_orchestration(self):
        item = self.item()
        Payment.objects.create(
            tab=item.order.tab,
            amount_cents=1200,
            method=PaymentMethod.CASH,
            idempotency_key="paid-correction",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(item, hook=lambda *_: self.fail("hook must not run"))

        assert captured.exception.code == "PAID_CORRECTION_REQUIRES_REFUND"
        item.refresh_from_db()
        assert item.state == OrderItemState.ACCEPTED

    def test_staff_endpoint_records_refund_required_without_mutating_paid_item(self):
        item = self.item()
        Charge.objects.create(tab=item.order.tab, order_item=item, amount_cents=1200)
        Payment.objects.create(
            tab=item.order.tab,
            amount_cents=1200,
            method=PaymentMethod.CASH,
            idempotency_key="paid-endpoint-correction",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "corrections-api-device",
                "platform": "WEB",
            },
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        body = {
            "kind": CorrectionKind.WRONG_ITEM_ENTERED,
            "reason_code": "WRONG_ENTRY",
            "reason_text": "Cliente recebeu o item errado",
            "idempotency_key": "paid-cancel-request",
        }

        first = self.client.post(f"/order-items/{item.id}/corrections/cancel/", body, format="json")
        replay = self.client.post(f"/order-items/{item.id}/corrections/cancel/", body, format="json")
        item.refresh_from_db()

        assert first.status_code == 202, first.json()
        assert replay.status_code == 200, replay.json()
        assert first.json()["id"] == replay.json()["id"]
        assert first.json()["financial_disposition"] == FinancialDisposition.REFUND_REQUIRED
        assert item.state == OrderItemState.ACCEPTED
        assert LedgerAdjustment.objects.count() == 0
        assert AuditEvent.objects.filter(event_type="order_item.refund_required").exists()

    def test_manager_settles_partial_paid_cancellation_with_refund_and_reversal(self):
        item = self.item()
        Charge.objects.create(tab=item.order.tab, order_item=item, amount_cents=1200)
        payment = Payment.objects.create(
            tab=item.order.tab,
            amount_cents=500,
            method=PaymentMethod.OTHER,
            idempotency_key="partial-paid-correction",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )
        pending = cancel_before_fulfillment(
            item_id=item.id,
            kind=CorrectionKind.CANCEL_ITEM,
            reason_code="CUSTOMER_LEFT",
            reason_text="Cliente desistiu antes da produção",
            idempotency_key="partial-paid-cancel",
            actor=self.actor,
            financial_reversal_hook=reverse_open_responsibility,
            record_paid_request=True,
        )
        manager = StaffMember.objects.create(display_name="Gerente", login_identifier="corrections-manager")
        manager.set_pin("4321")
        manager.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=manager, role=StaffRole.MANAGER
        )
        manager_client = APIClient()
        login = manager_client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": manager.login_identifier,
                "pin": "4321",
                "installation_id": "corrections-settlement-device",
                "platform": "WEB",
            },
            format="json",
        )
        manager_client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        body = {
            "payment_id": str(payment.id),
            "amount_cents": 500,
            "refund_idempotency_key": "partial-paid-refund",
        }

        denied = manager_client.post(f"/corrections/{pending.id}/settle-refund/", body, format="json")
        assert denied.status_code == 403
        assert denied.json()["code"] == "REAUTH_REQUIRED"
        reauth = manager_client.post("/auth/reauthenticate/", {"pin": "4321"}, format="json")
        assert reauth.status_code == 200, reauth.json()
        settled = manager_client.post(f"/corrections/{pending.id}/settle-refund/", body, format="json")
        replay = manager_client.post(f"/corrections/{pending.id}/settle-refund/", body, format="json")
        item.refresh_from_db()
        pending.refresh_from_db()

        assert settled.status_code == 201, settled.json()
        assert replay.status_code == 200, replay.json()
        assert settled.json()["refund_id"] == replay.json()["refund_id"]
        assert settled.json()["adjustments_cents"] == -1200
        assert settled.json()["refunds_cents"] == 500
        assert settled.json()["exposure_cents"] == 0
        assert item.state == OrderItemState.CANCELLED
        assert pending.status == CorrectionStatus.APPLIED
        assert pending.refund_id is not None
        assert pending.financial_adjustment_id is not None
        assert AuditEvent.objects.filter(event_type="order_item.cancelled_after_refund").exists()

    def test_other_venue_cannot_cancel_item(self):
        other_item = self.item(venue=self.other_venue)

        with self.assertRaises(CorrectionServiceError) as captured:
            self.cancel(other_item, hook=lambda *_: None)

        assert captured.exception.code == "ORDER_ITEM_NOT_FOUND"

    def test_replacement_link_and_waste_marker_are_separate_operational_history(self):
        original = self.item()
        replacement = self.item(tab=original.order.tab, name="Cerveja sem gelo")
        correction = OrderCorrection.objects.create(
            venue=self.venue,
            original_order_item=original,
            replacement_order_item=replacement,
            kind=CorrectionKind.REPLACEMENT,
            stage_at_request=original.state,
            status=CorrectionStatus.APPLIED,
            reason_code="WRONG_ITEM",
            financial_disposition=FinancialDisposition.MANUAL_REVIEW_REQUIRED,
            idempotency_key="replacement-link",
            request_fingerprint="a" * 64,
            requested_by=self.staff,
            approved_by=self.staff,
            applied_at=timezone.now(),
        )
        waste = WasteMarker.objects.create(
            venue=self.venue,
            order_item=original,
            correction=correction,
            kind=WasteKind.PREPARED_NOT_SERVED,
            quantity=1,
            reason="Item incorreto descartado",
            created_by=self.staff,
            occurred_at=timezone.now() - timedelta(minutes=1),
        )

        assert correction.original_order_item_id == original.id
        assert correction.replacement_order_item_id == replacement.id
        assert waste.correction_id == correction.id
        assert original.product_name_snapshot == "Cerveja"

    def manager_actor(self):
        if hasattr(self, "_manager_actor"):
            return self._manager_actor
        manager = StaffMember.objects.create(
            display_name="Gerente correções", login_identifier="corrections-post-production-manager"
        )
        manager.set_pin("4321")
        manager.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=manager, role=StaffRole.MANAGER
        )
        session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=manager,
            membership=VenueStaffMembership.objects.get(venue=self.venue, staff_member=manager),
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self._manager_actor = ActorContext.from_session(session)
        return self._manager_actor

    def test_remake_after_preparing_creates_new_work_and_courtesy_without_second_exposure(self):
        original = self.item(state=OrderItemState.PREPARING)
        Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)

        correction = create_post_production_correction(
            item_id=original.id,
            kind=CorrectionKind.REMAKE,
            reason_code="STATION_MISTAKE",
            reason_text="Copo quebrou no passe",
            idempotency_key="remake-preparing",
            actor=self.manager_actor(),
        )
        original.refresh_from_db()
        replacement = correction.replacement_order_item

        self.assertEqual(correction.status, CorrectionStatus.APPLIED)
        self.assertEqual(correction.financial_disposition, FinancialDisposition.COURTESY_REPLACEMENT)
        self.assertEqual(original.state, OrderItemState.CANCELLED)
        self.assertEqual(replacement.state, OrderItemState.NEW)
        self.assertEqual(replacement.product_name_snapshot, "Cerveja")
        self.assertEqual(totals(original.order.tab)["exposure_cents"], 1200)
        self.assertEqual(correction.financial_adjustment.amount_cents, -1200)
        self.assertTrue(AuditEvent.objects.filter(event_type="order_item.remake_created").exists())

        replay = create_post_production_correction(
            item_id=original.id,
            kind=CorrectionKind.REMAKE,
            reason_code="STATION_MISTAKE",
            reason_text="Copo quebrou no passe",
            idempotency_key="remake-preparing",
            actor=self.manager_actor(),
        )
        self.assertEqual(replay.id, correction.id)
        self.assertEqual(OrderCorrection.objects.filter(original_order_item=original).count(), 1)

    def test_manager_can_cancel_preparing_item_with_reversal_and_waste_history(self):
        original = self.item(state=OrderItemState.PREPARING)
        Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)

        correction = create_post_production_correction(
            item_id=original.id,
            kind=CorrectionKind.CANCEL_ITEM,
            reason_code="CUSTOMER_LEFT",
            reason_text="Cliente cancelou durante o preparo",
            idempotency_key="cancel-preparing",
            actor=self.manager_actor(),
        )
        original.refresh_from_db()

        self.assertEqual(correction.status, CorrectionStatus.APPLIED)
        self.assertEqual(correction.financial_disposition, FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY)
        self.assertEqual(original.state, OrderItemState.CANCELLED)
        self.assertEqual(totals(original.order.tab)["exposure_cents"], 0)
        waste = WasteMarker.objects.get(correction=correction)
        self.assertEqual(waste.kind, WasteKind.PREPARED_NOT_SERVED)
        self.assertEqual(waste.quantity, 1)
        self.assertTrue(AuditEvent.objects.filter(event_type="order_item.cancelled_after_production").exists())

    def test_ready_cancellation_cancels_delivery_and_requires_exact_refund_when_paid(self):
        from modules.dispatch.models import DispatchTask, DispatchTaskState, DispatchTaskType
        from modules.corrections.services import settle_refund_required_cancellation

        original = self.item(state=OrderItemState.READY)
        Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)
        payment = Payment.objects.create(
            tab=original.order.tab,
            amount_cents=500,
            method=PaymentMethod.OTHER,
            idempotency_key="ready-cancel-payment",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )
        task = DispatchTask.objects.create(
            venue=self.venue,
            task_type=DispatchTaskType.DELIVERY,
            order_item=original,
            state=DispatchTaskState.OPEN,
            ready_at=timezone.now(),
        )
        manager_actor = self.manager_actor()
        correction = create_post_production_correction(
            item_id=original.id,
            kind=CorrectionKind.CANCEL_ITEM,
            reason_code="CUSTOMER_REJECTED",
            reason_text="Cliente desistiu antes da entrega",
            idempotency_key="cancel-ready-paid",
            actor=manager_actor,
        )
        original.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(original.state, OrderItemState.CANCELLED)
        self.assertEqual(task.state, DispatchTaskState.CANCELLED)
        self.assertEqual(correction.status, CorrectionStatus.REQUESTED)
        self.assertEqual(correction.financial_disposition, FinancialDisposition.REFUND_REQUIRED)
        self.assertEqual(correction.refund_required_cents, 500)
        self.assertEqual(totals(original.order.tab)["exposure_cents"], -500)

        settled, refund, result = settle_refund_required_cancellation(
            correction_id=correction.id,
            payment_id=payment.id,
            amount_cents=500,
            refund_idempotency_key="ready-cancel-refund",
            cash_point_id=None,
            actor=manager_actor,
        )
        self.assertEqual(settled.status, CorrectionStatus.APPLIED)
        self.assertEqual(refund.amount_cents, 500)
        self.assertEqual(result["exposure_cents"], 0)

    def test_post_production_cancel_endpoint_requires_recent_manager_reauthentication(self):
        original = self.item(state=OrderItemState.PREPARING)
        Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)
        self.manager_actor()
        manager_client = APIClient()
        login = manager_client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": "corrections-post-production-manager",
                "pin": "4321",
                "installation_id": "post-production-correction-device",
                "platform": "WEB",
            },
            format="json",
        )
        manager_client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        payload = {
            "kind": CorrectionKind.CANCEL_ITEM,
            "reason_code": "CUSTOMER_LEFT",
            "reason_text": "Desistiu durante o preparo",
            "idempotency_key": "endpoint-post-production-cancel",
        }
        denied = manager_client.post(
            f"/order-items/{original.id}/corrections/post-production/", payload, format="json"
        )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(denied.json()["code"], "REAUTH_REQUIRED")
        self.assertEqual(
            manager_client.post("/auth/reauthenticate/", {"pin": "4321"}, format="json").status_code,
            200,
        )
        accepted = manager_client.post(
            f"/order-items/{original.id}/corrections/post-production/", payload, format="json"
        )
        self.assertEqual(accepted.status_code, 201, accepted.json())
        self.assertEqual(accepted.json()["order_item_state"], OrderItemState.CANCELLED)
        self.assertEqual(accepted.json()["original_line_total_cents"], 1200)
        self.assertIsNone(accepted.json()["replacement_line_total_cents"])
        self.assertEqual(accepted.json()["financial_delta_cents"], -1200)

    def test_replacement_price_difference_is_append_only_and_deterministic(self):
        for price, expected in ((1200, 1200), (900, 900), (1500, 1500)):
            with self.subTest(price=price):
                original = self.item(state=OrderItemState.READY, name=f"Cerveja original {price}")
                Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)
                target = Product.objects.create(
                    venue=self.venue,
                    name=f"Substituto {price}",
                    price_cents=price,
                    fulfillment_station=FulfillmentStation.BAR,
                )
                correction = create_post_production_correction(
                    item_id=original.id,
                    kind=CorrectionKind.REPLACEMENT,
                    reason_code="WRONG_ITEM",
                    reason_text="Cliente pediu outra bebida",
                    idempotency_key=f"replacement-{price}",
                    replacement_product_id=target.id,
                    actor=self.manager_actor(),
                )
                original.refresh_from_db()
                self.assertEqual(correction.status, CorrectionStatus.APPLIED)
                self.assertEqual(correction.replacement_order_item.unit_price_cents, price)
                self.assertEqual(original.state, OrderItemState.CANCELLED)
                self.assertEqual(totals(original.order.tab)["exposure_cents"], expected)
                self.assertEqual(correction.financial_adjustment.amount_cents, -1200)

    def test_paid_cheaper_replacement_requires_exact_refund_without_rewriting_payment(self):
        original = self.item(state=OrderItemState.READY)
        Charge.objects.create(tab=original.order.tab, order_item=original, amount_cents=1200)
        payment = Payment.objects.create(
            tab=original.order.tab,
            amount_cents=1200,
            method=PaymentMethod.OTHER,
            idempotency_key="paid-replacement",
            status=PaymentStatus.CONFIRMED,
            confirmed_at=timezone.now(),
            received_by=self.staff,
        )
        cheaper = Product.objects.create(
            venue=self.venue, name="Suco", price_cents=900, fulfillment_station=FulfillmentStation.BAR
        )
        manager_actor = self.manager_actor()
        correction = create_post_production_correction(
            item_id=original.id,
            kind=CorrectionKind.REPLACEMENT,
            reason_code="CUSTOMER_REJECTED",
            reason_text="Produto indisponível",
            idempotency_key="paid-cheaper-replacement",
            replacement_product_id=cheaper.id,
            actor=manager_actor,
        )
        self.assertEqual(correction.status, CorrectionStatus.REQUESTED)
        self.assertEqual(correction.financial_disposition, FinancialDisposition.REFUND_REQUIRED)
        self.assertEqual(correction.refund_required_cents, 300)
        self.assertEqual(totals(original.order.tab)["exposure_cents"], -300)

        with self.assertRaises(CorrectionServiceError) as captured:
            from modules.corrections.services import settle_refund_required_cancellation
            settle_refund_required_cancellation(
                correction_id=correction.id, payment_id=payment.id, amount_cents=200,
                refund_idempotency_key="wrong-paid-replacement-refund", cash_point_id=None, actor=manager_actor,
            )
        self.assertEqual(captured.exception.code, "REFUND_AMOUNT_MISMATCH")
