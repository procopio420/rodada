"""Real HTTP/ORM security matrix. No mocked authentication or resolution."""

import hashlib
import hmac
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import override_settings
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.hospitality.models import Table
from modules.ordering.models import Order, Tab
from modules.venue.domains import configure_domain
from modules.venue.hostnames import HostResolutionError, resolve_venue_from_hostname
from modules.venue.models import Venue, VenueDomain

pytestmark = pytest.mark.django_db
HOST_A = "bardoaderlan.rodada.ai"
HOST_B = "barteste.rodada.ai"
SECRET = "isolated-test-host-secret-with-at-least-32-bytes"


@pytest.fixture
def tenants():
    with override_settings(
        ALLOWED_HOSTS=[".rodada.ai", "testserver", "127.0.0.1"], RODADA_BFF_HOST_SECRET=SECRET
    ):
        venues = []
        for i, (slug, host) in enumerate((("bar-do-aderlan", HOST_A), ("bar-teste", HOST_B))):
            venue = Venue.objects.create(slug=slug, name=slug)
            configure_domain(
                venue_id=venue.pk,
                hostname=host,
                is_primary=True,
                is_active=True,
                is_verified=True,
                reason="Security fixture",
            )
            staff = StaffMember.objects.create(
                login_identifier=f"staff-{i}", display_name=f"Staff {i}"
            )
            staff.set_pin("1234")
            staff.save()
            VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="OWNER")
            venues.append(venue)
        yield venues


def login(client, venue, host=HOST_A, platform="WEB"):
    i = 0 if venue.slug == "bar-do-aderlan" else 1
    return client.post(
        "/auth/login/",
        {
            "venue_slug": venue.slug,
            "login_identifier": f"staff-{i}",
            "pin": "1234",
            "installation_id": f"isolated-{platform}-{i}",
            "platform": platform,
        },
        format="json",
        HTTP_HOST=host,
    )


def authenticated(tenants, index=0):
    client = APIClient()
    result = login(client, tenants[index], (HOST_A, HOST_B)[index])
    assert result.status_code == 200, result.data
    client.credentials(HTTP_AUTHORIZATION="Bearer " + result.data["access_token"])
    return client, result.data


def sign(path, host, method="GET", timestamp=None):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    message = f"{timestamp}\n{method}\n{path}\n{host}"
    return {
        "HTTP_X_RODADA_BFF_HOST": host,
        "HTTP_X_RODADA_BFF_TIME": timestamp,
        "HTTP_X_RODADA_BFF_SIGNATURE": hmac.new(
            SECRET.encode(), message.encode(), hashlib.sha256
        ).hexdigest(),
    }


def test_authoritative_alias_preserves_slug(tenants):
    assert resolve_venue_from_hostname(HOST_A.upper()).pk == tenants[0].pk
    assert resolve_venue_from_hostname(HOST_B).pk == tenants[1].pk
    assert tenants[0].slug == "bar-do-aderlan"
    configure_domain(
        venue_id=tenants[0].pk,
        hostname="aderlan.rodada.ai",
        is_active=True,
        is_verified=True,
        reason="Alias",
    )
    assert resolve_venue_from_hostname("aderlan.rodada.ai").pk == tenants[0].pk


@pytest.mark.parametrize(
    "host",
    [
        "unknown.rodada.ai",
        "api.rodada.ai",
        "admin.rodada.ai",
        "bar.rodada.ai",
        "rodada.ai",
        "bardoaderlan.rodada.ai.evil.com",
        "-bar.rodada.ai",
        "bar..rodada.ai",
        "bardoaderlan.rodada.ai/",
        "bardoaderlan.rodada.ai,evil",
        "bardoaderlan.rodada.ai.",
        " bardoaderlan.rodada.ai",
        "bár.rodada.ai",
    ],
)
def test_unknown_reserved_malformed_fail_closed(tenants, host):
    with pytest.raises(HostResolutionError):
        resolve_venue_from_hostname(host)


@pytest.mark.parametrize("active,verified", [(False, True), (True, False), (False, False)])
def test_disabled_unverified(tenants, active, verified):
    configure_domain(
        venue_id=tenants[0].pk,
        hostname=HOST_A,
        is_active=active,
        is_verified=verified,
        reason="Disable",
    )
    with pytest.raises(HostResolutionError):
        resolve_venue_from_hostname(HOST_A)
    assert login(APIClient(), tenants[0]).status_code == 421


def test_registry_constraints_and_audit(tenants):
    with pytest.raises(ValidationError):
        configure_domain(venue_id=tenants[1].pk, hostname=HOST_A, reason="Collision")
    for attributes in (
        {"hostname": HOST_A},
        {"hostname": "UPPER.rodada.ai"},
        {"hostname": "api.rodada.ai"},
        {"hostname": "evil.test"},
        {
            "hostname": "another.rodada.ai",
            "is_primary": True,
            "is_active": True,
            "is_verified": True,
        },
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            VenueDomain.objects.bulk_create([VenueDomain(venue=tenants[0], **attributes)])
    original = VenueDomain.objects.get(hostname=HOST_A)
    original.venue = tenants[1]
    with pytest.raises(ValidationError):
        original.save()
    configure_domain(
        venue_id=tenants[0].pk,
        hostname="new.rodada.ai",
        is_primary=True,
        is_active=True,
        is_verified=True,
        reason="Select canonical",
    )
    assert VenueDomain.objects.filter(venue=tenants[0], is_primary=True).count() == 1
    event = AuditEvent.objects.filter(
        event_type="venue.domain_configured", reason="Select canonical"
    ).get()
    assert event.metadata["before"] and event.metadata["after"]["hostname"] == "new.rodada.ai"


def test_login_cannot_substitute_foreign_venue(tenants):
    assert login(APIClient(), tenants[0]).status_code == 200
    rejected = login(APIClient(), tenants[1])
    assert rejected.status_code == 403 and rejected.data["code"] == "VENUE_HOST_MISMATCH"
    assert not StaffSession.objects.filter(venue=tenants[1]).exists()


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/auth/me/", None),
        ("get", "/tabs/", None),
        ("post", "/tabs/", {}),
        ("post", "/auth/switch-operator/", {"login_identifier": "staff-1", "pin": "1234"}),
        ("post", "/auth/reauthenticate/", {"pin": "1234"}),
        ("get", "/auth/invalidation-events/", None),
        ("get", "/realtime/snapshot/", None),
        ("get", "/realtime/stream/?once=1", None),
    ],
)
def test_foreign_host_rejects_session_before_reads_mutations(tenants, method, path, body):
    client, _ = authenticated(tenants)
    response = getattr(client, method)(path, body, format="json", HTTP_HOST=HOST_B)
    assert response.status_code == 403, response.data
    assert response.data["code"] == "VENUE_HOST_MISMATCH"
    assert not Tab.objects.exists()


def test_refresh_mismatch_does_not_rotate_or_revoke(tenants):
    client, tokens = authenticated(tenants)
    client.credentials()
    rejected = client.post(
        "/auth/refresh/",
        {"refresh_token": tokens["refresh_token"]},
        format="json",
        HTTP_HOST=HOST_B,
    )
    assert rejected.status_code == 403 and rejected.data["code"] == "VENUE_HOST_MISMATCH"
    accepted = client.post(
        "/auth/refresh/",
        {"refresh_token": tokens["refresh_token"]},
        format="json",
        HTTP_HOST=HOST_A,
    )
    assert accepted.status_code == 200


def test_forwarded_and_tenant_header_spoofing(tenants):
    client, _ = authenticated(tenants)
    for header in ("HTTP_X_FORWARDED_HOST", "HTTP_X_RODADA_VENUE", "HTTP_X_RODADA_HOST"):
        response = client.get(
            "/auth/me/?venue=" + str(tenants[1].pk), HTTP_HOST=HOST_A, **{header: HOST_B}
        )
        assert response.status_code == 200
        assert response.data["venue"]["id"] == str(tenants[0].pk)
    invalid = client.get("/auth/me/", HTTP_HOST=HOST_A, HTTP_X_RODADA_BFF_HOST=HOST_B)
    assert invalid.status_code == 403
    malformed = sign("/auth/me/", HOST_A)
    malformed["HTTP_X_RODADA_BFF_SIGNATURE"] = "é" * 64
    assert client.get("/auth/me/", HTTP_HOST="testserver", **malformed).status_code == 403
    valid = client.get("/auth/me/", HTTP_HOST="testserver", **sign("/auth/me/", HOST_A))
    assert valid.status_code == 200
    mismatch = client.get("/auth/me/", HTTP_HOST="testserver", **sign("/auth/me/", HOST_B))
    assert mismatch.status_code == 403 and mismatch.json()["code"] == "VENUE_HOST_MISMATCH"
    for path, assertion in [
        ("/tabs/", sign("/auth/me/", HOST_A)),
        ("/auth/me/", sign("/auth/me/", HOST_A, timestamp=0)),
    ]:
        assert client.get(path, HTTP_HOST="testserver", **assertion).status_code == 403


def test_guessed_foreign_objects_and_offline_idempotency(tenants):
    client, _ = authenticated(tenants)
    tab = Tab.objects.create(venue=tenants[1], display_label="Foreign")
    product = Product.objects.create(
        venue=tenants[1], name="Foreign", price_cents=100, fulfillment_station="BAR"
    )
    table = Table.objects.create(venue=tenants[1], label="Foreign")
    for path in (f"/tabs/{tab.pk}/", f"/catalog/products/{product.pk}/customization/"):
        assert client.get(path, HTTP_HOST=HOST_A).status_code == 404
    for method, path, payload in (
        (
            "post",
            f"/tabs/{tab.pk}/orders/confirm/",
            {
                "idempotency_key": "offline-replay",
                "lines": [{"product_id": str(product.pk), "quantity": 1}],
            },
        ),
        (
            "patch",
            f"/catalog/products/{product.pk}/",
            {"name": "Hacked", "price_cents": 10, "version": 1},
        ),
        ("post", f"/hospitality/tables/{table.pk}/occupy/", {}),
        (
            "post",
            f"/tabs/{tab.pk}/payments/",
            {"amount_cents": 100, "method": "CASH", "idempotency_key": "offline-payment"},
        ),
    ):
        response = getattr(client, method)(path, payload, format="json", HTTP_HOST=HOST_A)
        assert response.status_code == 404, (path, response.data)
    assert not Order.objects.exists()
    product.refresh_from_db()
    assert product.name == "Foreign"
    # Reusing a valid idempotency key with a foreign object cannot recover A's result.
    own = client.post("/tabs/", {}, format="json", HTTP_HOST=HOST_A).data
    own_product = Product.objects.create(
        venue=tenants[0], name="Own", price_cents=100, fulfillment_station="BAR"
    )
    body = {
        "idempotency_key": "same-offline-intent",
        "lines": [{"product_id": str(own_product.pk), "quantity": 1}],
    }
    first = client.post(f"/tabs/{own['id']}/orders/confirm/", body, format="json", HTTP_HOST=HOST_A)
    assert first.status_code == 201, first.data
    assert (
        client.post(
            f"/tabs/{own['id']}/orders/confirm/", body, format="json", HTTP_HOST=HOST_A
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/tabs/{tab.pk}/orders/confirm/", body, format="json", HTTP_HOST=HOST_A
        ).status_code
        == 404
    )
    body["lines"][0]["product_id"] = str(product.pk)
    body["idempotency_key"] = "foreign-product"
    assert (
        client.post(
            f"/tabs/{own['id']}/orders/confirm/", body, format="json", HTTP_HOST=HOST_A
        ).status_code
        == 409
    )
    assert Order.objects.count() == 1


def test_guest_qr_session_replay_and_generation(tenants):
    table = Table.objects.create(venue=tenants[0], label="Guest", guest_ordering_mode="DIRECT")
    client = APIClient()
    before = client.post(
        "/guest/qr/resolve/", {"token": table.public_token}, format="json", HTTP_HOST=HOST_B
    )
    assert before.status_code == 404
    result = client.post(
        "/guest/qr/resolve/", {"token": table.public_token}, format="json", HTTP_HOST=HOST_A
    )
    assert result.status_code == 201
    client.credentials(HTTP_X_GUEST_SESSION=result.data["guest_session_token"])
    for method, path, body in [
        ("get", "/guest/context/", None),
        ("get", "/guest/catalog/", None),
        ("post", "/guest/tabs/", {}),
        ("get", "/guest/realtime/snapshot/", None),
        ("get", "/guest/realtime/stream/?once=1", None),
    ]:
        response = getattr(client, method)(path, body, format="json", HTTP_HOST=HOST_B)
        assert response.status_code == 404, (path, response.data)
    assert not Tab.objects.exists()
    own = client.post("/guest/tabs/", {}, format="json", HTTP_HOST=HOST_A)
    assert own.status_code == 201
    assert Tab.objects.get(pk=own.data["id"]).venue_id == tenants[0].pk
    assert client.get("/guest/context/", HTTP_HOST=HOST_A).status_code == 200
    staff, _ = authenticated(tenants)
    release = staff.post(
        f"/hospitality/tables/{table.pk}/release/", {}, format="json", HTTP_HOST=HOST_A
    )
    assert release.status_code == 200, release.data
    assert client.get("/guest/context/", HTTP_HOST=HOST_A).status_code in (401, 403)


def test_sse_reconnect_rejects_foreign_cursor(tenants):
    client, _ = authenticated(tenants)
    snapshot = client.get("/realtime/snapshot/", HTTP_HOST=HOST_A)
    assert snapshot.status_code == 200
    stream = client.get(
        "/realtime/stream/?once=1", HTTP_HOST=HOST_A, HTTP_LAST_EVENT_ID=snapshot.data["cursor"]
    )
    assert stream.status_code == 200
    assert b"event: ready" in b"".join(stream.streaming_content)
    other, _ = authenticated(tenants, 1)
    foreign = other.get(
        "/realtime/stream/?once=1", HTTP_HOST=HOST_B, HTTP_LAST_EVENT_ID=snapshot.data["cursor"]
    )
    assert foreign.status_code == 200
    assert b"event: reset" in b"".join(foreign.streaming_content)


@pytest.mark.parametrize(
    "host,platform",
    [("127.0.0.1", "WEB"), ("testserver", "ANDROID"), ("rodada-web-demo.up.railway.app", "WEB")],
)
def test_explicit_legacy_and_android_compatibility(tenants, host, platform):
    with override_settings(ALLOWED_HOSTS=[host], RODADA_HOST_COMPATIBILITY_HOSTS=[host]):
        client = APIClient()
        result = login(client, tenants[0], host, platform)
        assert result.status_code == 200
        client.credentials(HTTP_AUTHORIZATION="Bearer " + result.data["access_token"])
        assert client.get("/auth/me/", HTTP_HOST=host).status_code == 200
        client.credentials()
        assert (
            client.post(
                "/auth/refresh/",
                {"refresh_token": result.data["refresh_token"]},
                format="json",
                HTTP_HOST=host,
            ).status_code
            == 200
        )


@pytest.mark.django_db(transaction=True)
def test_postgres_serializes_primary_selection():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL required for real row lock concurrency")
    venue = Venue.objects.create(slug="concurrent", name="Concurrent")

    def provision(host):
        close_old_connections()
        try:
            configure_domain(
                venue_id=venue.pk,
                hostname=host,
                is_primary=True,
                is_active=True,
                is_verified=True,
                reason="Concurrent provisioning",
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(provision, ("first.rodada.ai", "second.rodada.ai")))
    assert VenueDomain.objects.filter(venue=venue, is_primary=True).count() == 1
    assert AuditEvent.objects.filter(venue=venue, event_type="venue.domain_configured").count() == 2


def test_guest_unknown_and_foreign_sessions_are_indistinguishable(tenants):
    table = Table.objects.create(venue=tenants[0], label="Hidden", guest_ordering_mode="DIRECT")
    client = APIClient()
    issued = client.post(
        "/guest/qr/resolve/", {"token": table.public_token}, format="json", HTTP_HOST=HOST_A
    )
    client.credentials(HTTP_X_GUEST_SESSION=issued.data["guest_session_token"])
    foreign = client.get("/guest/context/", HTTP_HOST=HOST_B)
    client.credentials(HTTP_X_GUEST_SESSION="unknown-opaque-token")
    unknown = client.get("/guest/context/", HTTP_HOST=HOST_B)
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.data == unknown.data


@pytest.mark.django_db(transaction=True)
def test_stream_revokes_after_domain_disabled(tenants):
    from asgiref.sync import async_to_sync, sync_to_async

    client, _ = authenticated(tenants)
    cursor = client.get("/realtime/snapshot/", HTTP_HOST=HOST_A).data["cursor"]
    stream = client.get("/realtime/stream/", HTTP_HOST=HOST_A, HTTP_LAST_EVENT_ID=cursor)
    assert stream.status_code == 200

    async def consume():
        content = stream.streaming_content
        assert b"event: ready" in await anext(content)
        await sync_to_async(configure_domain)(
            venue_id=tenants[0].pk,
            hostname=HOST_A,
            is_active=False,
            is_verified=True,
            reason="Revoke open stream",
        )
        for _ in range(3):
            chunk = await anext(content)
            if b"event: revoked" in chunk:
                await content.aclose()
                return
        pytest.fail("Open stream did not revalidate domain")

    async_to_sync(consume)()


def test_postgres_bulk_lifecycle_cannot_reassign_or_skip_audit(tenants):
    if connection.vendor != "postgresql":
        pytest.skip("Production PostgreSQL lifecycle trigger")
    domain = VenueDomain.objects.get(hostname=HOST_A)
    VenueDomain.objects.filter(pk=domain.pk).update(is_primary=False, is_active=False)
    audit = AuditEvent.objects.filter(
        event_type="venue.domain_database_changed",
        entity_id=str(domain.pk),
        metadata__operation="UPDATE",
    ).latest("occurred_at")
    assert audit.metadata["after"]["is_active"] is False
    assert audit.metadata["before"]["is_active"] is True
    from django.db import DatabaseError

    for mutation in (
        lambda: VenueDomain.objects.filter(pk=domain.pk).update(venue=tenants[1]),
        lambda: VenueDomain.objects.filter(pk=domain.pk).update(hostname="hijacked.rodada.ai"),
        lambda: VenueDomain.objects.filter(pk=domain.pk).delete(),
    ):
        with pytest.raises(DatabaseError), transaction.atomic():
            mutation()
    domain.refresh_from_db()
    assert domain.hostname == HOST_A and domain.venue_id == tenants[0].pk


@pytest.mark.django_db(transaction=True)
def test_two_venues_complete_parallel_orders_payments_and_audit(tenants):
    if connection.vendor != "postgresql":
        pytest.skip("Real parallel transactions require PostgreSQL")
    from modules.ledger.models import Payment
    from modules.realtime.models import OutboxEvent

    for venue in tenants:
        Product.objects.create(
            venue=venue, name="Shared display name", price_cents=100, fulfillment_station="BAR"
        )

    def run(index):
        close_old_connections()
        try:
            client, _ = authenticated(tenants, index)
            host = (HOST_A, HOST_B)[index]
            tab = client.post("/tabs/", {}, format="json", HTTP_HOST=host)
            assert tab.status_code == 201, tab.data
            tab_id = tab.data["id"]
            product = Product.objects.get(venue=tenants[index])
            order = client.post(
                f"/tabs/{tab_id}/orders/confirm/",
                {
                    "idempotency_key": "shared-order-intent",
                    "lines": [{"product_id": str(product.pk), "quantity": 1}],
                },
                format="json",
                HTTP_HOST=host,
            )
            assert order.status_code == 201, order.data
            payment = client.post(
                f"/tabs/{tab_id}/payments/",
                {
                    "amount_cents": 100,
                    "method": "EXTERNAL_TERMINAL",
                    "idempotency_key": "shared-payment-intent",
                },
                format="json",
                HTTP_HOST=host,
            )
            assert payment.status_code == 201, payment.data
            closed = client.post(f"/tabs/{tab_id}/close/", {}, format="json", HTTP_HOST=host)
            assert closed.status_code == 200, closed.data
            assert closed.data["state"] == "CLOSED"
            return tab_id
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        tab_ids = list(pool.map(run, (0, 1)))
    assert tab_ids[0] != tab_ids[1]
    for index, venue in enumerate(tenants):
        tab = Tab.objects.get(pk=tab_ids[index])
        assert tab.venue_id == venue.pk
        assert Payment.objects.filter(tab=tab, amount_cents=100).count() == 1
        assert (
            AuditEvent.objects.filter(
                venue=venue, entity_id=str(tab.pk), event_type="tab.closed"
            ).count()
            == 1
        )
        assert not OutboxEvent.objects.filter(venue=tenants[1 - index], tab_id=tab.pk).exists()


def test_foreign_cash_access_refunds_management_and_audit_are_scoped(tenants):
    from modules.access.models import VenueStaffMembership
    from modules.cash.models import CashPoint
    from modules.ledger.models import Payment

    client, _ = authenticated(tenants)
    other, _ = authenticated(tenants, 1)
    assert (
        client.post(
            "/auth/reauthenticate/", {"pin": "1234"}, format="json", HTTP_HOST=HOST_A
        ).status_code
        == 200
    )
    point = CashPoint.objects.create(venue=tenants[1], label="Foreign drawer")
    shift = other.post(
        "/cash/shifts/",
        {
            "cash_point_id": str(point.pk),
            "opening_float_cents": 100,
            "idempotency_key": "foreign-shift",
        },
        format="json",
        HTTP_HOST=HOST_B,
    )
    assert shift.status_code == 201, shift.data
    shift_id = shift.data["id"]
    foreign_tab = Tab.objects.create(venue=tenants[1])
    # Fixture is a confirmed financial fact; HTTP commands must not alter it.
    from django.utils import timezone

    payment = Payment.objects.create(
        tab=foreign_tab,
        amount_cents=100,
        method="EXTERNAL_TERMINAL",
        status="CONFIRMED",
        confirmed_at=timezone.now(),
        idempotency_key="foreign-payment",
        received_by=StaffMember.objects.get(login_identifier="staff-1"),
    )
    membership = VenueStaffMembership.objects.get(venue=tenants[1])
    other_session = StaffSession.objects.get(venue=tenants[1])
    for path in (
        f"/cash/shifts/{shift_id}/",
        f"/cash/points/{point.pk}/active-shift/",
        f"/payments/{payment.pk}/integrated/",
    ):
        assert client.get(path, HTTP_HOST=HOST_A).status_code == 404
    for path, body in (
        (
            f"/cash/shifts/{shift_id}/supply/",
            {"amount_cents": 100, "reason": "Wrong venue", "idempotency_key": "foreign-supply"},
        ),
        (
            f"/payments/{payment.pk}/refunds/",
            {"amount_cents": 100, "idempotency_key": "foreign-refund"},
        ),
        (f"/manage/access/sessions/{other_session.pk}/revoke/", {"reason": "Wrong venue"}),
    ):
        response = client.post(path, body, format="json", HTTP_HOST=HOST_A)
        assert response.status_code == 404, (path, response.data)
    membership_mutation = client.patch(
        f"/manage/access/memberships/{membership.pk}/",
        {"expected_version": 1, "status": "REVOKED"},
        format="json",
        HTTP_HOST=HOST_A,
    )
    assert membership_mutation.status_code == 404
    other_session.refresh_from_db()
    payment.refresh_from_db()
    assert other_session.revoked_at is None
    assert payment.status == "CONFIRMED" and not payment.refunds.exists()
    audit = client.get("/manage/access/audit/", HTTP_HOST=HOST_A)
    assert audit.status_code == 200
    foreign_audits = {
        str(value)
        for value in AuditEvent.objects.filter(venue=tenants[1]).values_list("pk", flat=True)
    }
    assert not foreign_audits.intersection(row["id"] for row in audit.data["results"])
    for route in (
        "/tabs/",
        "/hospitality/tables/",
        "/catalog/products/",
        "/cash/points/",
        "/manage/access/sessions/",
    ):
        result = client.get(route, HTTP_HOST=HOST_A)
        assert result.status_code == 200
        assert not any(
            str(row.get("id")) in {str(point.pk), str(foreign_tab.pk), str(other_session.pk)}
            for row in result.data["results"]
        )
