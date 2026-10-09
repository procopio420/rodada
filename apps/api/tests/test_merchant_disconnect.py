"""Provider-contract doubles only; these tests do not establish settlement."""
from django.test import TestCase
from django.utils import timezone
from modules.ledger.models import Payment
from modules.payment_provider.models import MerchantConnection
from modules.payment_provider.merchant_services import disconnect_connection
from modules.payment_provider.services import ProviderServiceError
from modules.audit.models import AuditEvent
from tests import test_payment_provider as fixture_module


class MerchantDisconnectTests(TestCase):
    def setUp(self):
        fixture = fixture_module.PaymentProviderServiceTests()
        fixture.setUp()
        self.actor, self.tab, self.venue = fixture.actor, fixture.tab, fixture.venue
        self.connection = MerchantConnection.objects.create(
            venue=self.venue, provider="sumup", merchant_code="MERCHANT-A",
            encrypted_credentials="encrypted-historical-credentials",
        )

    def payment(self, status):
        return Payment.objects.create(tab=self.tab, amount_cents=1000, method="PIX",
            provider=f"sumup:{self.venue.pk}:MERCHANT-A", status=status,
            idempotency_key="disconnect-payment", received_by_id=self.actor.staff_id,
            confirmed_at=timezone.now() if status == "CONFIRMED" else None)

    def test_all_unresolved_states_preserve_connection_and_credentials(self):
        for status in ("CREATED", "PENDING", "PROCESSING", "AUTHORIZED", "CONFIRMATION_PENDING"):
            with self.subTest(status=status):
                payment = self.payment(status)
                with self.assertRaises(ProviderServiceError) as error:
                    disconnect_connection(connection_id=self.connection.pk, actor=self.actor)
                self.assertEqual(error.exception.code, "MERCHANT_PAYMENTS_PENDING")
                self.connection.refresh_from_db()
                self.assertTrue(self.connection.active)
                self.assertEqual(self.connection.encrypted_credentials, "encrypted-historical-credentials")
                payment.delete()

    def test_terminal_history_preserved_and_retry_is_idempotent(self):
        self.payment("CONFIRMED")
        disconnect_connection(connection_id=self.connection.pk, actor=self.actor)
        disconnect_connection(connection_id=self.connection.pk, actor=self.actor)
        self.connection.refresh_from_db()
        self.assertFalse(self.connection.active)
        self.assertEqual(self.connection.encrypted_credentials, "encrypted-historical-credentials")
        self.assertEqual(AuditEvent.objects.filter(event_type="payment.merchant_disconnected").count(), 1)

    def test_stale_adapter_cannot_persist_new_payment(self):
        from modules.payment_provider.adapters import DeterministicPaymentProvider
        from modules.payment_provider.services import initiate_provider_payment
        provider = DeterministicPaymentProvider()
        provider.provider_key = f"sumup:{self.venue.pk}:MERCHANT-A"
        disconnect_connection(connection_id=self.connection.pk, actor=self.actor)
        with self.assertRaises(ProviderServiceError) as error:
            initiate_provider_payment(tab_id=self.tab.pk, amount_cents=1000, method="PIX",
                idempotency_key="stale", provider=provider, actor=self.actor)
        self.assertEqual(error.exception.code, "MERCHANT_DISCONNECTED")
        self.assertFalse(Payment.objects.exists())
        self.assertEqual(provider.start_calls, [])


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections, connection
from django.test import TransactionTestCase


class MerchantDisconnectConcurrencyTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor != "postgresql":
            self.fail("Merchant disconnect serialization requires PostgreSQL")
        fixture = fixture_module.PaymentProviderServiceTests()
        fixture.setUp()
        self.actor, self.tab, self.venue = fixture.actor, fixture.tab, fixture.venue
        self.connection = MerchantConnection.objects.create(
            venue=self.venue, provider="sumup", merchant_code="MERCHANT-A",
            encrypted_credentials="encrypted-history",
        )

    def test_disconnect_against_payment_reservation_has_one_safe_winner(self):
        from modules.payment_provider.adapters import DeterministicPaymentProvider
        from modules.payment_provider.services import _create_or_replay_provider_payment
        barrier = Barrier(2)
        provider = DeterministicPaymentProvider()
        provider.provider_key = f"sumup:{self.venue.pk}:MERCHANT-A"
        provider.connection_id = self.connection.pk

        def run(create):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                if create:
                    _create_or_replay_provider_payment(tab_id=self.tab.pk, amount_cents=1000,
                        method="PIX", idempotency_key="race", provider=provider, actor=self.actor)
                    return "CREATED"
                disconnect_connection(connection_id=self.connection.pk, actor=self.actor)
                return "DISCONNECTED"
            except ProviderServiceError as error:
                return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            creation = pool.submit(run, True)
            removal = pool.submit(run, False)
            outcomes = (creation.result(timeout=20), removal.result(timeout=20))
        self.assertIn(outcomes, (("CREATED", "MERCHANT_PAYMENTS_PENDING"),
            ("MERCHANT_DISCONNECTED", "DISCONNECTED")))
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.active, Payment.objects.exists())
        self.assertEqual(provider.start_calls, [])

    def test_cross_venue_disconnect_cannot_access_connection(self):
        from dataclasses import replace
        from modules.venue.models import Venue
        other = Venue.objects.create(name="Other", slug="other-disconnect")
        with self.assertRaises(MerchantConnection.DoesNotExist):
            disconnect_connection(connection_id=self.connection.pk,
                actor=replace(self.actor, venue_id=other.pk))
        self.connection.refresh_from_db()
        self.assertTrue(self.connection.active)
