from django.test import TestCase

from catalog.models import Product
from ledger.models import PaymentIntent
from ledger.services import confirm_test_intent, create_intent
from pos.models import Order, OrderItem, StaffMember, Tab, Venue
from pos.services import confirm_order, exposure_cents


class PaymentIntentTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Payments venue")
        self.staff = StaffMember.objects.create(venue=self.venue, display_name="Waiter")
        product = Product.objects.create(venue=self.venue, name="Card item", current_price_cents=2000)
        self.tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        order = Order.objects.create(tab=self.tab, created_by=self.staff)
        OrderItem.objects.create(order=order, product=product, quantity=1)
        confirm_order(order.id, self.staff)

    def test_test_provider_confirmation_updates_the_correct_tab_once(self):
        intent = create_intent(self.tab, 1000, "CARD", "tap-1", self.staff)
        self.assertEqual(intent.provider, "TEST")
        confirm_test_intent(intent, self.staff)
        intent.refresh_from_db()
        self.assertEqual(intent.status, PaymentIntent.Status.SUCCEEDED)
        self.assertEqual(exposure_cents(self.tab), 1000)
        self.assertEqual(confirm_test_intent(intent, self.staff).payment_id, intent.payment_id)
