import secrets
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.corrections.models import OrderCorrection, WasteMarker
from modules.corrections.services import CorrectionServiceError, create_post_production_correction
from modules.ledger.models import Charge, LedgerAdjustment, Payment, PaymentStatus, Refund
from modules.ledger.services import totals
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


class WrongEntryFixture:
    def setUp(self):
        self.venue = Venue.objects.create(name="Estabelecimento de teste", slug="wrong-entry-test")
        self.staff = StaffMember.objects.create(display_name="Operador de teste", login_identifier="wrong-entry-operator")
        self.pin = str(secrets.randbelow(900000) + 100000)
        self.staff.set_pin(self.pin)
        self.staff.save()
        self.membership = VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {"venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": self.pin, "installation_id": "wrong-entry-test", "platform": "WEB"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.actor = ActorContext.from_session(StaffSession.objects.get(venue=self.venue))
        self.tab = Tab.objects.create(venue=self.venue)
        product = Product.objects.create(venue=self.venue, name="Item do catálogo", price_cents=800, fulfillment_station="BAR")
        self.item = OrderItem.objects.create(order=Order.objects.create(tab=self.tab, source="STAFF"), product=product,
            product_name_snapshot=product.name, unit_price_cents=800, quantity=3, state="DELIVERED", delivered_at=timezone.now())
        Charge.objects.create(tab=self.tab, order_item=self.item, amount_cents=2400)

    def command(self, quantity=1, key="wrong-entry-command", **changes):
        return {"item_id": self.item.id, "actor": self.actor, "kind": "WRONG_ITEM_ENTERED", "reason_code": "WRONG_ENTRY",
            "reason_text": "Quantidade lançada a mais no teste", "idempotency_key": key, "quantity": quantity, **changes}


class WrongEntryQuantityTests(WrongEntryFixture, TestCase):
    def test_partial_then_final_preserves_history_and_replays_once(self):
        original_time = self.item.delivered_at
        first = create_post_production_correction(**self.command())
        replay = create_post_production_correction(**self.command())
        self.assertEqual(first.id, replay.id)
        self.item.refresh_from_db()
        self.assertEqual((self.item.quantity, self.item.remaining_quantity, self.item.state), (3, 2, "DELIVERED"))
        self.assertEqual(self.item.delivered_at, original_time)
        self.assertEqual(totals(self.tab)["exposure_cents"], 1600)
        self.assertEqual(LedgerAdjustment.objects.count(), 1)
        with self.assertRaises(CorrectionServiceError) as ctx:
            create_post_production_correction(**self.command(quantity=2))
        self.assertEqual(ctx.exception.code, "IDEMPOTENCY_CONFLICT")
        create_post_production_correction(**self.command(quantity=2, key="last-units"))
        self.item.refresh_from_db()
        self.assertEqual((self.item.remaining_quantity, self.item.state), (0, "CANCELLED"))
        self.assertEqual(totals(self.tab)["exposure_cents"], 0)
        self.assertFalse(Payment.objects.exists()); self.assertFalse(Refund.objects.exists()); self.assertFalse(WasteMarker.objects.exists())
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.cancelled").count(), 2)

    def test_invalid_quantities_reason_and_generic_delivered_cancel_have_no_effect(self):
        for quantity in [True, 1.5, 0, -1, 4, "1"]:
            with self.assertRaises(CorrectionServiceError):
                create_post_production_correction(**self.command(quantity=quantity))
        with self.assertRaises(CorrectionServiceError):
            create_post_production_correction(**self.command(reason_text=" "))
        with self.assertRaises(CorrectionServiceError):
            create_post_production_correction(**self.command(kind="CANCEL_ITEM", quantity=None))
        self.assertFalse(OrderCorrection.objects.exists()); self.assertFalse(LedgerAdjustment.objects.exists())

    def test_paid_and_non_manager_and_other_venue_are_blocked(self):
        self.membership.role = StaffRole.STAFF; self.membership.save()
        with self.assertRaises(CorrectionServiceError): create_post_production_correction(**self.command())
        self.membership.role = StaffRole.MANAGER; self.membership.save()
        other = Venue.objects.create(name="Outro teste", slug="wrong-entry-other")
        with self.assertRaises(CorrectionServiceError): create_post_production_correction(**self.command(actor=ActorContext(other.id, self.staff.id, None, None)))
        Payment.objects.create(tab=self.tab, amount_cents=500, method="CASH", status=PaymentStatus.CONFIRMED, idempotency_key="test-paid", received_by=self.staff, confirmed_at=timezone.now())
        with self.assertRaises(CorrectionServiceError) as ctx: create_post_production_correction(**self.command())
        self.assertEqual(ctx.exception.code, "PAID_CORRECTION_REQUIRES_REFUND")
        self.assertFalse(OrderCorrection.objects.exists()); self.assertFalse(LedgerAdjustment.objects.exists())

    def test_endpoint_requires_recent_pin_and_explicit_valid_quantity(self):
        path = f"/order-items/{self.item.id}/corrections/post-production/"
        body = self.command(); body.pop("actor"); body.pop("item_id")
        self.assertEqual(self.client.post(path, body, format="json").status_code, 403)
        self.assertEqual(self.client.post("/auth/reauthenticate/", {"pin": self.pin}, format="json").status_code, 200)
        self.assertEqual(self.client.post(path, {**body, "quantity": None}, format="json").status_code, 400)
        result = self.client.post(path, body, format="json")
        self.assertEqual(result.status_code, 201, result.json())
        self.assertEqual(result.json()["status"], "APPLIED")
        self.assertEqual(result.json()["financial_delta_cents"], -800)
        self.assertEqual(result.json()["remaining_quantity"], 2)

    def test_partial_keeps_delivery_task_and_last_unit_cancels_it_auditably(self):
        from modules.dispatch.models import DispatchTask
        self.item.state = "PICKED_UP"; self.item.save()
        task = DispatchTask.objects.create(venue=self.venue, order_item=self.item, task_type="DELIVERY", state="CLAIMED")
        create_post_production_correction(**self.command())
        task.refresh_from_db(); self.assertEqual(task.state, "CLAIMED")
        create_post_production_correction(**self.command(quantity=2, key="final-delivery-units"))
        task.refresh_from_db(); self.assertEqual(task.state, "CANCELLED")
        self.assertEqual(AuditEvent.objects.filter(event_type="dispatch.delivery_cancelled_for_correction").count(), 1)

    def test_transferred_charge_returns_conflict_and_rolls_back(self):
        from modules.tab_operations.models import TabOperation, TabTransfer, TabTransferLine
        operation = TabOperation.objects.create(source_tab=self.tab, idempotency_key="transfer-test", request_fingerprint="test", kind="MOVE_ITEMS", created_by=self.staff)
        transfer = TabTransfer.objects.create(operation=operation, venue=self.venue, source_tab=self.tab,
            destination_tab=Tab.objects.create(venue=self.venue), kind="MOVE_ITEMS", source_version=1, destination_version=1)
        TabTransferLine.objects.create(transfer=transfer, source_charge=Charge.objects.get(order_item=self.item), amount_cents=800)
        self.client.post("/auth/reauthenticate/", {"pin": self.pin}, format="json")
        body = self.command(); body.pop("actor"); body.pop("item_id")
        result = self.client.post(f"/order-items/{self.item.id}/corrections/post-production/", body, format="json")
        self.assertEqual(result.status_code, 409, result.json())
        self.assertEqual(result.json()["code"], "TRANSFERRED_RESPONSIBILITY")
        self.assertFalse(OrderCorrection.objects.exists()); self.assertFalse(LedgerAdjustment.objects.exists())


class WrongEntryConcurrencyTests(WrongEntryFixture, TransactionTestCase):
    def test_concurrent_requests_cannot_cancel_more_than_remaining(self):
        def run(index):
            close_old_connections()
            try:
                return str(create_post_production_correction(**self.command(quantity=2, key=f"race-{index}")).id)
            except CorrectionServiceError as error:
                return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(run, range(2)))
        self.item.refresh_from_db()
        self.assertEqual(self.item.remaining_quantity, 1)
        self.assertEqual(results.count("INVALID_CANCELLATION_QUANTITY"), 1)
        self.assertEqual(LedgerAdjustment.objects.count(), 1)
