import uuid

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.corrections.models import OrderCorrection
from modules.ledger.models import Charge, LedgerAdjustment, Payment, Refund
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


class RecoveryContextTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Recovery test", slug="recovery-test")
        self.other = Venue.objects.create(name="Other recovery test", slug="other-recovery-test")
        self.clients = {}
        for role in (StaffRole.STAFF, StaffRole.MANAGER):
            staff = StaffMember.objects.create(display_name=role, login_identifier=f"recovery-{role}")
            staff.set_pin("2468"); staff.save(update_fields=["pin_hash"])
            VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=role)
            client = APIClient()
            response = client.post("/auth/login/", {"venue_slug": self.venue.slug, "login_identifier": staff.login_identifier, "pin": "2468", "installation_id": f"recovery-device-{role}", "platform": "WEB"}, format="json")
            self.assertEqual(response.status_code, 200)
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
            self.clients[role] = client
            if role == StaffRole.MANAGER: self.manager = staff
        self.tab, self.item, self.payment, self.correction = self.fixture(self.venue)
        self.foreign_tab, self.foreign_item, self.foreign_payment, self.foreign_correction = self.fixture(self.other)

    def fixture(self, venue):
        tab = Tab.objects.create(venue=venue, state="CLOSED")
        order = Order.objects.create(tab=tab, source="STAFF")
        product, _ = Product.objects.get_or_create(venue=venue, name="Recovery fixture item", defaults={"price_cents": 100, "fulfillment_station": "BAR"})
        item = OrderItem.objects.create(order=order, product=product, product_name_snapshot=product.name, unit_price_cents=100, quantity=1, state="CANCELLED")
        payment = Payment.objects.create(tab=tab, amount_cents=100, method="CASH", idempotency_key=str(uuid.uuid4()), received_by=self.manager, confirmed_at=timezone.now())
        correction = OrderCorrection.objects.create(venue=venue, original_order_item=item, kind="CANCEL_ITEM", stage_at_request="NEW", status="APPLIED", reason_code="WRONG_ENTRY", requested_by=self.manager, idempotency_key=str(uuid.uuid4()), request_fingerprint="test-fixture")
        return tab, item, payment, correction

    def snapshot(self):
        return {model.__name__: list(model.objects.order_by("pk").values()) for model in (Tab, Order, OrderItem, OrderCorrection, Payment, Refund, Charge, LedgerAdjustment, AuditEvent)}

    def test_closed_tab_cancelled_item_and_applied_correction_resolve_without_mutation(self):
        client = self.clients[StaffRole.MANAGER]
        before = self.snapshot()
        expected = str(self.tab.id)
        for _ in range(2):
            item = client.get(f"/order-items/{self.item.id}/recovery-context/")
            payment = client.get(f"/payments/{self.payment.id}/recovery-context/")
            correction = client.get(f"/corrections/{self.correction.id}/recovery-context/", {"payment_id": self.payment.id})
            for response in (item, payment, correction):
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["tab_id"], expected)
            self.assertEqual(item.json()["order_item_id"], str(self.item.id))
            self.assertEqual(payment.json()["payment_id"], str(self.payment.id))
            self.assertEqual(correction.json()["correction_id"], str(self.correction.id))
            self.assertEqual(correction.json()["payment_id"], str(self.payment.id))
            self.assertEqual(correction.json()["correction_status"], "APPLIED")
        self.assertEqual(before, self.snapshot())

    def test_foreign_and_missing_ids_have_same_not_found_response(self):
        client = self.clients[StaffRole.MANAGER]
        for resource, foreign in (("order-items", self.foreign_item.id), ("payments", self.foreign_payment.id), ("corrections", self.foreign_correction.id)):
            params = {"payment_id": self.payment.id} if resource == "corrections" else {}
            foreign_response = client.get(f"/{resource}/{foreign}/recovery-context/", params)
            missing_response = client.get(f"/{resource}/{uuid.uuid4()}/recovery-context/", params)
            self.assertEqual(foreign_response.status_code, 404)
            self.assertEqual(foreign_response.json(), missing_response.json())

    def test_settlement_payment_must_belong_to_same_tab_and_venue(self):
        _, _, another_payment, _ = self.fixture(self.venue)
        for payment in (another_payment, self.foreign_payment):
            response = self.clients[StaffRole.MANAGER].get(f"/corrections/{self.correction.id}/recovery-context/", {"payment_id": payment.id})
            self.assertEqual(response.status_code, 404)

    def test_settlement_requires_valid_payment_query(self):
        for params in ({}, {"payment_id": "invalid"}):
            self.assertEqual(self.clients[StaffRole.MANAGER].get(f"/corrections/{self.correction.id}/recovery-context/", params).status_code, 400)

    def test_read_capabilities_do_not_grant_refund_access_to_staff(self):
        staff = self.clients[StaffRole.STAFF]
        self.assertEqual(staff.get(f"/order-items/{self.item.id}/recovery-context/").status_code, 200)
        for path in (f"/payments/{self.payment.id}/recovery-context/", f"/corrections/{self.correction.id}/recovery-context/?payment_id={self.payment.id}"):
            self.assertEqual(staff.get(path).status_code, 403)

    def test_authentication_and_read_only_contract(self):
        path = f"/payments/{self.payment.id}/recovery-context/"
        self.assertEqual(APIClient().get(path).status_code, 401)
        self.assertEqual(self.clients[StaffRole.MANAGER].post(path, {}, format="json").status_code, 405)
