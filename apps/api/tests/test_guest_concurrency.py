"""Real PostgreSQL guest replay: independent connections, same immutable intent."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from modules.audit.models import AuditEvent
from modules.guest_access.services import confirm_guest_order, create_or_get_guest_tab
from modules.hospitality.models import TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Tab
from tests import test_guest_access as fixtures


@pytest.fixture
def guest(transactional_db):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL locks and independent connections")
    setup = fixtures.GuestAccessServiceTests()
    setup.setUp()
    return setup, setup.resolve().token


def race(command):
    barrier = Barrier(2)

    def execute():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return command()
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute) for _ in range(2)]
        return [future.result(timeout=20) for future in futures]


def test_concurrent_guest_tab_creation_has_one_visit_and_one_tab(guest):
    _, token = guest
    ids = race(lambda: create_or_get_guest_tab(session_token=token).pk)
    assert ids[0] == ids[1]
    assert TableOccupancy.objects.count() == Tab.objects.count() == TabOccupancyAssignment.objects.count() == 1
    assert AuditEvent.objects.filter(event_type="guest_tab.created").count() == 1


def test_concurrent_guest_order_replay_has_one_order_charge_and_no_payment(guest):
    setup, token = guest
    tab = create_or_get_guest_tab(session_token=token)
    ids = race(lambda: confirm_guest_order(session_token=token, lines=[{"product_id": setup.product.pk, "quantity": 2}], idempotency_key="guest-parallel").pk)
    assert ids[0] == ids[1]
    assert tab.orders.count() == tab.charges.count() == 1
    assert tab.charges.get().amount_cents == 2800
    assert tab.payments.count() == 0
    assert AuditEvent.objects.filter(event_type="guest_order.confirmed").count() == 1
