"""Real PostgreSQL serialization of a policy update against a confirmed order."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.house_account.models import VenueSpendingLimitPolicy
from modules.house_account.spending import spending_policy, update_spending_policy
from modules.ledger.models import Charge
from modules.ordering.models import Order, Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from tests.test_house_account import HouseFixture


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class SpendingConcurrencyTests(HouseFixture, TransactionTestCase):
    def test_waiting_order_uses_mode_committed_before_its_policy_read(self):
        self.reauth()
        actor = ActorContext.from_session(
            StaffSession.objects.select_related("membership", "staff_member").get(
                staff_member__login_identifier="house-manager"
            )
        )
        tab_id = self.tab()
        for mode in ("WARN_ONLY", "ENFORCE"):
            reached = Event()
            original = spending_policy

            def instrument(venue_id, *, lock=False, reached=reached, original=original):
                if lock:
                    reached.set()
                return original(venue_id, lock=lock)

            def order(mode=mode):
                close_old_connections()
                try:
                    try:
                        value = confirm_order(
                            tab_id=tab_id,
                            source="STAFF",
                            actor=actor,
                            lines=[{"product_id": self.product.id, "quantity": 4}],
                            idempotency_key=mode,
                        )
                        return str(value.id)
                    except OrderingServiceError as error:
                        return error.code
                finally:
                    close_old_connections()

            with (
                ThreadPoolExecutor(max_workers=1) as pool,
                patch("modules.house_account.spending.spending_policy", instrument),
            ):
                with transaction.atomic():
                    policy = VenueSpendingLimitPolicy.objects.select_for_update().get(
                        venue=self.venue
                    )
                    pending = pool.submit(order)
                    assert reached.wait(10), "Order did not reach policy boundary"
                    assert not pending.done()
                    update_spending_policy(
                        actor=actor,
                        mode=mode,
                        expected_version=policy.version,
                        reason="Concurrent mode test",
                        idempotency_key=mode,
                    )
                result = pending.result(timeout=15)
            if mode == "WARN_ONLY":
                assert Order.objects.filter(pk=result).exists()
            else:
                assert result == "SPENDING_LIMIT_EXCEEDED"
        assert Order.objects.filter(tab_id=tab_id).count() == 1
        assert Charge.objects.filter(tab_id=tab_id).count() == 1
        assert self.detail(tab_id)["exposure_cents"] == 4000
        assert Tab.objects.get(pk=tab_id).operating_limit_cents == 3000

    def policy_race(self, same_key):
        from threading import Barrier

        from modules.audit.models import AuditEvent
        from modules.house_account.models import SpendingLimitPolicyCommand

        self.reauth()
        actor = ActorContext.from_session(
            StaffSession.objects.select_related("membership", "staff_member").get(
                staff_member__login_identifier="house-manager"
            )
        )
        barrier = Barrier(2)

        def update(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    return update_spending_policy(
                        actor=actor,
                        mode="WARN_ONLY",
                        expected_version=1,
                        reason="Concurrent write",
                        idempotency_key="same" if same_key else str(index),
                    )
                except OrderingServiceError as error:
                    return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(update, range(2)))
        assert VenueSpendingLimitPolicy.objects.get(venue=self.venue).version == 2
        assert AuditEvent.objects.filter(event_type="spending_limit_policy.updated").count() == 1
        assert SpendingLimitPolicyCommand.objects.count() == 1
        if same_key:
            assert results[0] == results[1] and results[0]["mode"] == "WARN_ONLY"
        else:
            assert sum(value == "POLICY_VERSION_CONFLICT" for value in results) == 1

    def test_concurrent_policy_writes_compare_versions_under_lock(self):
        self.policy_race(same_key=False)

    def test_concurrent_identical_policy_replay_has_one_receipt_and_audit(self):
        self.policy_race(same_key=True)
