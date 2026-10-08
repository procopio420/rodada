"""Executable HTTP E2E against a real Django live server and persistent test DB.

No provider or ledger mocks: EXTERNAL_TERMINAL is the existing operator-confirmed
payment method. Both resolution paths exercise real authentication and APIs.
"""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.test import LiveServerTestCase, override_settings

from modules.house_account.models import LimitOverride
from modules.ledger.models import Charge, Payment
from tests.test_house_account import HouseFixture


@override_settings(STATIC_URL="/static/")
class HouseAccountHttpE2E(HouseFixture, LiveServerTestCase):
    def http(self, client, path, body=None, expected=200):
        headers = {
            "Content-Type": "application/json",
            "Authorization": client._credentials["HTTP_AUTHORIZATION"],
        }
        request = Request(
            self.live_server_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
        )
        try:
            response = urlopen(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            payload = json.load(response)
            assert response.status == expected, payload
            return payload

    def scenario(self, *, use_override):
        tab = self.http(self.staff, "/tabs/", {}, expected=201)
        tab_id = tab["id"]
        order_path = f"/tabs/{tab_id}/orders/confirm/"

        def order(key, qty, expected=201):
            return self.http(
                self.staff,
                order_path,
                {
                    "idempotency_key": key,
                    "lines": [{"product_id": str(self.product.id), "quantity": qty}],
                },
                expected,
            )

        order("consume", 2)
        order("hit-limit", 1)
        position = self.http(self.staff, f"/tabs/{tab_id}/")
        assert position["state"] == "REQUIRES_ACTION"
        assert position["remaining_capacity_cents"] == 0
        blocked = order("blocked", 1, 409)
        assert blocked["code"] == "SPENDING_LIMIT_EXCEEDED"
        assert Charge.objects.count() == 2
        if use_override:
            self.http(self.manager, "/auth/reauthenticate/", {"pin": "0420"})
            self.http(self.manager, f"/tabs/{tab_id}/limit-override/", self.override(tab_id))
            assert Payment.objects.count() == 0
            assert LimitOverride.objects.count() == 1
        else:
            self.http(
                self.cashier,
                f"/tabs/{tab_id}/payments/",
                {"amount_cents": 1000, "method": "EXTERNAL_TERMINAL", "idempotency_key": "partial"},
                expected=201,
            )
        order("continue", 1)
        order("continue", 1, 200)
        position = self.http(self.staff, f"/tabs/{tab_id}/")
        self.http(
            self.cashier,
            f"/tabs/{tab_id}/payments/",
            {
                "amount_cents": position["exposure_cents"],
                "method": "EXTERNAL_TERMINAL",
                "idempotency_key": "settle",
            },
            expected=201,
        )
        closed = self.http(self.cashier, f"/tabs/{tab_id}/close/", {})
        assert closed["state"] == "CLOSED"
        assert self.http(self.staff, f"/tabs/{tab_id}/")["exposure_cents"] == 0
        assert Charge.objects.count() == 3

    def test_open_consume_hit_limit_block_override_continue_pay_close(self):
        self.scenario(use_override=True)

    def test_open_consume_hit_limit_block_partial_continue_pay_close(self):
        self.scenario(use_override=False)
