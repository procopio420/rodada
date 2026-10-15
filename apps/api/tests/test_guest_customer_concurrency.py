"""PostgreSQL evidence: concurrent guest registration and profile claims."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from modules.audit.models import AuditEvent
from modules.guest_access.customer_identity import (
    claim_customer_tab, login_customer, register_customer,
)
from modules.guest_access.models import CustomerCredential
from modules.guest_access.services import GuestAccessError, create_or_get_guest_tab
from modules.house_account.models import Customer
from tests.test_guest_access import GuestAccessServiceTests


@pytest.fixture
def guest_setup(transactional_db):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL required for row locking tests")
    setup = GuestAccessServiceTests()
    setup.setUp()
    return setup


def race(*commands):
    barrier = Barrier(len(commands))
    def execute(command):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            try:
                return command()
            except GuestAccessError as error:
                return error.code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=len(commands)) as pool:
        tasks = [pool.submit(execute, command) for command in commands]
        return [task.result(timeout=35) for task in tasks]


def test_simultaneous_enroll_never_links_two_customers(guest_setup):
    resolution = guest_setup.resolve()
    tab = create_or_get_guest_tab(session_token=resolution.token)
    result = race(*[
        lambda: register_customer(
            guest_token=resolution.token,
            username="competitor_01", password="passphrase-strong-2026",
            display_name="Ana",
        )
        for _ in range(2)
    ])
    assert sum(isinstance(x, tuple) for x in result) == 1
    assert "TAB_CANNOT_ENROLL" in result
    assert Customer.objects.count() == 1
    assert CustomerCredential.objects.count() == 1
    tab.refresh_from_db()
    assert tab.customer_id == Customer.objects.get().id
    assert AuditEvent.objects.filter(event_type="guest_customer.registered").count() == 1


def test_same_customer_competing_devices_preserve_single_tab(guest_setup):
    first = guest_setup.resolve()
    tab = create_or_get_guest_tab(session_token=first.token)
    customer, _ = register_customer(
        guest_token=first.token, username="competing_01",
        password="passphrase-strong-2026", display_name="Ana",
    )
    second = guest_setup.resolve()
    third = guest_setup.resolve()
    _, second_token = login_customer(
        guest_token=second.token, username="competing_01",
        password="passphrase-strong-2026",
    )
    _, third_token = login_customer(
        guest_token=third.token, username="competing_01",
        password="passphrase-strong-2026",
    )
    result = race(
        lambda: claim_customer_tab(
            guest_token=second.token, auth_token=second_token,
            target_tab_id=tab.id,
        ),
        lambda: claim_customer_tab(
            guest_token=third.token, auth_token=third_token,
            target_tab_id=tab.id,
        ),
    )
    assert all(x.id == tab.id for x in result)
    assert AuditEvent.objects.filter(event_type="guest_customer.tab_claimed").count() == 2
    assert Customer.objects.count() == 1
    tab.refresh_from_db()
    assert tab.customer_id == customer.id
