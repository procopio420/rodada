from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class OrderIntentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name="Order recovery", slug="order-recovery")
        staff = StaffMember.objects.create(display_name="Operator", login_identifier="order-recovery")
        self.actor = ActorContext(venue.pk, staff.pk, None, None)
        self.tab = Tab.objects.create(venue=venue)
        self.product = Product.objects.create(venue=venue, name="Item", price_cents=1000, fulfillment_station="BAR")

    def race(self, quantities):
        barrier = Barrier(2)

        def worker(quantity):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    order = confirm_order(tab_id=self.tab.pk, source="STAFF", actor=self.actor,
                                          idempotency_key="same-order-intent",
                                          lines=[{"product_id": self.product.pk, "quantity": quantity}])
                    return str(order.pk)
                except OrderingServiceError as error:
                    return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, quantities))

    def assert_single_effect(self):
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Charge.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.filter(event_type="order.confirmed").count(), 1)
        from modules.house_account.services import financial_position

        self.assertEqual(financial_position(self.tab)["exposure_cents"], Charge.objects.get().amount_cents)

    def test_concurrent_same_intent_creates_one_order_charge_and_audit(self):
        results = self.race((2, 2))
        self.assertEqual(results[0], results[1])
        self.assert_single_effect()
        self.assertEqual(Charge.objects.get().amount_cents, 2000)

    def test_concurrent_changed_payload_does_not_replace_original(self):
        results = self.race((1, 2))
        self.assertIn("IDEMPOTENCY_CONFLICT", results)
        self.assert_single_effect()
        self.assertIn(Charge.objects.get().amount_cents, (1000, 2000))
