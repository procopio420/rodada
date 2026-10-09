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
