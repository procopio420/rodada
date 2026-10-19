"""Spec 009 / 026: location commands preserve finance and occupancy history."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from modules.access.context import ActorContext
from modules.access.models import StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from modules.hospitality.services import release_table
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Order, Tab
from modules.tab_operations.models import TabOperation, TabTransferLine
from modules.tab_operations.services import OperationError, execute
from modules.venue.models import Venue

from tests.test_tab_operations import OperationFixture


class LocationFixture(OperationFixture):
    def location(self, label, generation=1):
        table = Table.objects.create(venue=self.venue, label=label, status="OCCUPIED")
        occupancy = TableOccupancy.objects.create(table=table, generation=generation)
        return table, occupancy

    def events(self):
        return AuditEvent.objects.filter(event_type="tab.location_changed")

    def actor(self):
        return ActorContext.from_session(
            StaffSession.objects.get(staff_member__login_identifier="house-cashier")
        )


class TabLocationSafetyTests(LocationFixture, TestCase):
    def test_stale_generation_rejects_without_side_effects(self):
        source = self.tab()
        self.order(source)
        self.payment(source, 100)
        _, origin = self.location("A")
        TabOccupancyAssignment.objects.create(tab_id=source, occupancy=origin)
        _, destination = self.location("B", generation=2)
        before = self.detail(source)
        body = self.command(source, kind="MOVE_LOCATION", occupancy_id=str(destination.id))
        result = self.commit(source, body, 409, self.staff)
        assert result["code"] == "OCCUPANCY_NOT_ACTIVE"
        assert self.detail(source) == before
        assert TabOccupancyAssignment.objects.filter(tab_id=source).count() == 1
        assert TabOccupancyAssignment.objects.get(tab_id=source).released_at is None
        assert TabOperation.objects.count() == self.events().count() == 0

    def test_unavailable_foreign_or_unauthorized_destination_has_no_effect(self):
        source = self.tab()
        _, origin = self.location("A")
        TabOccupancyAssignment.objects.create(tab_id=source, occupancy=origin)
        table, destination = self.location("B")
        body = self.command(source, kind="MOVE_LOCATION", occupancy_id=str(destination.id))
        before = self.detail(source)
        table.status = "DIRTY"
        table.save(update_fields=["status"])
        assert self.commit(source, body, 409)["code"] == "OCCUPANCY_NOT_ACTIVE"
        table.status = "OCCUPIED"
        table.venue = Venue.objects.create(name="Other location", slug="other-location")
        table.save(update_fields=["status", "venue"])
        assert self.commit(source, body, 409)["code"] == "OCCUPANCY_NOT_ACTIVE"
        table.venue = self.venue
        table.save(update_fields=["venue"])
        release_table(
            table_id=table.id,
            actor=self.actor(),
            expected_occupancy_id=destination.id,
            expected_generation=destination.generation,
        )
        assert self.commit(source, body, 409)["code"] == "OCCUPANCY_NOT_ACTIVE"
        VenueStaffMembership.objects.filter(staff_member__login_identifier="house-cashier").update(
            capability_overrides={"deny": ["tab.move"]}
        )
        assert self.commit(source, body, 403)["code"] == "CAPABILITY_REQUIRED"
        assert self.detail(source) == before
        assert TabOperation.objects.count() == self.events().count() == 0
        assert TabOccupancyAssignment.objects.get(tab_id=source).released_at is None

    def test_paid_and_unpaid_move_preserve_snapshots_and_reason(self):
        for amount in (0, 100):
            with self.subTest(payment_cents=amount):
                source = self.tab()
                self.order(source)
                if amount:
                    self.payment(source, amount)
                _, origin = self.location(f"A-{amount}")
                _, destination = self.location(f"B-{amount}")
                original_assignment = TabOccupancyAssignment.objects.create(
                    tab_id=source, occupancy=origin
                )
                snapshots = (list(Order.objects.values()), list(Charge.objects.values()),
                             list(Payment.objects.values()))
                exposure = self.detail(source)["exposure_cents"]
                body = self.command(source, kind="MOVE_LOCATION",
                                    occupancy_id=str(destination.id), reason="  Mudança de lugar  ")
                result = self.commit(source, body, client=self.staff)
                assert result == self.commit(source, body, client=self.staff)
                assert snapshots == (list(Order.objects.values()), list(Charge.objects.values()),
                                     list(Payment.objects.values()))
                assert self.detail(source)["exposure_cents"] == exposure
                original_assignment.refresh_from_db()
                origin.refresh_from_db()
                assert original_assignment.released_at is not None
                assert origin.released_at is None
                event = self.events().get(entity_id=source)
                assert event.reason == "Mudança de lugar"
                assert event.metadata["before"]["occupancy_id"] == str(origin.id)
                assert event.metadata["occupancy_id"] == str(destination.id)
                assert event.actor_staff_id and event.actor_session_id and event.occurred_at
                assert TabTransferLine.objects.count() == 0

    def test_replay_after_release_does_not_restore_assignment_and_reauthorizes(self):
        source = self.tab()
        table, destination = self.location("B")
        body = self.command(source, kind="MOVE_LOCATION", occupancy_id=str(destination.id))
        original = self.commit(source, body)
        release_table(
            table_id=table.id,
            actor=self.actor(),
            expected_occupancy_id=destination.id,
            expected_generation=destination.generation,
        )
        assert self.commit(source, body) == original
        assert not TabOccupancyAssignment.objects.filter(
            tab_id=source, released_at__isnull=True
        ).exists()
        VenueStaffMembership.objects.filter(staff_member__login_identifier="house-cashier").update(
            capability_overrides={"deny": ["tab.move"]}
        )
        assert self.commit(source, body, 403)["code"] == "CAPABILITY_REQUIRED"
        assert TabOperation.objects.count() == self.events().count() == 1


@skipUnless(connection.vendor == "postgresql", "Real locks require PostgreSQL")
class TabLocationSafetyConcurrency(LocationFixture, TransactionTestCase):
    def race(self, workers):
        barrier = Barrier(2)

        def run(worker):
            close_old_connections()
            barrier.wait(timeout=10)
            try:
                return worker()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, workers))

    def test_identical_move_commits_once(self):
        source = self.tab()
        self.order(source)
        self.payment(source, 100)
        _, destination = self.location("B")
        body = self.command(source, kind="MOVE_LOCATION", occupancy_id=str(destination.id))
        actor = self.actor()

        def move():
            return execute(tab_id=source, data=body, actor=actor)

        results = self.race((move, move))
        assert results[0] == results[1]
        assert TabOperation.objects.count() == self.events().count() == 1
        assert TabOccupancyAssignment.objects.filter(tab_id=source).count() == 1
        assert self.detail(source)["exposure_cents"] == 900
        assert Payment.objects.count() == 1
        assert TabTransferLine.objects.count() == 0

    def test_move_and_release_serialize_on_destination(self):
        source = self.tab()
        _, origin = self.location("A")
        TabOccupancyAssignment.objects.create(tab_id=source, occupancy=origin)
        table, destination = self.location("B")
        body = self.command(source, kind="MOVE_LOCATION", occupancy_id=str(destination.id))
        actor = self.actor()

        def move():
            try:
                execute(tab_id=source, data=body, actor=actor)
                return "MOVED"
            except OperationError as error:
                return error.code

        def release():
            release_table(
                table_id=table.id,
                actor=actor,
                expected_occupancy_id=destination.id,
                expected_generation=destination.generation,
            )
            return "RELEASED"

        result = self.race((move, release))
        assert result in (["MOVED", "RELEASED"], ["OCCUPANCY_NOT_ACTIVE", "RELEASED"])
        destination.refresh_from_db()
        origin.refresh_from_db()
        assert destination.released_at is not None and origin.released_at is None
        assert not TabOccupancyAssignment.objects.filter(
            occupancy=destination, released_at__isnull=True
        ).exists()
        assert TabOperation.objects.count() == self.events().count() == (result[0] == "MOVED")
        assert Tab.objects.get(pk=source).version == body["expected_version"] + (
            result[0] == "MOVED"
        )
