import base64
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import FulfillmentStation, Product
from modules.ledger.models import Payment
from modules.payment_provider.models import ProviderEvent
from modules.payment_provider.paytime import PaytimePixProvider
from modules.venue.models import Venue


class PaytimeLiveTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Pix bar", slug="pix-bar")
        staff = StaffMember.objects.create(display_name="Cashier", login_identifier="pix")
        staff.set_pin("1234")
        staff.save()
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=staff, role=StaffRole.CASHIER
        )
        self.client = APIClient()
        token = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": "pix",
                "pin": "1234",
                "installation_id": "pix-device",
                "platform": "ANDROID",
            },
            format="json",
        ).json()["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        product = Product.objects.create(
            venue=self.venue,
            name="Beer",
            price_cents=3000,
            fulfillment_station=FulfillmentStation.BAR,
        )
        self.tab = self.client.post("/tabs/", {}, format="json").json()["id"]
        self.client.post(
            f"/tabs/{self.tab}/orders/confirm/",
            {"idempotency_key": "order", "lines": [{"product_id": str(product.pk), "quantity": 1}]},
            format="json",
        )
        config = {
            "base_url": "https://api.example.test",
            "integration_key": "secret-key",
            "x_token": "secret-token",
            "bearer_token": "secret-bearer",
            "establishment_id": 123,
            "webhook_user": "hook",
            "webhook_password": "secret",
        }
        setting = override_settings(RODADA_PAYMENT_PROVIDERS={str(self.venue.pk): config})
        setting.enable()
        self.addCleanup(setting.disable)
        self.remote = {
            "_id": "remote-1",
            "status": "PENDING",
            "type": "PIX",
            "original_amount": 1000,
            "amount": 970,
            "establishment": {"id": 123},
            "emv": "provider-emv",
        }
        self.calls = []

        def transport(adapter, method, path, body=None):
            self.calls.append((method, path, body))
            if path.endswith("/qrcode"):
                return {"qrcode": "data:image/gif;base64,R0lGODlh"}
            return dict(self.remote)

        transport_patch = patch.object(PaytimePixProvider, "_transport", transport)
        transport_patch.start()
        self.addCleanup(transport_patch.stop)
        self.hook = APIClient()
        self.hook.credentials(
            HTTP_AUTHORIZATION="Basic " + base64.b64encode(b"hook:secret").decode()
        )

    def create(self, **changes):
        return self.client.post(
            f"/tabs/{self.tab}/payments/integrated/",
            {"amount_cents": 1000, "method": "PIX", "idempotency_key": "pix-intent", **changes},
            format="json",
        )

    def webhook(self, status="PAID"):
        return self.hook.post(
            f"/payments/webhooks/paytime/{self.venue.pk}/",
            {
                "event": "updated-sub-transaction",
                "event_date": "2026-10-08T12:00:00Z",
                "data": {"_id": "remote-1", "status": status},
            },
            format="json",
        )

    def test_pix_create_restart_confirmation_duplicate_and_partial_balance(self):
        first = self.create()
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(first.data["status"], "PENDING")
        self.assertEqual(first.data["exposure_cents"], 3000)
        self.assertEqual(first.data["pix_copy_paste"], "provider-emv")
        self.assertTrue(first.data["pix_qr_code"].startswith("data:image/"))
        self.assertEqual(self.create().status_code, 200)
        self.assertEqual(sum(method == "POST" for method, _, _ in self.calls), 1)
        self.assertEqual(self.calls[0][2]["interest"], "STORE")
        self.assertEqual(self.calls[0][2]["reference_id"], first.data["id"])
        self.remote["status"] = "PAID"
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(ProviderEvent.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        state = self.client.get(f"/payments/{first.data['id']}/integrated/").data
        self.assertEqual(state["status"], "CONFIRMED")
        self.assertEqual(state["payments_cents"], 1000)
        self.assertEqual(state["exposure_cents"], 2000)
        self.assertEqual(state["pix_copy_paste"], "provider-emv")

    def test_webhook_payload_cannot_confirm_without_provider_fact(self):
        first = self.create()
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(Payment.objects.get(pk=first.data["id"]).status, "PENDING")
        self.remote["original_amount"] = 2000
        self.assertEqual(self.webhook().status_code, 503)
        self.assertEqual(Payment.objects.get(pk=first.data["id"]).status, "PENDING")

    def test_invalid_credentials_never_enter_inbox(self):
        self.create()
        self.hook.credentials(HTTP_AUTHORIZATION="Basic invalid")
        self.assertEqual(self.webhook().status_code, 401)
        self.assertEqual(ProviderEvent.objects.count(), 0)

    def test_timeout_replays_without_post_and_blocks_alternative_charge(self):
        with patch.object(PaytimePixProvider, "_transport", side_effect=TimeoutError):
            first = self.create()
        self.assertEqual(first.data["status"], "CONFIRMATION_PENDING")
        self.assertEqual(self.create().status_code, 200)
        self.assertFalse(any(method == "POST" for method, _, _ in self.calls))
        alternative = self.client.post(
            f"/tabs/{self.tab}/payments/",
            {"amount_cents": 1000, "method": "EXTERNAL_TERMINAL", "idempotency_key": "other"},
            format="json",
        )
        self.assertEqual(alternative.status_code, 409)
        reconciled = self.client.post(
            f"/payments/{first.data['id']}/integrated/", {}, format="json"
        )
        self.assertEqual(reconciled.data["status"], "CONFIRMATION_PENDING")

    def test_scope_and_capabilities_and_invalid_amount(self):
        self.assertTrue(self.client.get("/payments/capabilities/").data["pix"])
        self.assertFalse(self.client.get("/payments/capabilities/").data["tap_to_pay"])
        self.assertEqual(self.create(method="TAP_TO_PAY").status_code, 409)
        for invalid in (True, 1.2, "1000", None):
            self.assertEqual(self.create(amount_cents=invalid).status_code, 400)
        first = self.create()
        foreign = Venue.objects.create(name="Foreign", slug="foreign")
        payment = Payment.objects.get(pk=first.data["id"])
        payment.tab.venue = foreign
        payment.tab.save(update_fields=["venue"])
        self.assertEqual(self.client.get(f"/payments/{payment.pk}/integrated/").status_code, 404)

    def test_cancellation_is_authoritative_and_never_regresses(self):
        first = self.create()
        self.remote["status"] = "CANCELED"
        self.client.post(f"/payments/{first.data['id']}/integrated/", {}, format="json")
        payment = Payment.objects.get(pk=first.data["id"])
        self.assertEqual(payment.status, "CANCELLED")

        self.remote["status"] = "PENDING"
        self.webhook("PENDING")
        payment.refresh_from_db()
        self.assertEqual(payment.status, "CANCELLED")

    def test_committed_integrated_payment_replays_after_financial_close(self):
        self.remote["original_amount"] = 3000
        first = self.create(amount_cents=3000)
        self.assertEqual(first.status_code, 201, first.data)
        self.remote["status"] = "PAID"
        self.assertEqual(self.webhook().status_code, 200)
        closed = self.client.post(f"/tabs/{self.tab}/close/", {}, format="json")
        self.assertEqual(closed.status_code, 200, closed.data)
        replay = self.create(amount_cents=3000, expected_version=1)
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(replay.data["id"], first.data["id"])
        self.assertEqual(replay.data["status"], "CONFIRMED")
        self.assertEqual(replay.data["exposure_cents"], 0)
        self.assertEqual(self.create(amount_cents=2000).data["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.create(idempotency_key="new").data["code"], "TAB_CLOSED")
        self.assertEqual(sum(method == "POST" for method, _, _ in self.calls), 1)
        self.assertEqual(Payment.objects.count(), 1)

    def test_malformed_integrated_intents_create_no_payment_or_external_request(self):
        for changes in (
            {"method": []}, {"method": {}}, {"method": True},
            {"amount_cents": 2147483648}, {"expected_version": True},
            {"expected_version": "1"}, {"expected_version": 0},
        ):
            with self.subTest(changes=changes):
                response = self.create(**changes)
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(self.calls, [])

    def test_sensitive_provider_response_is_not_persisted(self):
        self.remote.update(card={"pan": "sensitive", "cvv": "123"}, token="secret")
        first = self.create()
        payment = Payment.objects.get(pk=first.data["id"])
        self.assertNotIn("sensitive", str(payment.provider_attempts.first().metadata))
        self.assertNotIn("secret", str(payment.provider_attempts.first().metadata))

    def test_paytime_callback_remains_usable_after_primary_switch_to_sumup(self):
        from django.conf import settings

        first = self.create()
        paytime_config = settings.RODADA_PAYMENT_PROVIDERS[str(self.venue.pk)]
        with override_settings(
            RODADA_PAYMENT_PROVIDERS={str(self.venue.pk): {"provider": "sumup", "connection_id": "not-used"}},
            RODADA_PAYTIME_PROVIDERS={str(self.venue.pk): paytime_config},
        ):
            self.remote["status"] = "PAID"
            self.assertEqual(self.webhook().status_code, 200)
            payment = Payment.objects.get(pk=first.data["id"])
            self.assertEqual(payment.status, "CONFIRMED")

    @override_settings(DEBUG=True, RODADA_PAYMENT_SIMULATION=True)
    def test_simulated_api_split_settlement_history_and_close(self):
        from modules.access.models import DeviceRegistration

        DeviceRegistration.objects.filter(venue=self.venue).update(trust_state="TRUSTED")
        with override_settings(RODADA_PAYMENT_PROVIDERS={str(self.venue.pk): {"provider": "simulator"}}):
            for method, amount in (("PIX", 1000), ("TAP_TO_PAY", 2000)):
                result = self.create(method=method, amount_cents=amount, idempotency_key=method)
                self.assertEqual(result.status_code, 201, result.data)
                self.assertTrue(result.data["simulated"])
                self.assertEqual(result.data["exposure_cents"], 3000 if method == "PIX" else 2000)
                for _ in range(2):
                    response = self.client.post(f"/payments/{result.data['id']}/integrated/", {}, format="json")
                    self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data["status"], "CONFIRMED")
            history = self.client.get(f"/tabs/{self.tab}/").data
            self.assertTrue(all(payment["simulated"] for payment in history["payments"]))
            closed = self.client.post(f"/tabs/{self.tab}/close/", {}, format="json")
            self.assertEqual(closed.status_code, 200, closed.data)
