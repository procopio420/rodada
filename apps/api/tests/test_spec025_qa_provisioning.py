"""Safe, auditable Spec025 QA provisioning: no pilot mutation or implicit rollout."""

import asyncio
import hashlib
import hmac
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Event

import pytest
from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django.db import close_old_connections, connection, transaction
from django.test import AsyncClient, override_settings

from modules.access.models import (
    AccessInvalidationEvent,
    StaffMember,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table
from modules.venue.models import Venue, VenueDomain
from modules.venue.management.commands.provision_spec025_ab import Command
from modules.access.services import AccessServiceError, authenticate_staff, switch_operator
from modules.guest_access.services import GuestAccessError, guest_session_context, resolve_table_qr


BACKUP = "railway-backup:verified-spec025-preflight-0001"
LOGICAL_BACKUP = "logical-sha256:" + "a1" * 32


@pytest.fixture
def pins(monkeypatch):
    monkeypatch.setenv("RODADA_SPEC025_A_PIN", "798102")
    monkeypatch.setenv("RODADA_SPEC025_B_PIN", "753921")


def run_qa(**kwargs):
    return call_command("provision_spec025_ab", stdout=StringIO(), **kwargs)


@pytest.mark.django_db
@pytest.mark.parametrize("reference,verified", [
    (LOGICAL_BACKUP, False),
    ("logical-sha256:" + "a" * 63, True),
    ("logical-sha256:" + "g" * 64, True),
    ("logical-sha256:" + "A" * 64, True),
])
def test_logical_backup_requires_exact_digest_and_verified_restore(pins, reference, verified):
    with pytest.raises(CommandError, match="verified logical backup"):
        run_qa(operation="provision", apply=True, backup_reference=reference,
               logical_backup_verified=verified)
    assert not Venue.objects.exists()


@pytest.mark.django_db
def test_verified_logical_backup_can_stage_and_activate_only_with_edge_confirmation(pins):
    kwargs = {"apply": True, "backup_reference": LOGICAL_BACKUP,
              "logical_backup_verified": True}
    run_qa(operation="provision", **kwargs)
    assert Venue.objects.count() == 2
    assert not VenueDomain.objects.filter(is_active=True).exists()
    with pytest.raises(CommandError, match="edge-confirmed"):
        run_qa(operation="activate", **kwargs)
    run_qa(operation="activate", edge_confirmed=True, **kwargs)
    assert VenueDomain.objects.filter(is_active=True).count() == 2


def login(staff, venue, pin="946382"):
    return authenticate_staff(
        venue_slug=venue.slug, login_identifier=staff.login_identifier, pin=pin,
        installation_id="qa-provision-regression", platform="ANDROID",
    )


@pytest.mark.django_db
def test_provision_does_not_enable_shared_api_login_before_activation(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    venue = Venue.objects.get(slug="spec025-qa-a")
    staff = StaffMember.objects.get(login_identifier="spec025-qa-a-owner")
    with pytest.raises(AccessServiceError, match="MEMBERSHIP_SUSPENDED"):
        login(staff, venue, "798102")


@pytest.mark.django_db
def test_containment_suspends_other_local_operators_without_affecting_foreign_access(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    venue = Venue.objects.get(slug="spec025-qa-a")
    pilot = Venue.objects.create(name="Pilot sentinel", slug="pilot-sentinel")
    staff = StaffMember.objects.create(login_identifier="qa-second-operator")
    staff.set_pin("946382")
    staff.save(update_fields=["pin_hash"])
    local = VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="STAFF")
    foreign = VenueStaffMembership.objects.create(venue=pilot, staff_member=staff, role="STAFF")
    local_session = login(staff, venue)
    foreign_session = login(staff, pilot)
    run_qa(operation="deactivate", apply=True)
    local.refresh_from_db()
    foreign.refresh_from_db()
    assert local.status == "SUSPENDED"
    assert local.version == 2
    assert foreign.status == "ACTIVE"
    assert StaffSession.objects.get(pk=local_session["session_id"]).revoked_at is not None
    assert StaffSession.objects.get(pk=foreign_session["session_id"]).revoked_at is None
    with pytest.raises(AccessServiceError, match="MEMBERSHIP_SUSPENDED"):
        login(staff, venue)
    assert login(staff, pilot)["venue"]["id"] == str(pilot.pk)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    local.refresh_from_db()
    assert local.status == "SUSPENDED"  # Only the reserved manager is restored.


@pytest.mark.django_db(transaction=True)
def test_committed_foreign_login_claim_after_preflight_aborts_entire_provision(pins, monkeypatch):
    foreign = Venue.objects.create(name="Foreign sentinel", slug="foreign-sentinel")
    original = Command._check_protected_identity
    preflights = []

    def claim_reserved_login():
        close_old_connections()
        try:
            staff = StaffMember.objects.create(login_identifier="spec025-qa-b-owner")
            VenueStaffMembership.objects.create(venue=foreign, staff_member=staff, role="STAFF")
        finally:
            close_old_connections()

    def interleaved(spec, **kwargs):
        result = original(spec, **kwargs)
        preflights.append(spec["slug"])
        if len(preflights) == 2:
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(claim_reserved_login).result(timeout=10)
        return result

    monkeypatch.setattr(Command, "_check_protected_identity", staticmethod(interleaved))
    with pytest.raises(CommandError, match="operator identifier already owned"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert not Venue.objects.filter(slug__startswith="spec025-qa-").exists()
    assert not VenueDomain.objects.exists()
    staff = StaffMember.objects.get(login_identifier="spec025-qa-b-owner")
    assert list(staff.venue_memberships.values_list("venue_id", flat=True)) == [foreign.pk]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("claimed", ["hostname", "slug"])
def test_committed_foreign_domain_or_slug_claim_after_preflight_is_not_adopted(pins, monkeypatch, claimed):
    foreign = Venue.objects.create(name="Foreign sentinel", slug="foreign-sentinel")
    original = Command._check_protected_identity
    preflights = []

    def claim_reserved_identity():
        close_old_connections()
        try:
            if claimed == "hostname":
                VenueDomain.objects.create(venue=foreign, hostname="e2eb.rodada.bar")
            else:
                Venue.objects.create(name="Foreign claimed slug", slug="spec025-qa-b")
        finally:
            close_old_connections()

    def interleaved(spec, **kwargs):
        result = original(spec, **kwargs)
        preflights.append(spec["slug"])
        if len(preflights) == 2:
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(claim_reserved_identity).result(timeout=10)
        return result

    monkeypatch.setattr(Command, "_check_protected_identity", staticmethod(interleaved))
    with pytest.raises(CommandError, match="hostname reassigned|unexpected identity"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert not Venue.objects.filter(slug="spec025-qa-a").exists()
    assert not StaffMember.objects.exists()
    if claimed == "hostname":
        assert VenueDomain.objects.get(hostname="e2eb.rodada.bar").venue_id == foreign.pk
        assert not Venue.objects.filter(slug="spec025-qa-b").exists()
    else:
        assert Venue.objects.get(slug="spec025-qa-b").name == "Foreign claimed slug"
        assert not VenueDomain.objects.exists()


@pytest.mark.django_db
def test_reprovision_after_activation_reports_preserved_state(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    output = StringIO()
    call_command("provision_spec025_ab", operation="provision", apply=True,
                 backup_reference=BACKUP, stdout=output)
    assert "domains remain unverified/inactive" not in output.getvalue()
    assert "domain=active verified=True" in output.getvalue()


@pytest.mark.django_db
def test_provision_rejects_shared_pin_before_writing(pins, monkeypatch):
    monkeypatch.setenv("RODADA_SPEC025_B_PIN", "798102")
    with pytest.raises(CommandError, match="PINs must be distinct"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert not Venue.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_parallel_provision_is_idempotent_on_postgresql(pins):
    def provision():
        close_old_connections()
        try:
            run_qa(operation="provision", apply=True, backup_reference=BACKUP)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(provision) for _ in range(2)]
        for future in futures:
            future.result(timeout=20)
    assert Venue.objects.count() == 2
    assert VenueDomain.objects.count() == 2
    assert StaffMember.objects.count() == 2
    assert VenueStaffMembership.objects.count() == 2
    assert Table.objects.count() == 2
    assert AuditEvent.objects.filter(event_type="qa.spec025_provisioned").count() == 2


@pytest.mark.django_db(transaction=True)
def test_containment_refuses_inflight_login_atomically_then_retry_revokes_it(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    venue = Venue.objects.get(slug="spec025-qa-a")
    staff = StaffMember.objects.get(login_identifier="spec025-qa-a-owner")
    membership = VenueStaffMembership.objects.get(venue=venue, staff_member=staff)
    identities_locked = Event()

    def observe_identity_lock(execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        if sql.startswith("SELECT") and '"access_staffmember"' in sql and "FOR " in sql:
            identities_locked.set()
        return result

    def contain():
        close_old_connections()
        try:
            with connection.execute_wrapper(observe_identity_lock):
                run_qa(operation="deactivate", apply=True)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as executor:
        # Real login holds its membership lock before inserting session/audit FKs.
        with transaction.atomic():
            VenueStaffMembership.objects.select_for_update().get(pk=membership.pk)
            pending = executor.submit(contain)
            assert identities_locked.wait(timeout=10)
            with pytest.raises(CommandError, match="no changes committed"):
                pending.result(timeout=10)
            assert VenueDomain.objects.filter(is_active=True).count() == 2
            tokens = login(staff, venue, "798102")
    run_qa(operation="deactivate", apply=True)
    membership.refresh_from_db()
    assert membership.status == "SUSPENDED"
    assert StaffSession.objects.get(pk=tokens["session_id"]).revoked_at is not None


@pytest.mark.django_db(transaction=True)
def test_containment_refuses_inflight_operator_switch_then_revokes_both_sessions(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    venue = Venue.objects.get(slug="spec025-qa-a")
    staff = StaffMember.objects.create(login_identifier="qa-switch-source")
    staff.set_pin("946382")
    staff.save(update_fields=["pin_hash"])
    VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="STAFF")
    tokens = login(staff, venue)
    session = StaffSession.objects.get(pk=tokens["session_id"])
    session.device.trust_state = "TRUSTED"
    session.device.save(update_fields=["trust_state"])

    def contain():
        close_old_connections()
        try:
            run_qa(operation="deactivate", apply=True)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            # Same joined locks and ordering as the actual switch service.
            locked = StaffSession.objects.select_for_update().select_related(
                "venue", "staff_member", "membership"
            ).get(pk=session.pk)
            with pytest.raises(CommandError, match="no changes committed"):
                executor.submit(contain).result(timeout=10)
            assert VenueDomain.objects.filter(is_active=True).count() == 2
            switched = switch_operator(current_session=locked,
                login_identifier="spec025-qa-a-owner", pin="798102")
    run_qa(operation="deactivate", apply=True)
    assert not StaffSession.objects.filter(venue=venue, revoked_at__isnull=True).exists()
    assert StaffSession.objects.get(pk=switched["session_id"]).revoked_at is not None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("host_bound", [True, False])
def test_containment_ends_live_asgi_staff_guest_streams_and_denies_reconnect(pins, host_bound):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    identities = []
    # Only disposable QA fixtures: guest access is separately enabled for this test.
    for suffix, pin in (("a", "798102"), ("b", "753921")):
        venue = Venue.objects.get(slug=f"spec025-qa-{suffix}")
        venue.guest_mutations_blocked = False
        venue.save(update_fields=["guest_mutations_blocked"])
        table = Table.objects.get(venue=venue)
        table.guest_ordering_mode = "DIRECT"
        table.save(update_fields=["guest_ordering_mode"])
        staff = StaffMember.objects.get(login_identifier=f"spec025-qa-{suffix}-owner")
        tokens = login(staff, venue, pin)
        guest = resolve_table_qr(public_token=table.public_token)
        identities.append((venue, table, tokens, guest))

    secret = "test-only-spec025-provision-asgi-secret"

    async def exercise():
        streams = []
        try:
            for venue, _, tokens, guest in identities:
                for is_guest in (False, True):
                    path = "/guest/realtime/stream/" if is_guest else "/realtime/stream/"
                    headers = ({"X-Guest-Session": guest.token} if is_guest else
                               {"Authorization": "Bearer " + tokens["access_token"]})
                    if host_bound:
                        host = f'e2e{venue.slug[-1]}.rodada.bar'
                        stamp = str(int(time.time()))
                        signature = hmac.new(secret.encode(),
                            f"{stamp}\nGET\n{path}\n{host}".encode(), hashlib.sha256).hexdigest()
                        headers.update({"X-Rodada-Bff-Host": host, "X-Rodada-Bff-Time": stamp,
                                        "X-Rodada-Bff-Signature": signature})
                    response = await AsyncClient().get(path, {"cursor": f"{venue.pk}:0"}, headers=headers)
                    assert response.status_code == 200
                    assert response.is_async
                    iterator = response.streaming_content.__aiter__()
                    streams.append((iterator, path, headers))
                    assert b"event: ready" in await asyncio.wait_for(iterator.__anext__(), 4)

            await sync_to_async(run_qa, thread_sensitive=True)(operation="deactivate", apply=True)

            async def expect_revoked(iterator):
                for _ in range(3):
                    frame = await asyncio.wait_for(iterator.__anext__(), 4)
                    if b"event: revoked" in frame:
                        return
                pytest.fail("QA stream survived containment")

            await asyncio.gather(*(expect_revoked(iterator) for iterator, _, _ in streams))
            for _, path, headers in streams:
                response = await AsyncClient().get(path, headers=headers)
                assert response.status_code >= 400
        finally:
            for iterator, _, _ in streams:
                await iterator.aclose()

    with override_settings(ALLOWED_HOSTS=["testserver"], RODADA_BFF_HOST_SECRET=secret):
        asyncio.run(exercise())
    for venue, table, tokens, guest in identities:
        assert StaffSession.objects.get(pk=tokens["session_id"]).revoked_at is not None
        guest.session.refresh_from_db()
        assert guest.session.revoked_at is not None
        with pytest.raises(GuestAccessError, match="GUEST_SESSION_EXPIRED"):
            guest_session_context(session_token=guest.token)
        with pytest.raises(GuestAccessError, match="VENUE_GUEST_MUTATIONS_BLOCKED"):
            resolve_table_qr(public_token=table.public_token)


@pytest.mark.django_db
def test_default_dry_run_has_no_writes_and_no_secret_requirement():
    run_qa()
    run_qa(operation="provision")
    run_qa(operation="activate")
    assert Venue.objects.count() == 0
    assert StaffMember.objects.count() == 0
    assert VenueDomain.objects.count() == 0


@pytest.mark.django_db
def test_provision_refuses_missing_backup_and_missing_private_pin(monkeypatch):
    with pytest.raises(CommandError, match="verified Railway backup"):
        run_qa(operation="provision", apply=True)
    with pytest.raises(CommandError, match="RODADA_SPEC025_A_PIN"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    monkeypatch.setenv("RODADA_SPEC025_A_PIN", "1234")
    with pytest.raises(CommandError, match="6-12 digit"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert not Venue.objects.exists()


@pytest.mark.django_db
def test_provision_is_idempotent_and_preserves_existing_pilot(pins):
    pilot = Venue.objects.create(name="Bar do Aderlan", slug="bar-do-aderlan")
    pilot_domain = VenueDomain.objects.create(
        venue=pilot, hostname="bardoaderlan.rodada.bar",
        is_active=True, is_verified=True,
    )
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    snapshot = {}
    for slug, host, login in (
        ("spec025-qa-a", "e2ea.rodada.bar", "spec025-qa-a-owner"),
        ("spec025-qa-b", "e2eb.rodada.bar", "spec025-qa-b-owner"),
    ):
        venue = Venue.objects.get(slug=slug)
        domain = VenueDomain.objects.get(hostname=host)
        staff = StaffMember.objects.get(login_identifier=login)
        assert staff.check_pin("798102" if slug.endswith("a") else "753921")
        assert venue.guest_mutations_blocked
        assert domain.venue == venue
        assert not domain.is_active and not domain.is_verified
        assert VenueStaffMembership.objects.filter(
            venue=venue, staff_member=staff, role="MANAGER"
        ).count() == 1
        assert Table.objects.filter(venue=venue, label="QA 01").count() == 1
        snapshot[slug] = (venue.id, domain.id, staff.id)
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert AuditEvent.objects.filter(event_type="qa.spec025_provisioned").count() == 2
    for slug, (venue_id, domain_id, staff_id) in snapshot.items():
        assert Venue.objects.get(slug=slug).id == venue_id
        assert VenueDomain.objects.get(venue_id=venue_id).id == domain_id
        assert StaffMember.objects.get(id=staff_id).venue_memberships.count() == 1
    pilot.refresh_from_db()
    pilot_domain.refresh_from_db()
    assert pilot.name == "Bar do Aderlan"
    assert pilot_domain.is_active and pilot_domain.is_verified
    assert pilot_domain.venue_id == pilot.pk


@pytest.mark.django_db
def test_hostname_collision_aborts_both_tenants_without_reassignment(pins):
    foreign = Venue.objects.create(name="Pilot", slug="pilot-foreign")
    VenueDomain.objects.create(
        venue=foreign, hostname="e2eb.rodada.bar", is_verified=False,
    )
    with pytest.raises(CommandError, match="hostname is already owned"):
        run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    assert not Venue.objects.filter(slug__startswith="spec025-qa-").exists()
    assert not StaffMember.objects.filter(
        login_identifier__startswith="spec025-qa-"
    ).exists()
    assert VenueDomain.objects.get(hostname="e2eb.rodada.bar").venue == foreign


@pytest.mark.django_db
def test_activation_requires_edge_proof_and_separately_verified_backup(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    with pytest.raises(CommandError, match="verified Railway backup"):
        run_qa(operation="activate", apply=True, edge_confirmed=True)
    with pytest.raises(CommandError, match="edge-confirmed"):
        run_qa(operation="activate", apply=True, backup_reference=BACKUP)
    assert not VenueDomain.objects.filter(is_active=True).exists()
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    assert VenueDomain.objects.filter(
        hostname__in=["e2ea.rodada.bar", "e2eb.rodada.bar"],
        is_active=True, is_verified=True,
    ).count() == 2


@pytest.mark.django_db
def test_containment_disables_aliases_and_revokes_all_qa_sessions(pins):
    run_qa(operation="provision", apply=True, backup_reference=BACKUP)
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    venue = Venue.objects.get(slug="spec025-qa-a")
    staff = StaffMember.objects.get(login_identifier="spec025-qa-a-owner")
    membership = VenueStaffMembership.objects.get(venue=venue, staff_member=staff)
    session = StaffSession.objects.create(
        venue=venue, staff_member=staff, membership=membership,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    run_qa(operation="deactivate", apply=True)
    session.refresh_from_db()
    assert session.revoked_at is not None
    assert "Spec025 QA" in session.revocation_reason
    assert AccessInvalidationEvent.objects.filter(
        session_id=session.id, event_type="SESSION_REVOKED"
    ).exists()
    assert VenueDomain.objects.filter(
        hostname__in=["e2ea.rodada.bar", "e2eb.rodada.bar"],
        is_active=True,
    ).count() == 0
    membership.refresh_from_db()
    assert membership.status == "SUSPENDED"
    assert AccessInvalidationEvent.objects.filter(
        venue_id=venue.id, staff_member_id=staff.id,
        event_type="MEMBERSHIP_CHANGED",
    ).exists()
    # A second backout is safe; reactivation must explicitly restore QA membership.
    run_qa(operation="deactivate", apply=True)
    membership.refresh_from_db()
    assert membership.status == "SUSPENDED"
    run_qa(operation="activate", apply=True, backup_reference=BACKUP, edge_confirmed=True)
    membership.refresh_from_db()
    assert membership.status == "ACTIVE"
    assert session.revoked_at is not None  # Reactivation cannot resurrect old sessions.
