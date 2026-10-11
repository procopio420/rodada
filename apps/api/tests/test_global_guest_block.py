"""013-005 global switch is canonical, immediate and separate from table mode."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase

from modules.audit.models import AuditEvent
from modules.guest_access.models import GuestSession
from modules.guest_access.services import (GuestAccessError, confirm_guest_order,
    create_or_get_guest_tab, guest_catalog, guest_session_context, resolve_table_qr)
from modules.hospitality.models import Table
from modules.hospitality.party_size import record_party_size
from modules.dispatch.services import create_service_request
from modules.ordering.models import OrderItem
from modules.venue.guest_policy import set_global_guest_block
from modules.venue.stations import StationChangeError
from tests.test_station_configuration import StationFixtures


class GuestBlockFixtures(StationFixtures):
    def setup_guest(self):
        self.setup_station()
        self.table = Table.objects.create(venue=self.venue, label="QR", guest_ordering_mode="DIRECT")
        self.resolution = resolve_table_qr(public_token=self.table.public_token)
        self.guest_tab = create_or_get_guest_tab(session_token=self.resolution.token)

    def block(self, blocked=True, version=1):
        return set_global_guest_block(actor=self.actor, blocked=blocked,
                                      expected_version=version, reason="Emergency")

    def guest_order(self):
        return confirm_guest_order(session_token=self.resolution.token,
            lines=[{"product_id": self.product.id, "quantity": 1}], idempotency_key="global-guest-order")


class GlobalGuestBlockTests(GuestBlockFixtures, TestCase):
    def setUp(self):
        self.setup_guest()

    def test_every_operational_guest_mutation_blocked_staff_ordering_unchanged(self):
        before = self.guest_order()
        original = list(before.items.values("id", "quantity", "unit_price_cents", "fulfillment_station_snapshot"))
        self.block()
        commands = [
            lambda: resolve_table_qr(public_token=self.table.public_token),
            lambda: create_or_get_guest_tab(session_token=self.resolution.token),
            self.guest_order,
            lambda: create_service_request(session_token=self.resolution.token, request_id=uuid.uuid4(), task_type="SERVICE_REQUEST"),
            lambda: create_service_request(session_token=self.resolution.token, request_id=uuid.uuid4(), task_type="BILL_REQUEST"),
            lambda: record_party_size(session_token=self.resolution.token, covers_count=2, expected_version=0, idempotency_key="covers-global"),
        ]
        for command in commands:
            with self.assertRaises(GuestAccessError) as error:
                command()
            assert error.exception.code == "VENUE_GUEST_MUTATIONS_BLOCKED"
        assert list(before.items.values("id", "quantity", "unit_price_cents", "fulfillment_station_snapshot")) == original
        assert self.order().id
        assert OrderItem.objects.count() == 2
        assert GuestSession.objects.count() == 1

    def test_read_context_and_catalog_remain_canonical_when_blocked(self):
        self.block()
        session = guest_session_context(session_token=self.resolution.token)
        assert session._guest_policy == {"emergency_blocked": True, "policy_version": 2}
        assert guest_catalog(session_token=self.resolution.token).filter(pk=self.product.pk).exists()
        response = self.client.get("/guest/context/", HTTP_X_GUEST_SESSION=self.resolution.token)
        assert response.status_code == 200
        assert response.json()["guest_policy"]["emergency_blocked"]

    def test_http_bypass_rejected_and_unblock_restores_original_session(self):
        self.block()
        response = self.client.post("/guest/orders/confirm/", {
            "idempotency_key": "bypass", "lines": [{"product_id": str(self.product.id), "quantity": 1}]},
            format="json", HTTP_X_GUEST_SESSION=self.resolution.token)
        assert response.status_code == 403
        self.block(False, 2)
        assert self.guest_order().tab_id == self.guest_tab.id

    def test_policy_conflict_cross_venue_and_audit(self):
        self.block()
        with self.assertRaises(StationChangeError) as error:
            self.block(False)
        assert error.exception.details["current"]["blocked"]
        self.other.refresh_from_db()
        assert not self.other.guest_mutations_blocked
        event = AuditEvent.objects.get(event_type="venue.guest_policy_changed")
        assert event.actor_session_id == self.session.id
        assert event.metadata["before"]["blocked"] is False
        assert event.metadata["after"]["blocked"] is True
        assert self.resolution.token not in str(event.metadata)

    def test_policy_api_rejects_unknown_fields_and_staff_authority(self):
        response = self.client.patch("/management/guest-policy/", {
            "blocked": True, "expected_version": 1, "venue_id": str(self.other.id)}, format="json")
        assert response.status_code == 400
        response = self.client.patch("/management/guest-policy/", {
            "blocked": True, "expected_version": 1}, format="json")
        assert response.status_code == 200
        assert response.json()["version"] == 2


class GlobalGuestConcurrencyTests(GuestBlockFixtures, TransactionTestCase):
    def run_race(self, commands):
        assert connection.vendor == "postgresql", "PostgreSQL required for serialization evidence"
        barrier = Barrier(2)
        def run(command):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    command()
                    return "OK"
                except StationChangeError as exc:
                    return exc.code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, commands))

    def setUp(self):
        self.setup_guest()

    def test_parallel_managers_cannot_lose_block_version(self):
        assert sorted(self.run_race([self.block, self.block])) == ["OK", "STALE_VERSION"]
        assert AuditEvent.objects.filter(event_type="venue.guest_policy_changed").count() == 1

    def test_order_vs_block_uses_canonical_serialization(self):
        # This race accepts a committed pre-block order or rejects a post-block
        # order; once block returns all subsequent guest mutations are denied.
        from modules.guest_access.services import GuestAccessError
        def attempt_order():
            try:
                self.guest_order()
            except GuestAccessError as error:
                raise StationChangeError(error.code, error.message, error.status_code) from error
        result = self.run_race([attempt_order, self.block])
        assert result in (["OK", "OK"], ["VENUE_GUEST_MUTATIONS_BLOCKED", "OK"])
        with self.assertRaises(GuestAccessError):
            self.guest_order()
        self.venue.refresh_from_db()
        assert self.venue.guest_mutations_blocked
