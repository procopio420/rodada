"""Spec 027 PostgreSQL gates: separate connections, simultaneous domain commands."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.models import AuditEvent
from modules.hospitality.models import TableOccupancy, TabOccupancyAssignment
from modules.hospitality.services import HospitalityServiceError, release_table
from modules.hospitality.table_service import (
    claim_occupancy_responsibility,
    open_tab_in_occupancy,
    start_table_service,
)
from modules.ordering.models import Tab
from tests import test_table_service as fixtures


@pytest.fixture
def setup_service(transactional_db):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections")
    setup = fixtures.TableServiceTests()
    setup.setUp()
    actors = [
        ActorContext.from_session(StaffSession.objects.filter(staff_member=staff).first())
        for staff in (setup.staff, setup.other)
    ]
    return setup, actors


def race(*commands):
    barrier = Barrier(len(commands))

    def execute(command):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return command()
            except HospitalityServiceError as error:
                return error.code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(commands)) as pool:
        futures = [pool.submit(execute, command) for command in commands]
        return [f.result(timeout=20) for f in futures]


def test_start_start(setup_service):
    setup, actors = setup_service
    results = race(
        *(
            lambda actor=actor: start_table_service(
                table_id=setup.table.id, idempotency_key="concurrent", actor=actor
            )
            for actor in actors
        )
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    assert "OCCUPANCY_ALREADY_ACTIVE" in results
    assert TableOccupancy.objects.count() == 1
    assert AuditEvent.objects.filter(event_type="occupancy.responsibility_assigned").count() == 1


def test_same_intent_start_replay(setup_service):
    setup, actors = setup_service
    results = race(
        *(
            lambda: start_table_service(
                table_id=setup.table.id, idempotency_key="same", actor=actors[0]
            )
            for _ in range(2)
        )
    )
    assert {r["replayed"] for r in results} == {True, False}
    assert len({r["active_occupancy"]["id"] for r in results}) == 1


def test_claim_claim(setup_service):
    setup, actors = setup_service
    setup.table.status = "OCCUPIED"
    setup.table.save()
    occupancy = TableOccupancy.objects.create(table=setup.table, generation=1)
    results = race(
        *(
            lambda actor=actor: claim_occupancy_responsibility(
                occupancy_id=occupancy.id,
                expected_responsibility_version=0,
                mode="CLAIM_UNASSIGNED",
                idempotency_key="concurrent",
                actor=actor,
            )
            for actor in actors
        )
    )
    assert sum(isinstance(r, dict) for r in results) == 1
    assert "RESPONSIBILITY_CONFLICT" in results
    occupancy.refresh_from_db()
    assert occupancy.responsibility_version == 1
    assert AuditEvent.objects.filter(event_type="occupancy.responsibility_assigned").count() == 1


def test_release_open(setup_service):
    setup, actors = setup_service
    start_table_service(table_id=setup.table.id, idempotency_key="start", actor=actors[0])
    occupancy = TableOccupancy.objects.get(table=setup.table)
    results = race(
        lambda: release_table(table_id=setup.table.id, actor=actors[0]),
        lambda: open_tab_in_occupancy(
            display_label="Comanda de teste",
            occupancy_id=occupancy.id,
            expected_generation=1,
            idempotency_key="open",
            actor=actors[1],
        ),
    )
    occupancy.refresh_from_db()
    assert occupancy.released_at is not None
    if isinstance(results[1], dict):
        tab = Tab.objects.get(pk=results[1]["tab_id"])
        assignment = TabOccupancyAssignment.objects.get(tab=tab, occupancy=occupancy)
        assert assignment.released_at is not None
    else:
        assert results[1] == "OCCUPANCY_RELEASED"
        assert not Tab.objects.exists()
    assert not TabOccupancyAssignment.objects.filter(released_at__isnull=True).exists()


def test_direct_cleaning_concurrent_completion_changes_generation_once(setup_service):
    from modules.hospitality.services import complete_cleaning
    setup, actors = setup_service
    start_table_service(table_id=setup.table.id, idempotency_key="cleaning-race", actor=actors[0])
    release_table(table_id=setup.table.id, actor=actors[0])
    results = race(*(lambda actor=actor: complete_cleaning(table_id=setup.table.id, actor=actor) for actor in actors))
    assert sum(isinstance(result, TableOccupancy) for result in results) == 1
    assert "INVALID_TABLE_TRANSITION" in results
    setup.table.refresh_from_db()
    assert setup.table.status == "AVAILABLE" and setup.table.access_generation == 2
    occupancy = TableOccupancy.objects.get(table=setup.table)
    assert occupancy.cleaning_started_at is None and occupancy.ready_at is not None
    assert AuditEvent.objects.filter(event_type="table.cleaning_completed").count() == 1
    assert not AuditEvent.objects.filter(event_type="table.cleaning_started").exists()
