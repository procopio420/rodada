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

    def test_manager_cannot_configure_provider_or_change_existing_binding(self):
        self.membership.role = StaffRole.MANAGER
        self.membership.save()
        tokens = self.login()
        self.bearer(tokens['access_token'])
        self.client.post('/auth/reauthenticate/', {'pin': '1234'}, format='json')
        binding = MerchantConnection.objects.create(
            venue=self.venue, provider='SUMUP', merchant_code='EXISTING',
            encrypted_credentials='sealed-existing-credential',
        )
        before = dict(MerchantConnection.objects.values().get(pk=binding.pk))
        for method, path, body in (
            ('post', '/payments/merchant-connections/', {'code': 'untrusted-code', 'state': 'fake'}),
            ('delete', '/payments/merchant-connections/', {'connection_id': str(binding.pk)}),
            ('post', '/payments/device-authorizations/', {'connection_id': str(binding.pk)}),
        ):
            response = getattr(self.client, method)(path, body, format='json')
            self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(dict(MerchantConnection.objects.values().get(pk=binding.pk)), before)
        self.assertFalse(OAuthAuthorization.objects.exists())

    def test_owner_downgrade_rejects_browser_bound_oauth_callback(self):
        state = self.begin()
        self.membership.role = StaffRole.MANAGER
        self.membership.save()
        with patch('modules.payment_provider.merchant_views.complete_connection') as exchange:
            response = self.client.get('/payments/merchant-connections/callback/', {
                'state': state, 'code': 'private-code',
            })
        self.assertEqual(response.status_code, 403, response.data)
        exchange.assert_not_called()

    @override_settings(RODADA_BFF_HOST_SECRET="test-secret-only")
    def test_foreign_host_callback_fails_closed_without_consuming_state(self):
        from modules.access.models import StaffMember, VenueStaffMembership
        from modules.audit.models import AuditEvent
        from modules.payment_provider.merchant_services import complete_connection
        from modules.venue.models import Venue, VenueDomain
        from rest_framework.test import APIClient
        from tests.test_spec025_host_security import signed

        VenueDomain.objects.create(
            venue=self.venue, hostname="e2ea.rodada.bar", is_active=True, is_verified=True,
        )
        state_a = self.begin()
        other = Venue.objects.create(name="Other OAuth", slug="other-oauth")
        VenueDomain.objects.create(
            venue=other, hostname="e2eb.rodada.bar", is_active=True, is_verified=True,
        )
        staff_b = StaffMember.objects.create(display_name="OAuth B", login_identifier="oauth-b")
        staff_b.set_pin("5678")
        staff_b.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=other, staff_member=staff_b, role=StaffRole.OWNER)
        client_b = APIClient()
        tokens_b = client_b.post("/auth/login/", {
            "venue_slug": other.slug, "login_identifier": staff_b.login_identifier, "pin": "5678",
            "installation_id": "oauth-independent-b", "platform": "ANDROID",
        }, format="json", HTTP_HOST="api.rodada.bar").json()
        client_b.credentials(HTTP_AUTHORIZATION="Bearer " + tokens_b["access_token"])
        self.assertEqual(client_b.post(
            "/auth/reauthenticate/", {"pin": "5678"}, format="json",
        ).status_code, 200)
        started = client_b.post("/payments/merchant-connections/", {}, format="json")
        self.assertEqual(started.status_code, 200)
        state_b = parse_qs(urlparse(started.json()["authorization_url"]).query)["state"][0]
        client_b.credentials()
        identities = (
            (self.venue, "e2ea.rodada.bar", self.client, state_a),
            (other, "e2eb.rodada.bar", client_b, state_b),
        )
        path = "/payments/merchant-connections/callback/"
        with patch("modules.payment_provider.merchant_views.complete_connection") as exchange:
            for own, foreign in ((identities[0], identities[1]), (identities[1], identities[0])):
                venue, _, client, state = own
                response = client.get(path, {"state": state, "code": "private-code"},
                                      **signed(foreign[1], method=path))
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["code"], "VENUE_HOST_MISMATCH")
                self.assertIsNone(OAuthAuthorization.objects.get(venue=venue).consumed_at)
        exchange.assert_not_called()
        self.assertFalse(MerchantConnection.objects.exists())

        # Exchange contract doubles; no provider network or financial settlement.
        bindings = {str(venue.pk): client.cookies["rodada_payment_oauth"].value
                    for venue, _, client, _ in identities}
        transports = []

        def complete(**kwargs):
            venue_id = str(kwargs["actor"].venue_id)

            def transport(endpoint, body=None, access_token=None):
                transports.append((venue_id, endpoint))
                if endpoint == "/v0.1/me":
                    return {"merchant_profile": {"merchant_code": "MERCHANT-" + venue_id}}
                return {"access_token": "private-access", "refresh_token": "private-refresh",
                        "expires_in": 3600, "scope": "payments transactions.history"}

            return complete_connection(**kwargs, transport=transport)

        with patch("modules.payment_provider.merchant_views.complete_connection", side_effect=complete):
            for venue, host, client, state in identities:
                response = client.get(path, {"state": state, "code": "private-code"},
                                      **signed(host, method=path))
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b"private", response.content)
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertTrue(MerchantConnection.objects.filter(
                    venue=venue, merchant_code="MERCHANT-" + str(venue.pk)).exists())
                # Replay the original browser cookie, not just an empty deleted cookie.
                client.cookies["rodada_payment_oauth"] = bindings[str(venue.pk)]
                replay = client.get(path, {"state": state, "code": "private-code"},
                                    **signed(host, method=path))
                self.assertEqual(replay.status_code, 409)
        self.assertEqual(len(transports), 4)
        self.assertEqual(MerchantConnection.objects.count(), 2)
        self.assertEqual(AuditEvent.objects.filter(event_type="payment.merchant_connected").count(), 2)

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
