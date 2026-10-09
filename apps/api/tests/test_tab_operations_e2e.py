"""Real HTTP full-service split, transfer, merge, payment, close and reopen."""
from django.test import LiveServerTestCase, override_settings

from modules.ledger.models import Charge, Payment
from modules.tab_operations.models import TabTransferLine
from tests.test_house_account_e2e import HouseAccountHttpE2E
from tests.test_tab_operations import OperationFixture


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

    def test_http_move_cancel_and_paid_reopen_leave_occupancies_active(self):
        from modules.hospitality.models import TableOccupancy
        from modules.ordering.models import Tab
        source = self.http(self.staff, "/tabs/", {"display_label": "Mudança"}, expected=201)["id"]
        occupancies = []
        for label in ("A", "B"):
            table = self.http(self.manager, "/hospitality/tables/", {"label": label}, expected=201)
            body = {"tab_id": source} if label == "A" else {}
            occupancies.append(self.http(self.staff, f"/hospitality/tables/{table['id']}/occupy/", body, expected=201))
        def command(tab_id, kind, key, **extra):
            state = self.http(self.cashier, f"/tabs/{tab_id}/operations/")["tab"]
            return {"kind": kind, "expected_version": state["version"], "idempotency_key": key, **extra}
        self.http(self.staff, f"/tabs/{source}/orders/confirm/", {
            "idempotency_key": "consumption", "lines": [{"product_id": str(self.product.id), "quantity": 1}]}, expected=201)
        self.http(self.cashier, f"/tabs/{source}/payments/", {
            "idempotency_key": "paid", "amount_cents": 1000, "method": "EXTERNAL_TERMINAL"}, expected=201)
        moved = self.http(self.staff, f"/tabs/{source}/operations/", command(source, "MOVE_LOCATION", "move", occupancy_id=occupancies[1]["id"]))
        assert moved["source"]["occupancy_id"] == occupancies[1]["id"]
        assert moved["source"]["exposure_cents"] == 0
        self.http(self.cashier, f"/tabs/{source}/close/", {})
        closed_at = Tab.objects.get(pk=source).closed_at
        self.http(self.manager, f"/tabs/{source}/operations/", command(source, "REOPEN", "reopen", reason="Conferir serviço"))
        assert Tab.objects.get(pk=source).closed_at == closed_at
        accidental = self.http(self.staff, "/tabs/", {}, expected=201)["id"]
        cancelled = self.http(self.staff, f"/tabs/{accidental}/operations/", command(accidental, "CANCEL_EMPTY", "cancel"))
        assert cancelled["source"]["state"] == "CANCELLED"
        assert TableOccupancy.objects.filter(released_at__isnull=True).count() == 2
        assert str(Payment.objects.get().tab_id) == str(Charge.objects.get().tab_id) == source
