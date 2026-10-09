"""Release gates use independent PostgreSQL connections, no simulated locking."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.cash.models import CashPoint
from modules.cash.services import open_cash_shift, start_cash_count, close_cash_shift
from modules.corrections.models import OrderCorrection
from modules.corrections.services import cancel_before_fulfillment, CorrectionServiceError
from modules.ledger.models import LedgerAdjustment, Payment
from modules.ledger.services import collect_payment, reverse_open_responsibility, LedgerServiceError
from modules.ordering.models import OrderItem
from tests.test_house_account import HouseFixture


@skipUnless(connection.vendor == "postgresql", "Real PostgreSQL locking required")
class NativeConcurrency(HouseFixture, TransactionTestCase):
    def parallel(self, commands):
        barrier = Barrier(2)
        def worker(command):
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return command()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, commands))

    def actor(self):
        return ActorContext.from_session(StaffSession.objects.get(staff_member__login_identifier="house-cashier"))

    def test_two_terminal_cancellations_append_only_one_reversal(self):
        tab = self.tab()
        self.order(tab)
        item = OrderItem.objects.get(order__tab_id=tab)
        actor = self.actor()
        def cancel(key):
            try:
                cancel_before_fulfillment(item_id=item.id, kind="CANCEL_ITEM", reason_code="WRONG_ENTRY",
                    reason_text="", idempotency_key=key, actor=actor,
                    financial_reversal_hook=reverse_open_responsibility)
                return "OK"
            except CorrectionServiceError as error:
                return error.code
        result = self.parallel([lambda: cancel("cancel-a"), lambda: cancel("cancel-b")])
        self.assertEqual(sorted(result), ["ITEM_ALREADY_CORRECTED", "OK"])
        self.assertEqual(OrderCorrection.objects.count(), 1)
        self.assertEqual(LedgerAdjustment.objects.filter(order_item=item).count(), 1)

    def test_cash_payment_racing_count_close_is_included_or_rejected(self):
        tab = self.tab()
        self.order(tab)
        actor = self.actor()
        point = CashPoint.objects.create(venue=self.venue, label="Race drawer")
        shift = open_cash_shift(cash_point_id=point.id, opening_float_cents=20000,
            business_date=timezone.localdate(), idempotency_key="open", actor=actor)
        def pay():
            try:
                collect_payment(tab_id=tab, amount_cents=1000, method="CASH", idempotency_key="race-cash",
                    actor=actor, cash_point_id=point.id, amount_tendered_cents=1000)
                return "PAID"
            except LedgerServiceError as error:
                return error.code
        def close():
            start_cash_count(shift_id=shift.id, actor=actor)
            close_cash_shift(shift_id=shift.id, counted_amount_cents=20000,
                review_threshold_cents=0, actor=actor)
            return "CLOSED"
        result = self.parallel([pay, close])
        shift.refresh_from_db()
        confirmed = Payment.objects.filter(tab_id=tab, status="CONFIRMED").count()
        self.assertEqual(shift.expected_amount_cents_snapshot, 20000 + 1000 * confirmed)
        self.assertEqual(shift.movements.filter(kind="CASH_PAYMENT").count(), confirmed)
        self.assertEqual(confirmed, int("PAID" in result))

    def test_staff_cannot_withdraw_by_direct_http_request(self):
        actor = self.actor()
        point = CashPoint.objects.create(venue=self.venue, label="Protected drawer")
        shift = open_cash_shift(cash_point_id=point.id, opening_float_cents=20000,
            business_date=timezone.localdate(), idempotency_key="open-protected", actor=actor)
        response = self.staff.post(f"/cash/shifts/{shift.id}/withdrawal/",
            {"amount_cents": 1000, "reason": "Forbidden", "idempotency_key": "unauthorized"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "CAPABILITY_REQUIRED")
        self.assertEqual(shift.movements.count(), 1)
