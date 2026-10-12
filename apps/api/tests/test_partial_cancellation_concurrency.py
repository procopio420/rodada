from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from modules.corrections.models import OrderCorrection
from modules.corrections.services import CorrectionServiceError
from modules.ledger.models import Charge, LedgerAdjustment
from modules.ledger.services import totals
from tests import test_corrections as fixtures


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class PartialCancellationConcurrencyTests(TransactionTestCase):
    setUp = fixtures.CorrectionFoundationTests.setUp
    item = fixtures.CorrectionFoundationTests.item
    partial_cancel = fixtures.CorrectionFoundationTests.partial_cancel

    def race(self, operation):
        barrier = Barrier(2)

        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    result = operation(index)
                    return str(result.id)
                except CorrectionServiceError as error:
                    return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(worker, range(2)))

    def test_concurrent_same_key_replays_one_partial_cancellation(self):
        item = self.item(quantity=3)
        Charge.objects.create(tab=item.order.tab, order_item=item, amount_cents=3600)
        results = self.race(lambda index: self.partial_cancel(item, 2, "same-key"))
        self.assertEqual(results[0], results[1])
        self.assertEqual(OrderCorrection.objects.filter(original_order_item=item).count(), 1)
        self.assertEqual(LedgerAdjustment.objects.filter(order_item=item).count(), 1)
        self.assertEqual(item.remaining_quantity, 1)
        self.assertEqual(totals(item.order.tab)["exposure_cents"], 1200)

    def test_concurrent_distinct_keys_cannot_cancel_more_than_remaining(self):
        item = self.item(quantity=3)
        Charge.objects.create(tab=item.order.tab, order_item=item, amount_cents=3600)
        results = self.race(lambda index: self.partial_cancel(item, 2, f"distinct-{index}"))
        self.assertEqual(results.count("INVALID_CANCELLATION_QUANTITY"), 1)
        self.assertEqual(OrderCorrection.objects.filter(original_order_item=item).count(), 1)
        self.assertEqual(LedgerAdjustment.objects.filter(order_item=item).count(), 1)
        self.assertEqual(item.remaining_quantity, 1)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(totals(item.order.tab)["exposure_cents"], 1200)
