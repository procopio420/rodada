from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.models import AuditEvent
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Tab, Order
from modules.tab_operations.models import ServicePoint, TabOperation, TabTransferLine
from modules.tab_operations.services import execute, OperationError, transfer_effect
from tests.test_house_account import HouseFixture


class OperationFixture(HouseFixture):
    def command(self, source, destination=None, **extra):
        data = {"kind": "SPLIT", "expected_version": self.detail(source)["version"], "idempotency_key": "split"}
        if destination:
            data.update(destination_tab_id=destination, destination_version=self.detail(destination)["version"])
        data.update(extra)
        return data

    def operations(self, tab):
        response = self.cashier.get(f"/tabs/{tab}/operations/")
        assert response.status_code == 200, response.json()
        return response.json()

    def commit(self, tab, data, status=200, client=None):
        return self.post(client or self.cashier, f"/tabs/{tab}/operations/", data, status=status)

    def line(self, tab, **extra):
        return {"charge_id": self.operations(tab)["lines"][0]["charge_id"], **extra}


class TabOperationTests(OperationFixture, TestCase):
    def test_split_balanced_history_retry_and_retransfer(self):
        source, dest = self.tab(), self.tab()
        self.order(source, 3)
        command = self.command(source, dest, lines=[self.line(source, quantity=2)])
        preview = self.post(self.cashier, f"/tabs/{source}/operations/preview/", command)
        assert preview["amount_cents"] == 2000 and TabTransferLine.objects.count() == 0
        result = self.commit(source, command)
        assert result == self.commit(source, command)
        assert TabTransferLine.objects.count() == 1
        assert self.detail(source)["exposure_cents"] == 1000
        assert self.detail(dest)["exposure_cents"] == 2000
        assert sum(transfer_effect(tab) for tab in Tab.objects.all()) == 0
        assert str(Order.objects.get().tab_id) == str(Charge.objects.get().tab_id) == source
        third = self.tab()
        self.commit(dest, self.command(dest, third, lines=[self.line(dest, amount_cents=500)]))
        assert self.detail(dest)["exposure_cents"] == 1500
        assert self.detail(third)["exposure_cents"] == 500
        assert self.commit(source, {**command, "reason": "changed"}, 409)["code"] == "IDEMPOTENCY_CONFLICT"

    def test_new_destination_retry_never_duplicates(self):
        source = self.tab()
        self.order(source)
        command = self.command(source, destination_label="Separada", lines=[self.line(source, quantity=1)])
        result = self.commit(source, command)
        assert result == self.commit(source, command)
        assert Tab.objects.count() == 2

    def test_overdraw_version_permission_and_limit_reject_atomically(self):
        source, dest = self.tab(), self.tab()
        self.order(source, 2)
        command = self.command(source, dest, lines=[self.line(source, amount_cents=2001)])
        assert self.commit(source, command, 409)["code"] == "INSUFFICIENT_TRANSFERABLE_BALANCE"
        command["lines"][0]["amount_cents"] = 2000
        assert self.commit(source, command, 403, self.staff)["code"] == "CAPABILITY_REQUIRED"
        command["expected_version"] = 999
        assert self.commit(source, command, 409)["code"] == "VERSION_CONFLICT"
        command["expected_version"] = self.detail(source)["version"]
        self.order(dest, 2)
        command["destination_version"] = self.detail(dest)["version"]
        assert self.commit(source, command, 409)["code"] == "SPENDING_LIMIT_EXCEEDED"
        assert TabOperation.objects.count() == 0

    def test_all_active_payments_block_both_sides(self):
        source, dest = self.tab(), self.tab()
        self.order(source)
        command = self.command(source, dest, lines=[self.line(source, quantity=1)])
        payment = self.payment(source, 100)
        original = Payment.objects.get(pk=payment["id"])
        for tab_id in (source, dest):
            for status in ("CREATED", "PENDING", "PROCESSING", "AUTHORIZED", "CONFIRMATION_PENDING", "CONFIRMED", "REFUNDED"):
                original.tab_id, original.status = tab_id, status
                original.save()
                assert self.commit(source, command, 409)["code"] in ("CONFIRMED_PAYMENT", "PAYMENT_IN_FLIGHT")
        assert TabTransferLine.objects.count() == 0
        original.tab_id, original.status = source, "FAILED"
        original.save()
        assert self.commit(source, command, 409)["code"] == "VERSION_CONFLICT"
        command["expected_version"] = self.detail(source)["version"]
        self.commit(source, command)

    def test_limit_and_orders_use_transferred_balance(self):
        source, dest = self.tab(), self.tab()
        self.order(source, 2)
        self.order(dest, 2)
        self.commit(source, self.command(source, dest, lines=[self.line(source, quantity=1)]))
        assert self.detail(dest)["consumption_blocked"]
        self.order(dest, key="more", status=409)

    def test_merge_preserves_source_and_revokes_guest(self):
        from datetime import timedelta
        from django.utils import timezone
        from modules.hospitality.models import Table, TableOccupancy
        from modules.guest_access.models import GuestSession
        source, dest = self.tab(), self.tab()
        self.order(source)
        table = Table.objects.create(venue=self.venue, label="1", status="OCCUPIED")
        occ = TableOccupancy.objects.create(table=table, generation=1)
        guest = GuestSession.objects.create(table=table, occupancy=occ, tab_id=source, generation=1,
            token_digest="x" * 64, expires_at=timezone.now() + timedelta(hours=1))
        result = self.commit(source, self.command(source, dest, kind="MERGE"))
        assert result["source"]["state"] == "CANCELLED" and result["source"]["merged_into_id"] == dest
        guest.refresh_from_db()
        assert str(guest.tab_id) == source and guest.revoked_at
        occ.refresh_from_db()
        assert occ.released_at is None

    def test_location_refreshes_dispatch_and_preserves_balance(self):
        from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
        from modules.dispatch.models import DispatchTask
        source = self.tab()
        order = self.order(source)
        table = Table.objects.create(venue=self.venue, label="A", status="OCCUPIED")
        occupancy = TableOccupancy.objects.create(table=table, generation=1)
        TabOccupancyAssignment.objects.create(tab_id=source, occupancy=occupancy)
        task = DispatchTask.objects.create(venue=self.venue, task_type="DELIVERY", order_item_id=order["items"][0]["id"], destination_label="Mesa A")
        point = ServicePoint.objects.create(venue=self.venue, label="Balcão")
        command = self.command(source, kind="MOVE_LOCATION", service_point_id=str(point.id))
        result = self.commit(source, command, client=self.staff)
        task.refresh_from_db()
        occupancy.refresh_from_db()
        assert task.destination_label == "Balcão" and occupancy.released_at is None
        assert self.detail(source)["exposure_cents"] == 1000
        assert result == self.commit(source, command, client=self.staff)

    def test_cancel_reopen_preserve_closure_and_payment(self):
        empty = self.tab()
        self.commit(empty, self.command(empty, kind="CANCEL_EMPTY"), client=self.staff)
        source = self.tab()
        self.order(source)
        assert self.commit(source, self.command(source, kind="CANCEL_EMPTY"), 409)["code"] == "TAB_NOT_EMPTY"
        payment = self.payment(source)
        self.post(self.cashier, f"/tabs/{source}/close/")
        closed = Tab.objects.get(pk=source).closed_at
        command = self.command(source, kind="REOPEN", reason="Corrigir visita")
        self.commit(source, command, 403)
        self.commit(source, command, client=self.manager)
        assert Tab.objects.get(pk=source).closed_at == closed
        assert str(Payment.objects.get(pk=payment["id"]).tab_id) == source
        assert AuditEvent.objects.filter(event_type="tab.post_close_exception").exists()


@skipUnless(connection.vendor == "postgresql", "Real row locking requires PostgreSQL")
class TabOperationConcurrency(OperationFixture, TransactionTestCase):
    def test_two_concurrent_splits_cannot_overdraw(self):
        source, dest = self.tab(), self.tab()
        self.order(source)
        command = self.command(source, dest, lines=[self.line(source, quantity=1)])
        actor = ActorContext.from_session(StaffSession.objects.get(staff_member__login_identifier="house-cashier"))
        barrier = Barrier(2)
        def worker(key):
            close_old_connections()
            barrier.wait(timeout=10)
            try:
                execute(tab_id=source, data={**command, "idempotency_key": key}, actor=actor)
                return "OK"
            except OperationError as error:
                return error.code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, ("a", "b")))
        assert sorted(results) == ["OK", "VERSION_CONFLICT"]
        assert TabTransferLine.objects.count() == 1

class TabOperationEdgeTests(OperationFixture, TestCase):
    def test_active_attempt_blocks_even_if_payment_status_is_terminal(self):
        from modules.payment_provider.models import PaymentAttempt
        source, dest = self.tab(), self.tab()
        self.order(source)
        payment = self.payment(source, 100)
        Payment.objects.filter(pk=payment["id"]).update(status="FAILED")
        PaymentAttempt.objects.create(payment_id=payment["id"], provider="test", idempotency_key="attempt", status="CONFIRMATION_PENDING")
        assert self.commit(source, self.command(source, dest, lines=[self.line(source, quantity=1)]), 409)["code"] == "PAYMENT_IN_FLIGHT"

    def test_refund_blocks_and_cross_venue_rejects(self):
        from modules.ledger.models import Refund
        from modules.venue.models import Venue
        source, dest = self.tab(), self.tab()
        self.order(source)
        payment = self.payment(source, 100)
        actor = StaffSession.objects.get(staff_member__login_identifier="house-manager")
        Refund.objects.create(payment_id=payment["id"], amount_cents=100, idempotency_key="refund", created_by_id=actor.staff_member_id)
        Payment.objects.filter(pk=payment["id"]).update(status="FAILED")
        assert self.commit(source, self.command(source, dest, lines=[self.line(source, quantity=1)]), 409)["code"] == "CONFIRMED_PAYMENT"
        other = Tab.objects.create(venue=Venue.objects.create(name="Other", slug="other"))
        body = self.command(source, lines=[self.line(source, quantity=1)], destination_tab_id=str(other.id), destination_version=1)
        assert self.commit(source, body, 404)["code"] == "TAB_NOT_FOUND"

    def test_transferred_charge_cannot_be_reversed_by_legacy_correction(self):
        source, dest = self.tab(), self.tab()
        order = self.order(source)
        self.commit(source, self.command(source, dest, lines=[self.line(source, quantity=1)]))
        response = self.staff.post(f"/order-items/{order['items'][0]['id']}/corrections/cancel/",
            {"kind": "CANCEL_ITEM", "reason_code": "WRONG_ITEM", "idempotency_key": "correction"}, format="json")
        assert response.status_code == 409, response.json()
        assert response.json()["code"] == "TRANSFERRED_RESPONSIBILITY"
        assert self.detail(source)["exposure_cents"] == 0 and self.detail(dest)["exposure_cents"] == 1000

    def test_completed_dispatch_preserves_destination_history_and_invalid_occupancy(self):
        from modules.dispatch.models import DispatchTask
        from modules.hospitality.models import Table, TableOccupancy
        source = self.tab()
        order = self.order(source)
        task = DispatchTask.objects.create(venue=self.venue, task_type="DELIVERY", order_item_id=order["items"][0]["id"], destination_label="Mesa anterior", state="DONE")
        point = ServicePoint.objects.create(venue=self.venue, label="Balcão")
        self.commit(source, self.command(source, kind="MOVE_LOCATION", service_point_id=str(point.id)), client=self.staff)
        task.refresh_from_db()
        assert task.destination_label == "Mesa anterior"
        table = Table.objects.create(venue=self.venue, label="B", status="OCCUPIED")
        occ = TableOccupancy.objects.create(table=table, generation=1)
        self.commit(source, self.command(source, kind="MOVE_LOCATION", occupancy_id=str(occ.id), idempotency_key="table"), client=self.staff)
        assert self.operations(source)["tab"]["occupancy_id"] == str(occ.id)
        assert self.operations(source)["tab"]["service_point_id"] is None
