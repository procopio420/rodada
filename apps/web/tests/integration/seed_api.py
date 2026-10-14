"""Shared test-only seed; reset is restricted to the disposable local PostgreSQL DB."""

import os
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))

def seed_api():
    from django.conf import settings
    from django.core.management import call_command
    from django.utils import timezone
    from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
    from modules.access.services import hash_token
    from modules.cash.models import CashPoint
    from modules.catalog.models import Product
    from modules.venue.models import Venue, VenueDomain
    from modules.hospitality.models import Table, GuestOrderingMode

    call_command("migrate", verbosity=0)
    if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3"):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL")
    venue = Venue.objects.create(name="Web E2E — test only", slug="web-e2e", table_service_enabled=True)
    other_venue = Venue.objects.create(name="Other E2E — test only", slug="other-e2e")
    VenueDomain.objects.create(venue=venue, hostname="e2ea.rodada.bar", is_active=True, is_verified=True)
    VenueDomain.objects.create(venue=other_venue, hostname="e2eb.rodada.bar", is_active=True, is_verified=True)
    Table.objects.create(venue=venue, label="QR-A", guest_ordering_mode=GuestOrderingMode.DIRECT, public_token="e2e-guest-qr-a")
    Table.objects.create(venue=other_venue, label="QR-B", guest_ordering_mode=GuestOrderingMode.DIRECT, public_token="e2e-guest-qr-b")
    other_staff = StaffMember.objects.create(display_name="test-other", login_identifier="test-other")
    other_staff.set_pin("2468")
    other_staff.save(update_fields=["pin_hash"])
    VenueStaffMembership.objects.create(venue=other_venue, staff_member=other_staff, role=StaffRole.MANAGER)

    for identifier, role in [("test-manager", StaffRole.MANAGER), ("test-staff", StaffRole.STAFF), ("test-owner", StaffRole.OWNER)]:
        staff = StaffMember.objects.create(display_name=identifier, login_identifier=identifier)
        staff.set_pin("2468")
        staff.save(update_fields=["pin_hash"])
        member = VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=role)
        if role == StaffRole.STAFF:
            past = timezone.now() - timedelta(minutes=5)
            StaffSession.objects.create(venue=venue, staff_member=staff, membership=member, expires_at=past,
                access_expires_at=past, access_token_hash=hash_token("rat_e2e-expired-only"),
                refresh_token_hash=hash_token("rrt_e2e-expired-only"))
    Product.objects.create(venue=venue, name="Kitchen E2E item", price_cents=1000, fulfillment_station="KITCHEN")
    Product.objects.create(venue=venue, name="Bar E2E item", price_cents=500, fulfillment_station="BAR")
    CashPoint.objects.create(venue=venue, label="E2E drawer")


if __name__ == "__main__":
    import os
    import django
    os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"
    django.setup()
    from django.conf import settings
    from django.core.management import call_command
    from e2e_db_guard import e2e_database_guard, retry_transient_reset
    assert os.environ.get("RODADA_E2E_POSTGRES") == "1", "Reset requires explicit test opt-in"
    db = settings.DATABASES["default"]
    assert db["NAME"] == "rodada_web_e2e" and db["HOST"] in {"127.0.0.1", "localhost"}, "Reset requires disposable local test DB"
    # Playwright is single-worker, so no test request is intentionally active
    # between files. The long-lived realtime publisher still needs to pause.
    with e2e_database_guard(exclusive=True):
        # A previous test may have a lingering HTTP read. Retry PostgreSQL
        # deadlock/lock-timeout only; other DB errors remain hard failures.
        retry_transient_reset(lambda: call_command("flush", interactive=False, verbosity=0))
        seed_api()
