from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import DatabaseError, close_old_connections, connection, transaction
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.ledger.models import AdjustmentAllocation, LedgerAdjustment
from modules.ledger.pricing import PricingError, apply
from modules.ledger.services import LedgerServiceError, collect_payment, totals
from tests.test_pricing import PricingFixture


@skipUnless(
    connection.vendor == "postgresql", "Requires PostgreSQL row locks and deferred triggers"
)
class PricingConcurrencyTests(PricingFixture, TransactionTestCase):
    def race(self, operation):
        barrier = Barrier(2)

        def worker(i):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return operation(i)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, (0, 1)))

    def actor(self):
        return ActorContext.from_session(
            StaffSession.objects.get(staff_member__login_identifier="manager")
        )

    def test_two_distinct_adjustments_one_version(self):
        data, actor = self.command(value=1000), self.actor()

        def operation(i):
            try:
                apply(
                    tab_id=self.tab.id, data={**data, "idempotency_key": f"race-{i}"}, actor=actor
                )
                return "applied"
            except PricingError as error:
                return error.code

        self.assertCountEqual(self.race(operation), ["applied", "VERSION_CONFLICT"])
        self.assertEqual(LedgerAdjustment.objects.count(), 1)
        self.assertEqual(totals(self.tab)["exposure_cents"], 1000)

    def test_duplicate_request_one_fact_and_response(self):
        data, actor = self.command(value=1000), self.actor()
        results = self.race(lambda _: apply(tab_id=self.tab.id, data=data, actor=actor))
        self.assertEqual(results[0], results[1])
        self.assertEqual(LedgerAdjustment.objects.count(), 1)
        self.assertEqual(AdjustmentAllocation.objects.count(), 1)

    def test_discount_racing_payment_never_overcollects(self):
        data, actor = self.command(value=1000), self.actor()

        def operation(i):
            try:
                if i == 0:
                    apply(tab_id=self.tab.id, data=data, actor=actor)
                else:
                    collect_payment(
                        tab_id=self.tab.id,
                        amount_cents=1500,
                        method="OTHER",
                        idempotency_key="race-payment",
                        actor=actor,
                    )
                return "committed"
            except (PricingError, LedgerServiceError) as error:
                return error.code

        results = self.race(operation)
        self.assertEqual(results.count("committed"), 1)
        self.assertTrue(
            set(results)
            <= {
                "committed",
                "SETTLEMENT_CORRECTION_REQUIRED",
                "PAYMENT_EXCEEDS_EXPOSURE",
                "VERSION_CONFLICT",
            }
        )
        bill = totals(self.tab)
        self.assertGreaterEqual(bill["exposure_cents"], 0)
        self.assertGreaterEqual(bill["payable_cents"], bill["payments_cents"])

    def test_concurrent_service_assessment_exactly_once(self):
        data, actor = self.command("SERVICE_CHARGE", 1000), self.actor()
        results = self.race(lambda _: apply(tab_id=self.tab.id, data=data, actor=actor))
        self.assertEqual(results[0], results[1])
        self.assertEqual(totals(self.tab)["service_charge_cents"], 200)

    def test_postgres_append_only_and_allocation_sum(self):
        result = apply(tab_id=self.tab.id, data=self.command(value=500), actor=self.actor())
        with self.assertRaises(DatabaseError), transaction.atomic():
            LedgerAdjustment.objects.filter(pk=result["adjustment_id"]).update(amount_cents=-1)
        with self.assertRaises(DatabaseError), transaction.atomic():
            AdjustmentAllocation.objects.all().delete()
        with self.assertRaises(DatabaseError), transaction.atomic():
            LedgerAdjustment.objects.create(
                tab=self.tab,
                kind="TAB_DISCOUNT",
                scope="TAB",
                amount_cents=-100,
                created_by_id=self.actor().staff_id,
                idempotency_key="invalid-allocation",
                request_fingerprint="test",
            )
