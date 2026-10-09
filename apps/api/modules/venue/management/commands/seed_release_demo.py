"""Provision test identities only; the shift runner uses public HTTP commands."""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from modules.access.models import StaffMember, VenueStaffMembership
from modules.venue.models import Venue


class Command(BaseCommand):
    help = "Provision isolated release QA identities in the Compose demo database"

    @transaction.atomic
    def handle(self, *args, **options):
        if connection.settings_dict["NAME"] != "rodada_demo":
            raise CommandError("Release fixtures require the isolated rodada_demo database")
        for slug in ("release-demo", "release-other"):
            venue, _ = Venue.objects.get_or_create(slug=slug, defaults={"name": slug})
            for identifier, role, pin in (
                ("release-owner", "OWNER", "2468"),
                ("release-staff", "STAFF", "1357"),
            ):
                staff, created = StaffMember.objects.get_or_create(
                    login_identifier=identifier, defaults={"display_name": identifier}
                )
                if created:
                    staff.set_pin(pin)
                    staff.save(update_fields=["pin_hash"])
                if slug == "release-demo" or role == "OWNER":
                    VenueStaffMembership.objects.get_or_create(
                        venue=venue, staff_member=staff, defaults={"role": role}
                    )
        self.stdout.write("Release QA identities provisioned (test environment only)")
