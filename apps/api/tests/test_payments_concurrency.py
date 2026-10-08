from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.catalog.models import FulfillmentStation, Product
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
