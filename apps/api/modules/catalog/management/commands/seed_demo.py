from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.venue.models import Venue


class Command(BaseCommand):
    help = "Create idempotent local Bar do Aderlan staff and catalog demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_demo_catalog", venue_slug="bar-do-aderlan", venue_name="Bar do Aderlan")
        venue = Venue.objects.get(slug="bar-do-aderlan")
        for name, identifier, pin, role in (
            ("Ana Gerente", "ana", "0420", StaffRole.MANAGER),
            ("Bia Staff", "bia", "1234", StaffRole.STAFF),
        ):
            staff, _ = StaffMember.objects.get_or_create(login_identifier=identifier, defaults={"display_name": name})
            staff.display_name = name
            staff.set_pin(pin)
            staff.save(update_fields=["display_name", "pin_hash"])
            VenueStaffMembership.objects.update_or_create(venue=venue, staff_member=staff, defaults={"role": role})
        self.stdout.write(self.style.SUCCESS("Demo ready: bar-do-aderlan; Ana Gerente/0420, Bia Staff/1234."))
