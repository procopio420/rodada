"""Run the real API with explicit test-only fixtures in an isolated database.

SQLite is disposable locally; CI provisions a dedicated PostgreSQL service/database.
Never points at or seeds a developer's ordinary database by default.
"""
import os
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "api"))
os.environ["DJANGO_SETTINGS_MODULE"] = "rodada_api.settings"

from django.conf import settings

with tempfile.TemporaryDirectory(prefix="rodada-web-e2e-") as temporary:
    if os.environ.get("RODADA_E2E_POSTGRES") != "1":
        settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(Path(temporary) / "test.sqlite3")}}
    else:
        # Explicit opt-in requires the dedicated CI database, never ordinary rodada.
        if settings.DATABASES["default"]["NAME"] != "rodada_web_e2e":
            raise RuntimeError("Real Web tests require dedicated database rodada_web_e2e")
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

    import django
    django.setup()
    from django.core.management import call_command
    from django.utils import timezone
    from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
    from modules.access.services import hash_token
    from modules.cash.models import CashPoint
    from modules.catalog.models import Product
    from modules.venue.models import Venue

    call_command("migrate", verbosity=0)
    venue = Venue.objects.create(name="Web E2E — test only", slug="web-e2e")
    for identifier, role in [("test-manager", StaffRole.MANAGER), ("test-staff", StaffRole.STAFF)]:
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
    call_command("runserver", "127.0.0.1:8100", use_reloader=False, verbosity=0)
