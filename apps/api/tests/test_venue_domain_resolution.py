import pytest
from django.core.exceptions import ValidationError

from modules.venue.domain_resolution import resolve_venue_domain
from modules.venue.models import Venue, VenueDomain


@pytest.mark.django_db
def test_resolves_only_verified_active_hostname():
    venue = Venue.objects.create(name="Pilot", slug="pilot")
    domain = VenueDomain.objects.create(
        venue=venue, hostname="bardoaderlan.rodada.bar",
        is_active=False, is_verified=False,
    )
    assert resolve_venue_domain(domain.hostname) is None
    domain.is_verified = True
    domain.save()
    assert resolve_venue_domain(domain.hostname) is None
    domain.is_active = True
    domain.save()
    assert resolve_venue_domain(domain.hostname).venue_id == venue.id
    assert resolve_venue_domain("unknown.rodada.bar") is None


@pytest.mark.django_db
def test_rejects_reserved_and_duplicate_domains():
    venue = Venue.objects.create(name="Pilot", slug="pilot")
    with pytest.raises(ValidationError):
        VenueDomain.objects.create(venue=venue, hostname="api.rodada.bar")
    VenueDomain.objects.create(venue=venue, hostname="pilot.rodada.bar")
    with pytest.raises(ValidationError):
        VenueDomain.objects.create(venue=venue, hostname="pilot.rodada.bar")
