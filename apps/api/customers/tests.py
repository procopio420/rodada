from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditEvent
from catalog.models import Product
from customers.models import Customer, Relationship, VenueRelationshipPolicy
from customers.services import override_limit
from ledger.models import Payment
from pos.models import Order, OrderItem, StaffMember, Tab, Venue
from pos.services import confirm_order, record_payment


class HouseAccountTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="House bar")
        self.manager = StaffMember.objects.create(venue=self.venue, display_name="Manager", role=StaffMember.Role.MANAGER)
        self.staff = StaffMember.objects.create(venue=self.venue, display_name="Staff")
        self.customer = Customer.objects.create(display_name="Joao da Oficina", phone="11999990000")
        self.relationship = Relationship.objects.create(venue=self.venue, customer=self.customer, status=Relationship.Status.HOUSE, nickname="Joao")
        VenueRelationshipPolicy.objects.create(venue=self.venue, status=Relationship.Status.HOUSE, operating_limit_cents=5000)
        self.client = APIClient(); self.client.credentials(HTTP_X_STAFF_ID=str(self.staff.id))

    def test_tab_snapshots_relationship_policy_and_search_finds_nickname(self):
        response = self.client.post("/api/tabs/", {"venue_id": self.venue.id, "customer_id": self.customer.id}, format="json")
        self.assertEqual(response.json()["operating_limit_cents"], 5000)
        self.relationship.status = Relationship.Status.RESTRICTED; self.relationship.save()
        self.assertEqual(Tab.objects.get(pk=response.json()["id"]).operating_limit_cents, 5000)
        found = self.client.get(f"/api/customers/?venue_id={self.venue.id}&q=joao")
        self.assertEqual(found.json()[0]["id"], self.customer.id)

    def test_limit_partial_payment_and_audited_override(self):
        product = Product.objects.create(venue=self.venue, name="Combo", current_price_cents=5000)
        tab = Tab.objects.create(venue=self.venue, customer=self.customer, operating_limit_cents=5000, opened_by=self.staff)
        order = Order.objects.create(tab=tab, created_by=self.staff); OrderItem.objects.create(order=order, product=product, quantity=1)
        confirm_order(order.id, self.staff); tab.refresh_from_db()
        self.assertEqual(tab.status, Tab.Status.REQUIRES_ACTION)
        record_payment(tab.id, self.staff, amount_cents=1000, method=Payment.Method.CASH); tab.refresh_from_db()
        self.assertEqual(tab.status, Tab.Status.OPEN)
        override_limit(tab.id, self.manager, 9000, "Noite especial"); tab.refresh_from_db()
        self.assertEqual(tab.operating_limit_cents, 9000)
        event = AuditEvent.objects.get(action="tab.limit_overridden")
        self.assertEqual(event.before["operating_limit_cents"], 5000)
        self.assertEqual(event.after["operating_limit_cents"], 9000)

    def test_regular_staff_cannot_override(self):
        tab = Tab.objects.create(venue=self.venue, operating_limit_cents=3000)
        with self.assertRaises(Exception): override_limit(tab.id, self.staff, 9000)
