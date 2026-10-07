from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import Product
from pos.models import PhysicalTable, StaffMember, TableAccessToken, Venue, Zone


class CustomerQrTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="QR venue")
        self.zone = Zone.objects.create(venue=self.venue, name="Rua")
        self.table = PhysicalTable.objects.create(venue=self.venue, zone=self.zone, label="Mesa QR")
        self.access = TableAccessToken.objects.create(table=self.table)
        self.product = Product.objects.create(venue=self.venue, name="Brahma", current_price_cents=1000, fulfillment_station="BAR")
        self.client = APIClient()

    def test_opaque_qr_creates_tab_and_customer_order_without_table_identity_leak(self):
        entry = self.client.get(f"/api/public/qr/{self.access.token}/")
        self.assertEqual(entry.status_code, 200)
        self.assertNotIn(str(self.table.id), self.access.token)
        session = self.client.post(f"/api/public/qr/{self.access.token}/sessions/", {"guest_name": "Lia"}, format="json")
        self.assertEqual(session.status_code, 201)
        session_token = session.json()["session_token"]
        ordered = self.client.post(f"/api/public/sessions/{session_token}/orders/", {"items": [{"product_id": self.product.id, "quantity": 2}], "idempotency_key": "customer-1"}, format="json")
        self.assertEqual(ordered.status_code, 201)
        self.assertEqual(ordered.json()["tab"]["exposure_cents"], 2000)
        self.table.refresh_from_db(); self.assertEqual(self.table.status, PhysicalTable.Status.OCCUPIED)

    def test_qr_cannot_order_unavailable_product(self):
        self.product.available = False; self.product.save()
        session = self.client.post(f"/api/public/qr/{self.access.token}/sessions/", {}, format="json").json()
        response = self.client.post(f"/api/public/sessions/{session['session_token']}/orders/", {"items": [{"product_id": self.product.id, "quantity": 1}]}, format="json")
        self.assertEqual(response.status_code, 404)
