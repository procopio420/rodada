"""Test-only shared seed; never imported by application code."""
import os
from datetime import timedelta
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

def seed():
    from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
    from modules.access.services import hash_token
    from modules.cash.models import CashPoint
    from modules.catalog.models import Product
    from modules.venue.models import Venue

    if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3"):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL")
    venue = Venue.objects.create(name="Web E2E — test only", slug="web-e2e")
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
    if os.environ.get("RODADA_E2E_MENU") == "1":
        # Explicit disposable test-only import of the photographed canonical CSV.
        from modules.catalog.management.commands.seed_demo_catalog import MENU_CSV
        call_command("import_catalog_csv", file=str(MENU_CSV), venue_slug=venue.slug,
                     apply=True, update_existing=False, verbosity=0)
    CashPoint.objects.create(venue=venue, label="E2E drawer")
