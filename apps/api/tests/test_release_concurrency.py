"""Release integration races use the real services and PostgreSQL row locks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.catalog.models import Product
from modules.ledger.models import Charge, Payment
from modules.ledger.services import LedgerServiceError, collect_payment, totals
from modules.ordering.models import Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class ReleaseConcurrencyTests(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name="Release race", slug="release-race")
        staff = StaffMember.objects.create(display_name="QA", login_identifier="release-race")
        self.actor = ActorContext(venue.pk, staff.pk, None, None)
        self.tab = Tab.objects.create(venue=venue, operating_limit_cents=1000)
        self.product = Product.objects.create(
            venue=venue, name="Beer", price_cents=1000, fulfillment_station="BAR"
        )
        self.order("initial")

    def order(self, key):
        return confirm_order(
            tab_id=self.tab.pk,
            source="STAFF",
            actor=self.actor,
            lines=[{"product_id": self.product.pk, "quantity": 1}],
            idempotency_key=key,
        )

    def pay(self, key):
        return collect_payment(
            tab_id=self.tab.pk,
            amount_cents=1000,
            method="EXTERNAL_TERMINAL",
            idempotency_key=key,
            actor=self.actor,
        )

    def race(self, operations):
        barrier = Barrier(len(operations))

        def worker(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    operation()
                    return "committed"
                except (LedgerServiceError, OrderingServiceError) as error:
                    return error.code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(worker, operations))

    def test_distinct_manual_payments_cannot_overcollect_same_balance(self):
        results = self.race([lambda: self.pay("a"), lambda: self.pay("b")])
        self.assertCountEqual(results, ["committed", "PAYMENT_EXCEEDS_EXPOSURE"])
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(totals(self.tab)["exposure_cents"], 0)

    def test_order_and_partial_shift_payment_preserve_limit_and_ledger(self):
        results = self.race([lambda: self.order("next"), lambda: self.pay("pay")])
        self.assertEqual(results[1], "committed")
        self.assertIn(results[0], ["committed", "SPENDING_LIMIT_EXCEEDED"])
        expected = 1000 if results[0] == "committed" else 0
        self.assertEqual(totals(self.tab)["exposure_cents"], expected)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Charge.objects.count(), 2 if expected else 1)
