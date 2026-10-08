"""Real HTTP full-service split, transfer, merge, payment, close and reopen."""
from django.test import LiveServerTestCase, override_settings
from tests.test_house_account_e2e import HouseAccountHttpE2E
from tests.test_tab_operations import OperationFixture
from modules.ledger.models import Charge, Payment
from modules.tab_operations.models import TabTransferLine


@override_settings(STATIC_URL="/static/")
class TabOperationHttpE2E(OperationFixture, LiveServerTestCase):
    http = HouseAccountHttpE2E.http

    def test_shift_split_transfer_merge_pay_close_reopen(self):
        def tab(label):
            return self.http(self.staff, "/tabs/", {"display_label": label}, expected=201)
        source, dest, third = tab("Grupo"), tab("Separada"), tab("Duplicada")
        source_id, dest_id, third_id = source["id"], dest["id"], third["id"]
        order = self.http(self.staff, f"/tabs/{source_id}/orders/confirm/", {
            "idempotency_key": "order", "lines": [{"product_id": str(self.product.id), "quantity": 3}]}, expected=201)
        def detail(id):
            return self.http(self.cashier, f"/tabs/{id}/operations/")
        def transfer(src, dst, kind, key, quantity=None):
            state = detail(src)
            body = {"kind": kind, "expected_version": state["tab"]["version"],
                "destination_tab_id": dst, "destination_version": detail(dst)["tab"]["version"], "idempotency_key": key}
            if quantity:
                body["lines"] = [{"charge_id": state["lines"][0]["charge_id"], "quantity": quantity}]
            preview = self.http(self.cashier, f"/tabs/{src}/operations/preview/", body)
            result = self.http(self.cashier, f"/tabs/{src}/operations/", body)
            assert result["amount_cents"] == preview["amount_cents"]
            assert result == self.http(self.cashier, f"/tabs/{src}/operations/", body)
            return result
        transfer(source_id, dest_id, "SPLIT", "split", 2)
        transfer(dest_id, third_id, "MOVE_ITEMS", "move", 1)
        result = transfer(third_id, dest_id, "MERGE", "merge")
        assert result["source"]["state"] == "CANCELLED"
        assert TabTransferLine.objects.count() == 3
        assert str(Charge.objects.get().tab_id) == source_id
        for id in (source_id, dest_id):
            amount = detail(id)["tab"]["exposure_cents"]
            self.http(self.cashier, f"/tabs/{id}/payments/", {"amount_cents": amount, "method": "EXTERNAL_TERMINAL", "idempotency_key": "settle"}, expected=201)
            self.http(self.cashier, f"/tabs/{id}/close/", {})
        state = detail(dest_id)
        self.http(self.manager, f"/tabs/{dest_id}/operations/", {"kind": "REOPEN", "expected_version": state["tab"]["version"], "reason": "Conferir turno", "idempotency_key": "reopen"})
        assert detail(dest_id)["tab"]["exposure_cents"] == 0
        assert Payment.objects.count() == 2
        assert self.http(self.staff, f"/tabs/{source_id}/")["orders"][0]["id"] == order["id"]
