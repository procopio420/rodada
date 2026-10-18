from django.test import TestCase

from modules.access.context import ActorContext
from modules.access.models import StaffMember
from modules.catalog.models import FulfillmentStation, Product
from modules.ledger.models import Charge, PaymentStatus
from modules.ledger.services import totals
from modules.ordering.models import Order, OrderItem, OrderSource, Tab
from modules.payment_provider.adapters import DeterministicPaymentProvider, ProviderResult
from modules.payment_provider.models import (
    PaymentAttempt,
    PaymentAttemptStatus,
    ProviderEvent,
    ProviderEventProcessingStatus,
)
from modules.payment_provider.services import (
    ProviderServiceError,
    ingest_provider_webhook,
    initiate_provider_payment,
    reconcile_provider_payment,
)
from modules.venue.models import Venue


class PaymentProviderServiceTests(TestCase):
    def test_unconfirmed_payment_blocks_zero_balance_close_without_provider_calls(self):
        from modules.ledger.models import Payment
        from modules.ledger.services import close_tab, LedgerServiceError
        for status in ("CREATED", "PENDING", "PROCESSING", "AUTHORIZED", "CONFIRMATION_PENDING"):
            with self.subTest(status=status):
                tab = Tab.objects.create(venue=self.venue, display_label=status)
                payment = Payment.objects.create(tab=tab, amount_cents=100,
                    method="OTHER", status=status, idempotency_key=status, received_by=self.staff)
                with self.assertRaises(LedgerServiceError) as denied:
                    close_tab(tab_id=tab.pk, actor=self.actor)
                self.assertEqual(denied.exception.code, "PAYMENT_ALREADY_PENDING")
                tab.refresh_from_db()
                payment.refresh_from_db()
                self.assertEqual(tab.state, "OPEN")
                self.assertIsNone(payment.confirmed_at)
                self.assertEqual(totals(tab)["payments_cents"], 0)
                payment.status = "CANCELLED"
                payment.save(update_fields=["status"])
                self.assertEqual(close_tab(tab_id=tab.pk, actor=self.actor).state, "CLOSED")

    def setUp(self):
        self.venue = Venue.objects.create(name="Provider Bar", slug="provider-bar")
        self.staff = StaffMember.objects.create(
            display_name="Caixa Provider", login_identifier="provider-cashier"
        )
        self.actor = ActorContext(
            venue_id=self.venue.id,
            staff_id=self.staff.id,
            session_id=None,
            device_id=None,
        )
        self.tab = Tab.objects.create(venue=self.venue, display_label="Provider tab")
        product = Product.objects.create(
            venue=self.venue,
            name="Produto provider",
            price_cents=3000,
            fulfillment_station=FulfillmentStation.BAR,
        )
        order = Order.objects.create(tab=self.tab, source=OrderSource.STAFF)
        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            unit_price_cents=3000,
            quantity=1,
        )
        Charge.objects.create(tab=self.tab, order_item=item, amount_cents=3000)

    def initiate(self, provider, *, key="provider-key", amount=3000):
        return initiate_provider_payment(
            tab_id=self.tab.id,
            amount_cents=amount,
            method="TAP_TO_PAY",
            idempotency_key=key,
            provider=provider,
            actor=self.actor,
        )

    def webhook_payload(self, payment, *, event_id, status, provider_payment_id="provider-payment-1"):
        return {
            "provider_event_id": event_id,
            "event_type": f"payment.{status.lower()}",
            "status": status,
            "merchant_reference": str(payment.id),
            "provider_payment_id": provider_payment_id,
            "provider_attempt_id": "provider-attempt-1",
            "metadata": {"provider_state": status},
        }

    def test_initiation_is_idempotent_and_pending_money_does_not_reduce_exposure(self):
        provider = DeterministicPaymentProvider(
            start_result=ProviderResult(
                status=PaymentStatus.PENDING,
                provider_payment_id="provider-payment-1",
            )
        )
        first_payment, first_attempt, replayed = self.initiate(provider)
        replay_payment, replay_attempt, replayed_again = self.initiate(provider)

        assert not replayed
        assert replayed_again
        assert first_payment.id == replay_payment.id
        assert first_attempt.id == replay_attempt.id
        assert len(provider.start_calls) == 1
        assert PaymentAttempt.objects.count() == 1
        assert first_payment.status == PaymentStatus.PENDING
        assert totals(self.tab)["payments_cents"] == 0
        assert totals(self.tab)["exposure_cents"] == 3000

    def test_ambiguous_start_stays_confirmation_pending_and_reconciliation_confirms_once(self):
        class TimeoutProvider(DeterministicPaymentProvider):
            def start_payment(self, input):
                self.start_calls.append(input)
                raise TimeoutError("provider timed out after accepting request")

        provider = TimeoutProvider(
            lookup_results={
                # Filled with the canonical merchant reference after initiation.
            }
        )
        payment, attempt, _ = self.initiate(provider)
        payment.refresh_from_db()
        attempt.refresh_from_db()
        assert payment.status == PaymentStatus.CONFIRMATION_PENDING
        assert attempt.status == PaymentAttemptStatus.CONFIRMATION_PENDING
        assert totals(self.tab)["payments_cents"] == 0

        replay_payment, _replay_attempt, replayed = self.initiate(provider)
        assert replayed
        assert replay_payment.id == payment.id
        assert len(provider.start_calls) == 1

        provider.lookup_results[str(payment.id)] = ProviderResult(
            status=PaymentStatus.CONFIRMED,
            provider_payment_id="resolved-provider-payment",
        )
        reconciled, reconciled_attempt = reconcile_provider_payment(
            payment_id=payment.id, provider=provider, actor=self.actor
        )
        assert reconciled.status == PaymentStatus.CONFIRMED
        assert reconciled.confirmed_at is not None
        assert reconciled_attempt.status == PaymentAttemptStatus.CONFIRMED
        assert totals(self.tab)["payments_cents"] == 3000
        assert totals(self.tab)["exposure_cents"] == 0
        self.tab.refresh_from_db()
        assert self.tab.state == "CLOSED"
        assert self.tab.closed_at is not None

    def test_confirmed_provider_money_survives_stale_service_without_closing(self):
        from modules.ledger.models import LedgerAdjustment, AdjustmentAllocation
        from modules.audit.models import AuditEvent
        charge = self.tab.charges.get()
        assessment = LedgerAdjustment.objects.create(tab=self.tab, kind="SERVICE_CHARGE",
            amount_cents=0, idempotency_key="service-assessment", reason_code="TEST",
            created_by=self.staff)
        AdjustmentAllocation.objects.create(adjustment=assessment, charge=charge,
            amount_cents=0, basis_cents=3000)
        provider = DeterministicPaymentProvider(start_result=ProviderResult(
            status=PaymentStatus.PENDING, provider_payment_id="stale-service-payment"))
        payment, _, _ = self.initiate(provider)
        provider.lookup_results[str(payment.id)] = ProviderResult(
            status=PaymentStatus.CONFIRMED, provider_payment_id="stale-service-payment")
        # New confirmed consumption plus a compensating reversal keeps the total
        # while changing the per-charge service basis after provider initiation.
        other = OrderItem.objects.create(order=charge.order_item.order, product=charge.order_item.product,
            product_name_snapshot="Outro item", unit_price_cents=100, quantity=1)
        Charge.objects.create(tab=self.tab, order_item=other, amount_cents=100)
        adjustment = LedgerAdjustment.objects.create(tab=self.tab, kind="COURTESY",
            amount_cents=-100, idempotency_key="basis-change", reason_code="TEST", created_by=self.staff)
        AdjustmentAllocation.objects.create(adjustment=adjustment, charge=charge,
            amount_cents=-100, basis_cents=3000)
        assert totals(self.tab)["service_assessment_stale"]
        confirmed, _ = reconcile_provider_payment(payment_id=payment.id, provider=provider, actor=self.actor)
        self.tab.refresh_from_db()
        assert confirmed.status == PaymentStatus.CONFIRMED
        assert totals(self.tab)["exposure_cents"] == 0
        assert self.tab.state == "OPEN"
        assert not AuditEvent.objects.filter(event_type="tab.closed", entity_id=str(self.tab.id)).exists()

    def test_duplicate_and_reordered_provider_events_are_safe(self):
        provider = DeterministicPaymentProvider(
            start_result=ProviderResult(
                status=PaymentStatus.PENDING,
                provider_payment_id="provider-payment-1",
            )
        )
        payment, _attempt, _ = self.initiate(provider)
        confirmed_payload = self.webhook_payload(
            payment, event_id="provider-event-confirmed", status=PaymentStatus.CONFIRMED
        )
        event, duplicate = ingest_provider_webhook(
            provider=provider, payload=confirmed_payload, signature="test-valid-signature"
        )
        assert not duplicate
        assert event.processing_status == ProviderEventProcessingStatus.APPLIED
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.CONFIRMED
        assert totals(self.tab)["payments_cents"] == 3000

        duplicate_event, duplicate = ingest_provider_webhook(
            provider=provider, payload=confirmed_payload, signature="test-valid-signature"
        )
        assert duplicate
        assert duplicate_event.id == event.id
        assert ProviderEvent.objects.count() == 1
        from modules.audit.models import AuditEvent
        self.tab.refresh_from_db()
        assert self.tab.state == "CLOSED"
        closed = AuditEvent.objects.get(event_type="tab.closed", entity_id=str(self.tab.id))
        assert closed.metadata["payment_id"] == str(payment.id)
        assert closed.actor_staff_id is None

        failed_payload = self.webhook_payload(
            payment, event_id="provider-event-late-failure", status=PaymentStatus.FAILED
        )
        late_event, duplicate = ingest_provider_webhook(
            provider=provider, payload=failed_payload, signature="test-valid-signature"
        )
        assert not duplicate
        assert late_event.processing_status == ProviderEventProcessingStatus.IGNORED
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.CONFIRMED
        assert totals(self.tab)["payments_cents"] == 3000

    def test_event_id_with_different_payload_is_rejected_and_bad_signature_never_enters_inbox(self):
        provider = DeterministicPaymentProvider()
        payment, _attempt, _ = self.initiate(provider)
        payload = self.webhook_payload(payment, event_id="reused-event", status=PaymentStatus.PENDING)
        ingest_provider_webhook(provider=provider, payload=payload, signature="test-valid-signature")
        conflicting = {**payload, "status": PaymentStatus.CONFIRMED}
        with self.assertRaises(ProviderServiceError) as captured:
            ingest_provider_webhook(
                provider=provider, payload=conflicting, signature="test-valid-signature"
            )
        assert captured.exception.code == "PROVIDER_EVENT_CONFLICT"
        with self.assertRaises(ProviderServiceError) as captured:
            ingest_provider_webhook(provider=provider, payload=payload, signature="not-valid")
        assert captured.exception.code == "INVALID_PROVIDER_SIGNATURE"
        assert ProviderEvent.objects.count() == 1

    def test_provider_pending_payment_blocks_a_second_blind_integrated_charge(self):
        provider = DeterministicPaymentProvider()
        self.initiate(provider, key="first-provider-intent")
        with self.assertRaises(ProviderServiceError) as captured:
            self.initiate(provider, key="second-provider-intent")
        assert captured.exception.code == "PAYMENT_ALREADY_PENDING"
