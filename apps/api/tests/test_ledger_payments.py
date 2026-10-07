from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import FulfillmentStation, Product
from modules.ledger.models import Charge, Payment
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
        order = self.client.post(f"/tabs/{tab['id']}/orders/confirm/", {"lines": [{"product_id": str(self.product.id), "quantity": 2}]}, format="json")
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
        partial = self.client.post(f"/tabs/{tab['id']}/payments/", {"amount_cents": 1000, "method": "CASH", "idempotency_key": "p1"}, format="json")
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
