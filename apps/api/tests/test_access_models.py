from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from modules.access.models import (
    DeviceRegistration,
    DeviceTrustState,
    MembershipStatus,
    StaffMember,
    StaffRole,
    StaffSession,
    VenueStaffMembership,
)
from modules.venue.models import Venue


class AccessModelTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar", slug="bar")
        self.staff = StaffMember.objects.create(display_name="Bruno", login_identifier="bruno")
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.CASHIER,
        )
        self.device = DeviceRegistration.objects.create(
            venue=self.venue,
            installation_key_hash="device-hash",
            platform="ANDROID",
            trust_state=DeviceTrustState.TRUSTED,
        )

    def test_pin_is_hashed_and_verifiable(self):
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])

        assert self.staff.pin_hash != "1234"
        assert self.staff.check_pin("1234")
        assert not self.staff.check_pin("0000")

    def test_session_validity_tracks_membership_and_device(self):
        session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            device=self.device,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        assert session.is_valid

        self.membership.status = MembershipStatus.REVOKED
        self.membership.save(update_fields=["status"])

        session.refresh_from_db()
        assert not session.is_valid

    def test_revoked_device_invalidates_bound_session(self):
        session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            device=self.device,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.device.trust_state = DeviceTrustState.REVOKED
        self.device.save(update_fields=["trust_state"])

        session.refresh_from_db()
        assert not session.is_valid
