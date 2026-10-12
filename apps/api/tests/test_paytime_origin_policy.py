"""Provider onboarding security gates; no PSP calls or settlement assertions."""
from django.test import SimpleTestCase

from modules.payment_provider.paytime import PaytimePixProvider


class PaytimeOriginPolicyTests(SimpleTestCase):
    def provider(self, origin):
        return PaytimePixProvider(
            venue_id="00000000-0000-4000-8000-000000000001",
            base_url=origin,
            integration_key="isolated-test-integration",
            x_token="isolated-test-token",
            authentication_key="isolated-test-auth",
            establishment_id="123",
            webhook_user="test-hook",
            webhook_password="test-only",
        )

    def test_valid_https_origin_is_normalized_and_does_not_request_network(self):
        for origin in ("https://sandbox.example.test", "https://sandbox.example.test/"):
            with self.subTest(origin=origin):
                provider = self.provider(origin)
                self.assertEqual(provider.base_url, "https://sandbox.example.test")
                self.assertEqual(provider.establishment_id, "123")

    def test_rejects_ambiguous_or_credential_bearing_api_urls(self):
        for origin in (
            "http://sandbox.example.test",
            "https://",
            "https://user@sandbox.example.test",
            "https://user:password@sandbox.example.test",
            "https://sandbox.example.test/api",
            "https://sandbox.example.test/?access_token=sensitive",
            "https://sandbox.example.test/#fragment",
            "https://sandbox.example.test:invalid",
            "https://sandbox.example.test:0",
            "https://sandbox.example.test:65536",
            " https://sandbox.example.test",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self.provider(origin)

    def test_missing_merchant_credentials_stays_rejected(self):
        with self.assertRaises(ValueError):
            PaytimePixProvider(
                venue_id="00000000-0000-4000-8000-000000000001",
                base_url="https://sandbox.example.test",
                integration_key="only-one-field",
                x_token="",
                authentication_key="",
                establishment_id="123",
                webhook_user="hook",
                webhook_password="",
            )
