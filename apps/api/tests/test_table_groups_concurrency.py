"""PostgreSQL locking proof for competing TableGroup creation intents."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from modules.access.context import ActorContext
from modules.access.models import StaffSession
from modules.audit.models import AuditEvent
from modules.hospitality.groups import create_table_group
from modules.hospitality.models import Table, TableGroup, TableGroupMembership
from modules.hospitality.services import HospitalityServiceError
from tests.test_hospitality_tables import HospitalityTableApiTests


@pytest.fixture
def setup_groups(transactional_db):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and independent connections")
    setup = HospitalityTableApiTests()
    setup.setUp()
    actor = ActorContext.from_session(
        StaffSession.objects.filter(staff_member=setup.staff).first()
    )
    tables = [Table.objects.create(venue=setup.venue, label=str(i)) for i in range(3)]
    return actor, tables


def _race(*calls):
    barrier = Barrier(len(calls))
    def execute(call):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return call()
            except HospitalityServiceError as error:
                return error.code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        jobs = [pool.submit(execute, call) for call in calls]
        return [job.result(timeout=30) for job in jobs]


def test_competing_groups_cannot_share_a_table(setup_groups):
    actor, tables = setup_groups
    a, b, c = tables
    results = _race(
        lambda: create_table_group(actor=actor, table_ids=[a.id, b.id],
                                   label="A/B", request_key=uuid.uuid4()),
        lambda: create_table_group(actor=actor, table_ids=[a.id, c.id],
                                   label="A/C", request_key=uuid.uuid4()),
    )
    assert sum(isinstance(x, tuple) for x in results) == 1
    assert "TABLE_ALREADY_GROUPED" in results
    assert TableGroup.objects.count() == 1
    assert TableGroupMembership.objects.filter(table=a, removed_at__isnull=True).count() == 1
    assert AuditEvent.objects.filter(event_type="table_group.created").count() == 1


def test_same_intent_concurrent_replay_has_one_effect(setup_groups):
    actor, tables = setup_groups
    key = uuid.uuid4()
    results = _race(*[
        lambda: create_table_group(actor=actor, table_ids=[tables[0].id, tables[1].id],
                                   label="Mesas", request_key=key)
        for _ in range(2)
    ])
    assert sorted(replayed for _, replayed in results) == [False, True]
    assert TableGroup.objects.count() == 1
    assert TableGroupMembership.objects.count() == 2
    assert AuditEvent.objects.filter(event_type="table_group.created").count() == 1
