"""Pilot hostname must survive migration-before-seed startup ordering."""
import io
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from modules.venue.models import Venue, VenueDomain


@pytest.mark.django_db
def test_fresh_seed_provisions_alias_and_reseed_preserves_manual_suspension():
    assert not Venue.objects.filter(slug="bar-do-aderlan").exists()
    assert not VenueDomain.objects.filter(hostname="bardoaderlan.rodada.bar").exists()
    call_command("seed_demo", stdout=io.StringIO())
    venue = Venue.objects.get(slug="bar-do-aderlan")
    alias = VenueDomain.objects.get(hostname="bardoaderlan.rodada.bar")
    assert alias.venue_id == venue.id and alias.is_verified and alias.is_active
    alias.is_active = False
    alias.save(update_fields=["is_active"])
    call_command("seed_demo", stdout=io.StringIO())
    alias.refresh_from_db()
    assert not alias.is_active


@pytest.mark.django_db
def test_seed_refuses_hostname_ownership_collision():
    other = Venue.objects.create(name="Other", slug="other")
    VenueDomain.objects.create(venue=other, hostname="bardoaderlan.rodada.bar",
                               is_verified=True, is_active=True)
    with pytest.raises(CommandError, match="different Venue"):
        call_command("seed_demo", stdout=io.StringIO())
    assert VenueDomain.objects.get(hostname="bardoaderlan.rodada.bar").venue_id == other.id
