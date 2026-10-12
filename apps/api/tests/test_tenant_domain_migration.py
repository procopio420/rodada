"""Real data-migration callable and seed lifecycle, against the integration database."""

import importlib
import io

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import connection

from modules.venue.domains import configure_domain
from modules.venue.hostnames import resolve_venue_from_hostname
from modules.venue.models import Venue, VenueDomain

pytestmark = pytest.mark.django_db


def test_existing_pilot_data_migration_preserves_uuid_and_disabled_state():
    pilot = Venue.objects.create(name="Existing pilot", slug="bar-do-aderlan")
    other = Venue.objects.create(name="Other", slug="bar-teste")
    module = importlib.import_module("modules.venue.migrations.0009_pilot_venue_domain")
    module.seed_existing_pilot(apps, connection.schema_editor())
    domain = VenueDomain.objects.get(hostname="bardoaderlan.rodada.ai")
    assert domain.venue_id == pilot.pk
    assert resolve_venue_from_hostname(domain.hostname).pk == pilot.pk
    assert not VenueDomain.objects.filter(venue=other).exists()
    configure_domain(
        venue_id=pilot.pk,
        hostname=domain.hostname,
        is_active=False,
        is_verified=True,
        reason="Explicitly disabled",
    )
    module.seed_existing_pilot(apps, connection.schema_editor())
    domain.refresh_from_db()
    pilot.refresh_from_db()
    assert pilot.slug == "bar-do-aderlan" and not domain.is_active


def test_new_demo_seed_maps_pilot_but_reseed_does_not_reenable_alias():
    output = io.StringIO()
    call_command("seed_demo", stdout=output)
    pilot = Venue.objects.get(slug="bar-do-aderlan")
    domain = VenueDomain.objects.get(hostname="bardoaderlan.rodada.ai")
    assert domain.venue_id == pilot.pk and domain.is_primary
    configure_domain(
        venue_id=pilot.pk,
        hostname=domain.hostname,
        is_active=False,
        is_verified=True,
        reason="Explicitly disabled",
    )
    call_command("seed_demo", stdout=output)
    domain.refresh_from_db()
    assert not domain.is_active
