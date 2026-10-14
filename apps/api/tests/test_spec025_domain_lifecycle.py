"""Database defense-in-depth for Spec 025 VenueDomain identity and audit."""
import pytest
from django.db import DatabaseError, connection, transaction

from modules.audit.models import AuditEvent
from modules.venue.models import Venue, VenueDomain


@pytest.mark.django_db
def test_venue_domain_bulk_identity_change_and_delete_fail_closed():
    if connection.vendor != "postgresql":
        pytest.skip("Database lifecycle trigger is PostgreSQL-only")

    venue = Venue.objects.create(name="Security Pilot", slug="security-pilot-domain")
    alias = VenueDomain.objects.create(
        venue=venue, hostname="security-pilot.rodada.bar",
        is_active=True, is_verified=True,
    )
    with pytest.raises(DatabaseError), transaction.atomic():
        VenueDomain.objects.filter(pk=alias.pk).update(
            hostname="hijacked.rodada.bar",
        )
    with pytest.raises(DatabaseError), transaction.atomic():
        VenueDomain.objects.filter(pk=alias.pk).delete()

    alias.refresh_from_db()
    assert alias.hostname == "security-pilot.rodada.bar"
    assert alias.venue_id == venue.pk


@pytest.mark.django_db
def test_venue_domain_status_update_is_audited_without_reassigning_identity():
    if connection.vendor != "postgresql":
        pytest.skip("Database lifecycle trigger is PostgreSQL-only")

    venue = Venue.objects.create(name="Security Pilot", slug="security-pilot-status")
    alias = VenueDomain.objects.create(
        venue=venue, hostname="security-status.rodada.bar",
        is_active=True, is_verified=True,
    )
    VenueDomain.objects.filter(pk=alias.pk).update(is_active=False)
    alias.refresh_from_db()
    assert alias.is_active is False
    assert AuditEvent.objects.filter(
        venue=venue,
        event_type="venue.domain_database_changed",
        entity_id=str(alias.pk),
    ).count() >= 2  # creation and status change
