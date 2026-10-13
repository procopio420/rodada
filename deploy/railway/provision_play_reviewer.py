"""One-time reviewer bootstrap; enabled only by explicit Railway environment input."""
import os
from django.db import transaction
from modules.access.models import StaffMember, VenueStaffMembership, StaffRole, MembershipStatus
from modules.venue.models import Venue

pin = os.environ.get("RODADA_PLAY_REVIEW_PIN", "")
if not pin:
    print("Play reviewer bootstrap skipped")
else:
    if not (pin.isdigit() and 6 <= len(pin) <= 12):
        raise SystemExit("RODADA_PLAY_REVIEW_PIN must be 6-12 digits")
    with transaction.atomic():
        venue = Venue.objects.get(slug="bar-do-aderlan")
        staff, _ = StaffMember.objects.get_or_create(
            login_identifier="play-review@rodada.bar",
            defaults={"display_name": "Google Play Reviewer"},
        )
        staff.set_pin(pin)
        staff.is_active = True
        staff.save(update_fields=["pin_hash", "is_active"])
        membership, created = VenueStaffMembership.objects.get_or_create(
            venue=venue, staff_member=staff,
            defaults={"role": StaffRole.OWNER, "status": MembershipStatus.ACTIVE},
        )
        if not created and membership.status != MembershipStatus.ACTIVE:
            raise SystemExit("Reviewer membership is not active; refusing to reactivate")
    print("Play reviewer account provisioned (PIN hidden)")
