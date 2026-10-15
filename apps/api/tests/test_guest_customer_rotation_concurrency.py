"""Observe a real cross-Venue lock wait, then verify atomic rotation/revocation."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import check_password
from django.db import close_old_connections, connection

from modules.guest_access import customer_identity as ci
from modules.guest_access.models import CustomerCredential, GuestSession
from modules.guest_access.services import (
    GuestAccessError,
    create_or_get_guest_tab,
    resolve_table_qr,
)
from modules.hospitality.models import Table
from modules.house_account.models import Relationship
from modules.venue.models import Venue


@pytest.mark.django_db(transaction=True)
def test_cross_venue_password_rotation_has_no_deadlock():
    assert connection.vendor == "postgresql"
    visits = []
    for k in ("a", "b"):
        v = Venue.objects.create(name="Reviewer disposable " + k, slug="reviewer-race-" + k)
        t = Table.objects.create(venue=v, label="QA", guest_ordering_mode="DIRECT")
        visits.append((v, resolve_table_qr(public_token=t.public_token)))
    create_or_get_guest_tab(session_token=visits[0][1].token)
    customer, token_a = ci.register_customer(
        guest_token=visits[0][1].token,
        username="reviewer_disposable",
        password="disposable-passphrase-original",
        display_name="Synthetic",
    )
    Relationship.objects.create(venue=visits[1][0], customer=customer, kind="VISITOR")
    _, token_b = ci.login_customer(
        guest_token=visits[1][1].token,
        username="reviewer_disposable",
        password="disposable-passphrase-original",
    )
    a_authorized = Event()
    b_authorizing = Event()
    other_pid = {}
    original = ci._authorized_customer

    def observed(session, auth_token):
        if auth_token == token_a:
            result = original(session, auth_token)
            a_authorized.set()
            assert b_authorizing.wait(10)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                with connection.cursor() as c:
                    c.execute("SELECT pg_stat_clear_snapshot()")
                    c.execute(
                        "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s",
                        [other_pid["pid"]],
                    )
                    row = c.fetchone()
                if row and row[0] == "Lock":
                    break
                time.sleep(0.01)
            else:
                raise AssertionError("Competing authorization never waited on a DB lock")
            return result
        b_authorizing.set()
        return original(session, auth_token)

    def rotate(k):
        close_old_connections()
        try:
            if k == 1:
                with connection.cursor() as c:
                    c.execute("SELECT pg_backend_pid()")
                    other_pid["pid"] = c.fetchone()[0]
                assert a_authorized.wait(10)
            try:
                ci.change_customer_password(
                    guest_token=visits[k][1].token,
                    auth_token=(token_a, token_b)[k],
                    old_password="disposable-passphrase-original",
                    new_password="disposable-new-password-" + str(k),
                )
                return "OK"
            except GuestAccessError as e:
                return (e.code, e.status_code)
        finally:
            close_old_connections()

    with (
        patch.object(ci, "_authorized_customer", observed),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        jobs = [pool.submit(rotate, k) for k in (0, 1)]
        results = [j.result(35) for j in jobs]
    assert results == ["OK", ("CUSTOMER_AUTH_REVOKED", 401)]
    credential = CustomerCredential.objects.get(customer=customer)
    assert credential.version == 2
    assert check_password("disposable-new-password-0", credential.password_hash)
    assert not check_password("disposable-passphrase-original", credential.password_hash)
    assert credential.sessions.count() == 3
    assert credential.sessions.filter(revoked_at__isnull=True, credential_version=2).count() == 1
    assert GuestSession.objects.filter(revoked_at__isnull=True).count() == 2
    for token, visit in zip((token_a, token_b), visits, strict=True):
        with pytest.raises(GuestAccessError) as denied:
            ci.customer_context(guest_token=visit[1].token, auth_token=token)
        assert denied.value.code == "CUSTOMER_AUTH_REVOKED"
