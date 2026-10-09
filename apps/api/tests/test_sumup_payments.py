import base64
from decimal import Decimal

from cryptography.exceptions import InvalidTag
from django.test import override_settings
from django.utils import timezone

from modules.ledger.models import PaymentStatus, RefundStatus
from modules.ledger.services import close_tab, totals
from modules.payment_provider.credentials import unseal
from modules.payment_provider.fake import DeterministicFakePaymentProvider
from modules.payment_provider.merchant_services import (
    access_token_for,
    begin_connection,
    complete_connection,
    disconnect_connection,
)
from modules.payment_provider.models import MerchantConnection
from modules.payment_provider.refunds import apply_refund_evidence, reserve_refund
from modules.payment_provider.registry import provider_for_venue
from modules.payment_provider.services import (
    ProviderServiceError,
    initiate_provider_payment,
    reconcile_provider_payment,
)
from modules.payment_provider.sumup import SumUpPixProvider, encode_body, major, minor
from tests import test_payment_provider as provider_tests


class SumUpContractTests(provider_tests.PaymentProviderServiceTests):
    def provider(self, *, payment_type="qr_code_pix"):
        self.calls = []
        self.remote_state = "PENDING"
        self.bad_merchant = False
        self.checkout = None

        def transport(method, path, body=None):
            self.calls.append((method, path, body))
            if method == "POST":
                self.checkout = {"id": "checkout-1", **body, "status": "PENDING"}
                return self.checkout
            if "payment-methods" in path:
                return {"items": [{"id": payment_type}]}
            if "/transactions?" in path:
                return {
                    "id": "transaction-1",
                    "amount": Decimal("10.01"),
                    "currency": "BRL",
                    "merchant_code": "OTHER" if self.bad_merchant else "MERCHANT-A",
                    "status": "SUCCESSFUL",
                }
            data = {
                **self.checkout,
                "status": self.remote_state,
                payment_type: {
                    "artefacts": [
                        {
                            "name": "code",
                            "content_type": "text/plain",
                            "content": "provider-payload",
                        },
                        {
                            "name": "barcode",
                            "location": "https://localhost:3000/private",
                            "content_type": "image/jpeg",
                        },
                    ]
                },
            }
            if self.remote_state == "PAID":
                data["transactions"] = [{"id": "transaction-1"}]
            return [data] if "checkout_reference=" in path else data

        return SumUpPixProvider(
            venue_id=self.venue.pk,
            merchant_code="MERCHANT-A",
            access_token="secret",
            payment_type=payment_type,
            transport=transport,
        )

    def start(self, provider, amount=1001, key="sumup"):
        return initiate_provider_payment(
            tab_id=self.tab.pk,
            amount_cents=amount,
            method="PIX",
            idempotency_key=key,
            provider=provider,
            actor=self.actor,
        )[0]

    def test_sumup_pix_contract_binding_partial_payment_and_exact_decimal(self):
        provider = self.provider()
        payment = self.start(provider)
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(self.calls[0][2]["amount"], Decimal("10.01"))
        self.assertIn('"amount":10.01', encode_body(self.calls[0][2]))
        self.assertEqual(self.start(provider).pk, payment.pk)
        self.assertEqual(sum(method == "POST" for method, _, _ in self.calls), 1)
        self.remote_state = "PAID"
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        self.assertEqual(payment.status, "CONFIRMED")
        self.assertEqual(totals(self.tab)["exposure_cents"], 1999)
        self.assertNotIn("pix_qr_location", payment.provider_attempts.first().metadata)

    def test_merchant_mismatch_and_unknown_result_cannot_establish_settlement(self):
        provider = self.provider()
        payment = self.start(provider)
        self.remote_state = "PAID"
        self.bad_merchant = True
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        self.assertEqual(payment.status, "CONFIRMATION_PENDING")
        self.assertEqual(totals(self.tab)["payments_cents"], 0)

    def test_sumup_expiry_is_provider_authoritative(self):
        provider = self.provider(payment_type="pix")
        payment = self.start(provider)
        self.remote_state = "EXPIRED"
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        self.assertEqual(payment.status, "EXPIRED")
        self.assertEqual(totals(self.tab)["payments_cents"], 0)

    def test_sumup_process_timeout_preserves_checkout_and_never_reprocesses(self):
        provider = self.provider()
        original = provider.transport

        def transport(method, path, body=None):
            if method == "PUT":
                raise TimeoutError("unknown")
            return original(method, path, body)

        provider.transport = transport
        payment = self.start(provider)
        self.assertEqual(payment.status, "CONFIRMATION_PENDING")
        payment.refresh_from_db()
        self.assertEqual(payment.provider_payment_id, "checkout-1")
        self.start(provider)
        self.assertEqual(sum(method == "POST" for method, _, _ in self.calls), 1)
        self.remote_state = "PAID"
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        self.assertEqual(payment.status, "CONFIRMED")

    def test_major_units_never_use_binary_floating_point(self):
        self.assertEqual(minor(major(9007199254740991)), 9007199254740991)
        with self.assertRaises(ValueError):
            minor(10.01)
        with self.assertRaises(ValueError):
            minor(Decimal("1.001"))

    @override_settings(DEBUG=True, RODADA_PAYMENT_SIMULATION=True)
    def test_simulator_restart_split_and_close(self):
        provider = DeterministicFakePaymentProvider(venue_id=self.venue.pk)
        pix = self.start(provider, amount=1000)
        for _ in range(2):
            pix, _ = reconcile_provider_payment(
                payment_id=pix.pk,
                provider=DeterministicFakePaymentProvider(venue_id=self.venue.pk),
                actor=self.actor,
            )
        self.assertEqual(totals(self.tab)["exposure_cents"], 2000)
        card, _, _ = initiate_provider_payment(
            tab_id=self.tab.pk,
            amount_cents=2000,
            method="TAP_TO_PAY",
            idempotency_key="card",
            provider=provider,
            actor=self.actor,
        )
        for _ in range(2):
            reconcile_provider_payment(payment_id=card.pk, provider=provider, actor=self.actor)
        self.assertEqual(close_tab(tab_id=self.tab.pk, actor=self.actor).state, "CLOSED")
        self.assertTrue(pix.provider_attempts.first().metadata["simulated"])

    @override_settings(DEBUG=False, RODADA_PAYMENT_SIMULATION=True)
    def test_production_refuses_simulator(self):
        with override_settings(
            RODADA_PAYMENT_PROVIDERS={str(self.venue.pk): {"provider": "simulator"}}
        ), self.assertRaises(ProviderServiceError):
            provider_for_venue(self.venue.pk)

    def test_refund_reservation_and_duplicate_evidence_preserve_history(self):
        provider = self.provider()
        payment = self.start(provider)
        self.remote_state = "PAID"
        reconcile_provider_payment(payment_id=payment.pk, provider=provider, actor=self.actor)
        refund, replay = reserve_refund(
            payment_id=payment.pk, amount_cents=500, key="refund", reason="wrong", actor=self.actor
        )
        self.assertFalse(replay)
        self.assertEqual(refund.status, RefundStatus.PENDING)
        with self.assertRaises(ProviderServiceError):
            reserve_refund(
                payment_id=payment.pk,
                amount_cents=600,
                key="other",
                reason="wrong",
                actor=self.actor,
            )
        event = {
            "event_type": "REFUND",
            "status": "SUCCESSFUL",
            "amount": Decimal("5.00"),
            "id": "refund-remote",
        }
        apply_refund_evidence(refund_id=refund.pk, event=event, actor=self.actor)
        apply_refund_evidence(refund_id=refund.pk, event=event, actor=self.actor)
        self.assertEqual(totals(self.tab)["refunds_cents"], 500)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatus.PARTIALLY_REFUNDED)
        self.assertEqual(payment.refunds.count(), 1)

    @override_settings(
        RODADA_PAYMENT_CREDENTIAL_KEY=base64.b64encode(bytes(range(32))).decode(),
        RODADA_SUMUP_OAUTH={
            "client_id": "client",
            "client_secret": "secret",
            "redirect_uri": "https://rodada.ai/callback",
        },
    )
    def test_oauth_state_once_encrypted_storage_refresh_and_disconnect(self):
        from urllib.parse import parse_qs, urlparse

        state = parse_qs(urlparse(begin_connection(self.actor)).query)["state"][0]

        def transport(path, body=None, access_token=None):
            if path == "/v0.1/me":
                return {"merchant_profile": {"merchant_code": "MERCHANT-A"}}
            return {
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "expires_in": 3600,
                "scope": "payments transactions.history",
            }

        connection = complete_connection(
            actor=self.actor, state=state, code="code", transport=transport
        )
        self.assertNotIn("secret", connection.encrypted_credentials)
        self.assertEqual(unseal(connection)["refresh_token"], "refresh-secret")
        with self.assertRaises(ProviderServiceError):
            complete_connection(actor=self.actor, state=state, code="code", transport=transport)
        connection.token_expires_at = timezone.now()
        connection.save()
        self.assertEqual(
            access_token_for(connection.pk, venue_id=self.venue.pk, transport=transport),
            "access-secret",
        )
        with self.assertRaises(MerchantConnection.DoesNotExist):
            access_token_for(connection.pk, venue_id="00000000-0000-0000-0000-000000000001")
        connection.refresh_from_db()
        connection.merchant_code = "OTHER"
        with self.assertRaises(InvalidTag):
            unseal(connection)
        disconnect_connection(connection_id=connection.pk, actor=self.actor)
        connection.refresh_from_db()
        self.assertFalse(connection.active)
        self.assertEqual(connection.encrypted_credentials, "")

    def test_tap_verification_uses_durable_client_transaction_id(self):
        from modules.payment_provider.sumup import SumUpTapToPayProvider

        calls = []

        def transport(method, path, body=None):
            calls.append(path)
            return {
                "id": "card-tx",
                "client_transaction_id": str(payment.pk),
                "merchant_code": "MERCHANT-A",
                "amount": Decimal("10.00"),
                "currency": "BRL",
                "status": "SUCCESSFUL",
            }

        provider = SumUpTapToPayProvider(
            venue_id=self.venue.pk,
            merchant_code="MERCHANT-A",
            access_token="secret",
            transport=transport,
        )
        payment, _, _ = initiate_provider_payment(
            tab_id=self.tab.pk,
            amount_cents=1000,
            method="TAP_TO_PAY",
            idempotency_key="tap",
            provider=provider,
            actor=self.actor,
        )
        self.assertEqual(payment.status, "PROCESSING")
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        self.assertEqual(payment.status, "CONFIRMED")
        self.assertIn("client_transaction_id=" + str(payment.pk), calls[0])

    def test_sumup_refund_post_is_not_confirmation_and_replay_never_posts_again(self):
        from modules.payment_provider.refunds import (
            reconcile_provider_refund,
            request_provider_refund,
        )

        provider = self.provider()
        payment = self.start(provider)
        self.remote_state = "PAID"
        reconcile_provider_payment(payment_id=payment.pk, provider=provider, actor=self.actor)
        calls = []
        events = []

        def transport(method, path, body=None):
            calls.append((method, body))
            if method == "POST":
                raise TimeoutError("accepted then timed out")
            return {
                "id": "transaction-1",
                "merchant_code": "MERCHANT-A",
                "transaction_events": events,
            }

        provider.transport = transport
        refund = request_provider_refund(
            payment_id=payment.pk,
            amount_cents=500,
            key="refund-intent",
            reason="wrong",
            actor=self.actor,
            provider=provider,
        )
        self.assertEqual(refund.status, "PENDING")
        request_provider_refund(
            payment_id=payment.pk,
            amount_cents=500,
            key="refund-intent",
            reason="wrong",
            actor=self.actor,
            provider=provider,
        )
        self.assertEqual(sum(method == "POST" for method, _ in calls), 1)
        self.assertEqual(totals(self.tab)["refunds_cents"], 0)
        events.append(
            {
                "id": "new-refund",
                "event_type": "REFUND",
                "status": "SUCCESSFUL",
                "amount": Decimal("5.00"),
            }
        )
        refund = reconcile_provider_refund(refund_id=refund.pk, actor=self.actor, provider=provider)
        self.assertEqual(refund.status, "CONFIRMED")
        self.assertEqual(totals(self.tab)["refunds_cents"], 500)

    def test_paytime_alternative_selection_when_sumup_is_primary(self):
        config = {
            "base_url": "https://sandbox.paytime.com.br",
            "integration_key": "test", "x_token": "test", "bearer_token": "test",
            "establishment_id": "merchant-a", "webhook_user": "test", "webhook_password": "test",
        }
        with override_settings(
            RODADA_PAYMENT_PROVIDERS={str(self.venue.pk): {"provider": "sumup", "connection_id": "not-used"}},
            RODADA_PAYTIME_PROVIDERS={str(self.venue.pk): config},
        ):
            adapter = provider_for_venue(self.venue.pk, provider_key=f"paytime:{self.venue.pk}")
            self.assertEqual(adapter.provider_key, f"paytime:{self.venue.pk}")
            with self.assertRaises(ProviderServiceError):
                provider_for_venue(self.venue.pk, provider_key="paytime:another-venue")

    def test_paid_checkout_with_mismatched_transaction_identity_never_settles(self):
        provider = self.provider()
        payment = self.start(provider)
        original = provider.transport
        self.remote_state = "PAID"
        def transport(method, path, body=None):
            result = original(method, path, body)
            if "/transactions?" in path:
                result["id"] = "wrong-transaction"
            return result
        provider.transport = transport
        payment, _ = reconcile_provider_payment(payment_id=payment.pk, provider=provider, actor=self.actor)
        self.assertEqual(payment.status, "CONFIRMATION_PENDING")
        self.assertEqual(totals(self.tab)["payments_cents"], 0)
