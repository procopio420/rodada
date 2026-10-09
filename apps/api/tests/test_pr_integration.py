"""Cross-PR financial and production regression checks."""
from django.test import TestCase

from tests.test_pricing import PricingFixture


class IntegratedPricingTests(PricingFixture, TestCase):
    def test_priced_payment_replays_after_close_and_production_can_finish(self):
        self.assertEqual(self.apply(self.command(value=200)).status_code, 200)
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        before = self.detail()
        payload = {"amount_cents": 1980, "method": "OTHER", "idempotency_key": "integrated",
                   "expected_version": before["version"]}
        route = f"/tabs/{self.tab.id}/payments/"
        original = self.client.post(route, payload, format="json")
        self.assertEqual(original.status_code, 201, original.json())
        closed = self.client.post(f"/tabs/{self.tab.id}/close/", {}, format="json")
        self.assertEqual(closed.status_code, 200, closed.json())
        retry = self.client.post(route, payload, format="json")
        self.assertEqual(retry.status_code, 201, retry.json())
        self.assertEqual(retry.json()["id"], original.json()["id"])
        for state in ("ACCEPTED", "PREPARING", "READY"):
            result = self.client.post(f"/order-items/{self.charge.order_item_id}/transition/",
                                      {"state": state}, format="json")
            self.assertEqual(result.status_code, 200, result.json())
        after = self.detail()
        self.assertEqual(after["exposure_cents"], 0)
        self.assertEqual(after["payable_cents"], 1980)
        self.assertEqual(self.tab.payments.count(), 1)

    def test_receipt_freezes_pricing_totals_while_new_checks_follow_adjustments(self):
        route = "/printing/documents/"
        payload = {"tab_id": str(self.tab.id), "kind": "CUSTOMER_CHECK"}
        original = self.client.post(route, payload, format="json")
        self.assertEqual(original.status_code, 201, original.json())
        self.assertEqual(self.apply(self.command(value=200)).status_code, 200)
        self.assertEqual(self.apply(self.command("SERVICE_CHARGE", 1000)).status_code, 200)
        revised = self.client.post(route, payload, format="json")
        self.assertEqual(revised.status_code, 201, revised.json())
        totals = revised.json()["snapshot"]["totals"]
        self.assertEqual((totals["discounts_cents"], totals["service_charge_cents"],
                          totals["payable_cents"], totals["exposure_cents"]), (200, 180, 1980, 1980))
        frozen = self.client.get(f"/printing/documents/{original.json()['id']}/")
        self.assertEqual(frozen.status_code, 200)
        self.assertEqual(frozen.json()["snapshot"]["totals"]["payable_cents"], 2000)
        self.assertNotEqual(original.json()["id"], revised.json()["id"])
