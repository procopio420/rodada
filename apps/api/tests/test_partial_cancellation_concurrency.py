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
    review_fixture = fixtures.CorrectionFoundationTests.review_fixture

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

    def test_concurrent_review_applies_one_reversal_and_one_approval(self):
        from modules.audit.models import AuditEvent
        from modules.corrections.services import settle_cancellation_without_refund
        item, _, pending = self.review_fixture()
        results = self.race(lambda index: settle_cancellation_without_refund(
            correction_id=pending.id, actor=self.actor)[0])
        self.assertEqual(results[0], results[1])
        self.assertEqual(LedgerAdjustment.objects.filter(order_item=item).count(), 1)
        self.assertEqual(totals(item.order.tab)["exposure_cents"], 2000)
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.cancelled_without_refund").count(), 1)

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

    def test_paid_correction_concurrent_replay_preserves_one_refund_and_reversal(self):
        from modules.audit.models import AuditEvent
        from modules.corrections.services import settle_refund_required_cancellation
        from modules.ledger.models import Payment, Refund

        item, payment, pending = self.review_fixture(payment_cents=3500)
        original = Payment.objects.values().get(pk=payment.pk)
        results = self.race(lambda index: settle_refund_required_cancellation(
            correction_id=pending.pk, payment_id=payment.pk, amount_cents=500,
            refund_idempotency_key="correction-race-refund", cash_point_id=None, actor=self.actor)[0])
        self.assertEqual(results[0], results[1])
        self.assertEqual(Refund.objects.count(), 1)
        self.assertEqual(LedgerAdjustment.objects.filter(order_item=item).count(), 1)
        self.assertEqual(totals(item.order.tab)["exposure_cents"], 0)
        self.assertEqual(AuditEvent.objects.filter(event_type="payment.refunded").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="order_item.cancelled_after_refund").count(), 1)
        current = Payment.objects.values().get(pk=payment.pk)
        self.assertEqual(current.pop("status"), "PARTIALLY_REFUNDED")
        original.pop("status")
        self.assertEqual(current, original)
