"""Safe, auditable Spec025 QA provisioning: no pilot mutation or implicit rollout."""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from modules.access.models import (
    AccessInvalidationEvent,
    StaffMember,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.hospitality.models import Table
from modules.venue.models import Venue, VenueDomain


BACKUP = "railway-backup:verified-spec025-preflight-0001"


@pytest.fixture
def pins(monkeypatch):
    monkeypatch.setenv("RODADA_SPEC025_A_PIN", "798102")
    monkeypatch.setenv("RODADA_SPEC025_B_PIN", "753921")


def run_qa(**kwargs):
    return call_command("provision_spec025_ab", stdout=StringIO(), **kwargs)


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
