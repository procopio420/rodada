from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import CanonicalItem, Product
from catalog.services import generate_pending_icons
from pos.models import StaffMember, Venue
from pos.models import Order, OrderItem, Tab
from pos.services import confirm_order
from audit.models import AuditEvent


class CatalogTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Catalog venue")
        self.manager = StaffMember.objects.create(venue=self.venue, display_name="Manager", role=StaffMember.Role.MANAGER)
        self.client = APIClient(); self.client.credentials(HTTP_X_STAFF_ID=str(self.manager.id))

    def test_inline_canonical_creation_autocomplete_and_persistent_fallback_icon(self):
        created = self.client.post("/api/catalog/canonical-items/", {"name": "Pastel de queijo", "description": "Frito"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.get("/api/catalog/canonical-items/?q=queijo").json()[0]["name"], "Pastel de queijo")
        generate_pending_icons()
        item = CanonicalItem.objects.get(pk=created.json()["id"])
        self.assertEqual(item.icon_status, "READY")
        self.assertTrue(item.icon_key)
        again = self.client.post("/api/catalog/canonical-items/", {"name": "Pastel de queijo"}, format="json")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["icon_key"], item.icon_key)

    def test_unavailable_product_is_not_orderable(self):
        product = Product.objects.create(venue=self.venue, name="Fritas", current_price_cents=1200)
        response = self.client.post(f"/api/products/{product.id}/availability/", {"available": False}, format="json")
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db(); self.assertFalse(product.available)
        self.assertTrue(AuditEvent.objects.filter(action="product.availability_changed", entity_id=product.id).exists())
        tab = Tab.objects.create(venue=self.venue, opened_by=self.manager)
        order = Order.objects.create(tab=tab, created_by=self.manager)
        OrderItem.objects.create(order=order, product=product, quantity=1)
        with self.assertRaises(Exception):
            confirm_order(order.id, self.manager)
