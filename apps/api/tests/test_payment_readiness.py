import base64
from io import StringIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from modules.access.models import StaffRole, StaffSession
from modules.ledger.services import totals
from modules.payment_provider.models import MerchantConnection, OAuthAuthorization
from modules.payment_provider.services import ProviderServiceError, reconcile_provider_payment
from modules.payment_provider.views import cache_pix_qr, payment_response
from tests import test_access_api as access_tests
from tests import test_sumup_payments as sumup_tests


class PixRecoveryTests(TestCase):
    setUp = sumup_tests.SumUpContractTests.setUp
    provider = sumup_tests.SumUpContractTests.provider
    start = sumup_tests.SumUpContractTests.start

    def test_artifacts_expiry_and_identity_survive_lookup_without_artifacts(self):
        provider = self.provider()
        payment = self.start(provider)
        attempt = payment.provider_attempts.get()
        attempt.metadata.update(
            expires_at="2026-10-09T20:00:00Z", pix_qr_code="data:image/png;base64,test"
        )
        attempt.save()
        original = provider.transport

        def transport(method, path, body=None):
            data = original(method, path, body)
            data.pop("qr_code_pix", None)
            return data

        provider.transport = transport
        payment, _ = reconcile_provider_payment(
            payment_id=payment.pk, provider=provider, actor=self.actor
        )
        response = payment_response(payment)
        self.assertEqual(response["pix_copy_paste"], "provider-payload")
        self.assertEqual(response["pix_qr_code"], "data:image/png;base64,test")
        self.assertEqual(response["expires_at"], "2026-10-09T20:00:00Z")
        self.assertEqual(response["provider_payment_id"], "checkout-1")
        self.assertEqual(totals(self.tab)["payments_cents"], 0)

    def test_checkout_return_url_uses_configured_https_backend(self):
        provider = self.provider()
        provider.webhook_base_url = "https://api.rodada.ai"
        self.start(provider)
        self.assertEqual(
            self.calls[0][2]["return_url"],
            f"https://api.rodada.ai/payments/webhooks/sumup/{self.venue.pk}/",
        )

    def test_qr_fetch_can_recover_without_recreating_payment(self):
        provider = self.provider()
        payment = self.start(provider)
        attempt = payment.provider_attempts.get()
        with patch.object(
            provider, "qr_code", side_effect=[TimeoutError(), "data:image/png;base64,recovered"]
        ) as fetch:
            cache_pix_qr(payment, attempt, provider)
            cache_pix_qr(payment, attempt, provider)
            attempt.refresh_from_db()
            cache_pix_qr(payment, attempt, provider)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(
            payment_response(payment)["pix_qr_code"], "data:image/png;base64,recovered"
        )
        self.assertEqual(sum(method == "POST" for method, _, _ in self.calls), 1)

    def test_historical_paytime_connection_survives_primary_removal(self):
        from modules.payment_provider.registry import provider_for_venue

        config = {
            "base_url": "https://api.sandbox.paytime.com.br",
            "integration_key": "test",
            "x_token": "test",
            "bearer_token": "test",
            "establishment_id": "1",
            "webhook_user": "test",
            "webhook_password": "test",
        }
        with override_settings(
            RODADA_PAYMENT_PROVIDERS={}, RODADA_PAYTIME_PROVIDERS={str(self.venue.pk): config}
        ):
            adapter = provider_for_venue(self.venue.pk, provider_key=f"paytime:{self.venue.pk}")
            self.assertEqual(adapter.provider_key, f"paytime:{self.venue.pk}")

    def test_distinct_checkouts_cannot_own_same_settlement(self):
        from modules.ledger.models import Payment
        from modules.payment_provider.adapters import ProviderResult
        from modules.payment_provider.models import PaymentAttempt
        from modules.payment_provider.services import apply_provider_result
        from modules.payment_provider.sumup import settlement_key

        provider = self.provider()
        payment = self.start(provider)
        self.remote_state = "PAID"
        reconcile_provider_payment(payment_id=payment.pk, provider=provider, actor=self.actor)
        other = Payment.objects.create(
            tab=self.tab,
            provider=provider.provider_key,
            amount_cents=1001,
            method="PIX",
            status="PENDING",
            idempotency_key="duplicate-financial-owner",
            provider_payment_id="different-checkout",
            received_by=self.staff,
        )
        attempt = PaymentAttempt.objects.create(
            payment=other, provider=other.provider, idempotency_key=other.idempotency_key
        )
        other, attempt, _ = apply_provider_result(
            payment_id=other.pk,
            attempt_id=attempt.pk,
            result=ProviderResult(
                status="CONFIRMED",
                metadata={"settlement_key": settlement_key("MERCHANT-A", "transaction-1")},
            ),
            actor=self.actor,
        )
        self.assertEqual(other.status, "CONFIRMATION_PENDING")
        self.assertEqual(attempt.error_code, "SETTLEMENT_ALREADY_OWNED")
        self.assertEqual(totals(self.tab)["payments_cents"], 1001)

    def test_unsigned_sumup_notifications_only_request_lookup(self):
        import uuid

        from rest_framework.test import APIClient

        provider = self.provider()
        payment = self.start(provider)
        client = APIClient()
        payload = {
            "event_type": "CHECKOUT_STATUS_CHANGED",
            "id": payment.provider_payment_id,
            "status": "PAID",
            "amount": 1001,
        }
        for _ in range(2):
            response = client.post(
                f"/payments/webhooks/sumup/{self.venue.pk}/", payload, format="json"
            )
            self.assertEqual(response.status_code, 204)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(totals(self.tab)["payments_cents"], 0)
        attempt = payment.provider_attempts.get()
        self.assertIn("untrusted_lookup_requested_at", attempt.metadata)
        before = attempt.metadata
        client.post(f"/payments/webhooks/sumup/{uuid.uuid4()}/", payload, format="json")
        client.post(
            f"/payments/webhooks/sumup/{self.venue.pk}/",
            {"event_type": "UNKNOWN", "id": payment.provider_payment_id},
            format="json",
        )
        attempt.refresh_from_db()
        self.assertEqual(attempt.metadata, before)
        self.remote_state = "PAID"
        reconcile_provider_payment(payment_id=payment.pk, provider=provider, actor=self.actor)
        client.post(f"/payments/webhooks/sumup/{self.venue.pk}/", payload, format="json")
        payment.refresh_from_db()
        self.assertEqual(payment.status, "CONFIRMED")
        self.assertEqual(totals(self.tab)["payments_cents"], 1001)

    def test_worker_continues_after_unavailable_configuration(self):
        provider = self.provider()
        self.start(provider)
        # A second Tab allows a separate pending intent, preserving the duplicate-charge guard.
        from modules.ledger.models import Payment
        from modules.ordering.models import Tab

        payment = Payment.objects.first()
        payment.pk = None
        payment.tab = Tab.objects.create(venue=self.venue, display_label="Second")
        payment.idempotency_key = "second"
        payment.provider_payment_id = ""
        payment.save()
        output = StringIO()
        with (
            patch(
                "modules.payment_provider.management.commands.reconcile_payments.provider_for_venue",
                side_effect=[ProviderServiceError("UNAVAILABLE", "Unavailable"), provider],
            ),
            patch(
                "modules.payment_provider.management.commands.reconcile_payments.reconcile_provider_payment",
                return_value=(payment, None),
            ) as lookup,
        ):
            call_command("reconcile_payments", stdout=output)
        self.assertEqual(lookup.call_count, 1)
        self.assertIn("Checked 2 payments", output.getvalue())
        self.assertIn("unavailable 1", output.getvalue())


@override_settings(
    RODADA_PAYMENT_CREDENTIAL_KEY=base64.b64encode(bytes(range(32))).decode(),
    RODADA_SUMUP_OAUTH={
        "client_id": "client",
        "client_secret": "secret",
        "redirect_uri": "https://api.rodada.ai/payments/merchant-connections/callback/",
    },
)
class MerchantCallbackTests(TestCase):
    setUp = access_tests.StaffAuthAPITests.setUp
    login = access_tests.StaffAuthAPITests.login
    bearer = access_tests.StaffAuthAPITests.bearer

    def begin(self):
        self.membership.role = StaffRole.OWNER
        self.membership.save()
        tokens = self.login()
        self.bearer(tokens["access_token"])
        self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json")
        response = self.client.post("/payments/merchant-connections/", {}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.cookies["rodada_payment_oauth"]["secure"])
        self.assertTrue(response.cookies["rodada_payment_oauth"]["httponly"])
        self.client.credentials()
        return parse_qs(urlparse(response.data["authorization_url"]).query)["state"][0]

    def test_browser_callback_exchanges_once_without_exposing_tokens(self):
        state = self.begin()
        from modules.payment_provider.merchant_services import complete_connection

        def transport(path, body=None, access_token=None):
            if path == "/v0.1/me":
                return {"merchant_profile": {"merchant_code": "MERCHANT-A"}}
            return {
                "access_token": "private-access",
                "refresh_token": "private-refresh",
                "expires_in": 3600,
                "scope": "payments transactions.history",
            }

        def complete(**kwargs):
            return complete_connection(**kwargs, transport=transport)

        with patch(
            "modules.payment_provider.merchant_views.complete_connection", side_effect=complete
        ) as exchange:
            response = self.client.get(
                "/payments/merchant-connections/callback/", {"state": state, "code": "private-code"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b"private", response.content)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.client.get(
                "/payments/merchant-connections/callback/", {"state": state, "code": "private-code"}
            )
            self.assertEqual(exchange.call_count, 1)
        self.assertEqual(MerchantConnection.objects.count(), 1)

    def test_denial_consumes_state_without_exchange(self):
        state = self.begin()
        with patch("modules.payment_provider.merchant_views.complete_connection") as exchange:
            response = self.client.get(
                "/payments/merchant-connections/callback/",
                {"state": state, "error": "access_denied", "error_description": "secret"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(exchange.called)
        self.assertIsNotNone(OAuthAuthorization.objects.get().consumed_at)
        self.assertNotIn(b"secret", response.content)

    def test_wrong_browser_wrong_state_and_revoked_session_never_exchange(self):
        state = self.begin()
        with patch("modules.payment_provider.merchant_views.complete_connection") as exchange:
            self.assertGreaterEqual(
                self.client.get(
                    "/payments/merchant-connections/callback/", {"state": "wrong", "code": "code"}
                ).status_code,
                400,
            )
            StaffSession.objects.update(revoked_at=timezone.now())
            self.assertGreaterEqual(
                self.client.get(
                    "/payments/merchant-connections/callback/", {"state": state, "code": "code"}
                ).status_code,
                400,
            )
            self.client.cookies.clear()
            self.assertGreaterEqual(
                self.client.get(
                    "/payments/merchant-connections/callback/", {"state": state, "code": "code"}
                ).status_code,
                400,
            )
        self.assertFalse(exchange.called)
