from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone

from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.catalog.models import FulfillmentStation, Product
from modules.cash.models import CashMovement, CashMovementKind, CashPoint
from modules.cash.services import cash_shift_position, open_cash_shift
from modules.ledger.services import collect_payment
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, OrderItem, Tab
from modules.payment_provider.fake import DeterministicFakePaymentProvider
from modules.payment_provider.refunds import reserve_refund
from modules.payment_provider.services import (
    ProviderServiceError,
    initiate_provider_payment,
    reconcile_provider_payment,
)
from modules.venue.models import Venue


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class PaymentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name="Race", slug="race")
        staff = StaffMember.objects.create(display_name="Cashier", login_identifier="race")
        self.actor = ActorContext(venue.pk, staff.pk, None, None)
        self.tab = Tab.objects.create(venue=venue)
        product = Product.objects.create(
            venue=venue, name="Beer", price_cents=3000, fulfillment_station=FulfillmentStation.BAR
        )
        order = Order.objects.create(tab=self.tab)
        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot="Beer",
            unit_price_cents=3000,
            quantity=1,
        )
        Charge.objects.create(tab=self.tab, order_item=item, amount_cents=3000)
        self.provider = DeterministicFakePaymentProvider(venue_id=venue.pk)

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

    def test_two_tabs_with_same_client_key_concurrently_record_distinct_cash(self):
        # PostgreSQL connections race on separate Tabs, but share a single drawer.
        second = Tab.objects.create(venue=self.tab.venue)
        product = Product.objects.get(venue=self.tab.venue)
        order = Order.objects.create(tab=second)
        item = OrderItem.objects.create(
            order=order, product=product, product_name_snapshot="Beer",
            unit_price_cents=3000, quantity=1,
        )
        Charge.objects.create(tab=second, order_item=item, amount_cents=3000)
        point = CashPoint.objects.create(venue=self.tab.venue, label="Race cash drawer")
        shift = open_cash_shift(
            cash_point_id=point.id, opening_float_cents=1000,
            business_date=timezone.localdate(), idempotency_key="open-race",
            actor=self.actor,
        )
        tab_ids = (self.tab.id, second.id)

        def operation(i):
            payment, _ = collect_payment(
                tab_id=tab_ids[i], amount_cents=3000, method="CASH",
                idempotency_key="same-client-payment-key",
                cash_point_id=point.id, actor=self.actor,
            )
            return payment.id

        payment_ids = self.race(operation)
        self.assertEqual(len(set(payment_ids)), 2)
        movements = list(CashMovement.objects.filter(
            shift=shift, kind=CashMovementKind.CASH_PAYMENT
        ))
        self.assertEqual(len(movements), 2)
        self.assertEqual({m.payment_id for m in movements}, set(payment_ids))
        self.assertEqual(len({m.idempotency_key for m in movements}), 2)
        self.assertEqual(cash_shift_position(shift)["expected_cents"], 7000)

    def test_two_waiters_cannot_start_two_collections_against_one_balance(self):
        def operation(i):
            try:
                initiate_provider_payment(
                    tab_id=self.tab.pk,
                    amount_cents=3000,
                    method="PIX",
                    idempotency_key=f"waiter-{i}",
                    provider=self.provider,
                    actor=self.actor,
                )
                return "started"
            except ProviderServiceError as error:
                return error.code

        self.assertCountEqual(self.race(operation), ["started", "PAYMENT_ALREADY_PENDING"])
        self.assertEqual(Payment.objects.count(), 1)

    def test_cash_same_intent_has_one_payment_drawer_effect_and_audit(self):
        from django.utils import timezone

        from modules.audit.models import AuditEvent
        from modules.cash.models import CashMovement, CashPoint, CashShift
        from modules.ledger.services import collect_payment

        point = CashPoint.objects.create(venue_id=self.actor.venue_id, label="Race drawer")
        shift = CashShift.objects.create(
            venue_id=self.actor.venue_id, cash_point=point, business_date=timezone.localdate(),
            opened_by_id=self.actor.staff_id, opening_float_cents=0, opening_idempotency_key="open-race",
        )
        def collect(_):
            return collect_payment(tab_id=self.tab.pk, amount_cents=1000, method="CASH",
                                   cash_point_id=point.pk, idempotency_key="same-cash",
                                   expected_version=1, actor=self.actor)[0].pk

        ids = self.race(collect)
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(CashMovement.objects.filter(shift=shift).count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="payment.collected").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="cash.payment_recorded").count(), 1)
        self.tab.refresh_from_db()
        self.assertEqual(self.tab.version, 2)

    def test_duplicate_intent_concurrent_confirmation_and_refund_reservation(self):
        def start(i):
            return initiate_provider_payment(
                tab_id=self.tab.pk,
                amount_cents=3000,
                method="PIX",
                idempotency_key="same",
                provider=self.provider,
                actor=self.actor,
            )[0].pk

        ids = self.race(start)
        self.assertEqual(ids[0], ids[1])
        for _ in range(2):
            reconcile_provider_payment(payment_id=ids[0], provider=self.provider, actor=self.actor)

        def refund(i):
            try:
                reserve_refund(
                    payment_id=ids[0],
                    amount_cents=2000,
                    key=f"r-{i}",
                    reason="wrong",
                    actor=self.actor,
                )
                return "reserved"
            except ProviderServiceError as error:
                return error.code

        self.assertCountEqual(self.race(refund), ["reserved", "REFUND_EXCEEDS_PAYMENT"])

    def test_duplicate_webhooks_are_applied_once_under_postgres_inbox_lock(self):
        from modules.payment_provider.adapters import DeterministicPaymentProvider
        from modules.payment_provider.models import ProviderEvent
        from modules.payment_provider.services import ingest_provider_webhook

        provider = DeterministicPaymentProvider()
        payment, _, _ = initiate_provider_payment(
            tab_id=self.tab.pk,
            amount_cents=3000,
            method="PIX",
            idempotency_key="hook",
            provider=provider,
            actor=self.actor,
        )
        payload = {
            "provider_event_id": "one-event",
            "event_type": "payment.confirmed",
            "merchant_reference": str(payment.pk),
            "status": "CONFIRMED",
            "provider_payment_id": "tx-unique",
        }

        def hook(i):
            return ingest_provider_webhook(
                provider=provider, payload=payload, signature="test-valid-signature"
            )[1]

        self.assertCountEqual(self.race(hook), [False, True])
        self.assertEqual(ProviderEvent.objects.count(), 1)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "CONFIRMED")

    def test_one_transaction_cannot_settle_distinct_tabs_concurrently(self):
        from modules.payment_provider.adapters import ProviderResult
        from modules.payment_provider.models import PaymentAttempt
        from modules.payment_provider.services import apply_provider_result
        from modules.payment_provider.sumup import settlement_key

        payments = []
        for index in range(2):
            tab = Tab.objects.create(venue=self.tab.venue)
            payment = Payment.objects.create(
                tab=tab,
                amount_cents=1000,
                method="PIX",
                provider=f"sumup:{self.tab.venue_id}:merchant",
                status="PENDING",
                received_by_id=self.actor.staff_id,
                idempotency_key=f"checkout-{index}",
                provider_payment_id=f"checkout-{index}",
            )
            attempt = PaymentAttempt.objects.create(
                payment=payment, provider=payment.provider, idempotency_key=payment.idempotency_key
            )
            payments.append((payment.pk, attempt.pk))

        def settle(index):
            payment_id, attempt_id = payments[index]
            return apply_provider_result(
                payment_id=payment_id,
                attempt_id=attempt_id,
                result=ProviderResult(
                    status="CONFIRMED",
                    metadata={"settlement_key": settlement_key("merchant", "one-transaction")},
                ),
                actor=self.actor,
            )[0].status

        self.assertCountEqual(self.race(settle), ["CONFIRMED", "CONFIRMATION_PENDING"])
        self.assertEqual(Payment.objects.filter(status="CONFIRMED").count(), 1)

    def manual_refund_race(self, same_key):
        from django.utils import timezone

        from modules.audit.models import AuditEvent
        from modules.cash.models import CashMovement, CashPoint, CashShift
        from modules.ledger.models import Refund
        from modules.ledger.services import (
            LedgerServiceError,
            collect_payment,
            create_refund,
            totals,
        )

        point = CashPoint.objects.create(venue_id=self.actor.venue_id, label="Refund race drawer")
        shift = CashShift.objects.create(venue_id=self.actor.venue_id, cash_point=point,
            business_date=timezone.localdate(), opened_by_id=self.actor.staff_id,
            opening_float_cents=0, opening_idempotency_key="refund-race-open")
        payment, _ = collect_payment(tab_id=self.tab.pk, amount_cents=1000, method="CASH",
            cash_point_id=point.pk, idempotency_key="refund-race-payment", actor=self.actor)
        original = Payment.objects.values().get(pk=payment.pk)
        def operation(i):
            try:
                refund, _ = create_refund(payment_id=payment.pk, amount_cents=700,
                    idempotency_key="refund-race" if same_key else f"refund-race-{i}",
                    reason="Race test", cash_point_id=point.pk, actor=self.actor)
                return str(refund.pk)
            except LedgerServiceError as error:
                return error.code
        outcomes = self.race(operation)
        if same_key:
            self.assertEqual(outcomes[0], outcomes[1])
        else:
            self.assertEqual(outcomes.count("REFUND_EXCEEDS_PAYMENT"), 1)
        self.assertEqual(Refund.objects.count(), 1)
        self.assertEqual(CashMovement.objects.filter(shift=shift, refund__isnull=False).count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="payment.refunded").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(event_type="cash.refund_recorded").count(), 1)
        self.assertEqual(totals(self.tab)["exposure_cents"], 2700)
        current = Payment.objects.values().get(pk=payment.pk)
        self.assertEqual(current.pop("status"), "PARTIALLY_REFUNDED")
        original.pop("status")
        self.assertEqual(current, original)

    def test_same_manual_refund_is_exactly_once_under_postgres_lock(self):
        self.manual_refund_race(same_key=True)

    def test_distinct_manual_refunds_cannot_exceed_refundable_concurrently(self):
        self.manual_refund_race(same_key=False)
