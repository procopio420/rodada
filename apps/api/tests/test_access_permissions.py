from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from modules.access.capabilities import Capability
from modules.access.errors import AccessPermissionDenied
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.access.permissions import RequireCapability, RequireRecentReauthentication
from modules.venue.models import Venue


class CapabilityPermissionTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar", slug="bar")
        self.staff = StaffMember.objects.create(display_name="Bia", login_identifier="bia")
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.STAFF,
        )
        self.session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.request = SimpleNamespace(auth=self.session)

    def test_required_capability_allows_role_capability(self):
        view = SimpleNamespace(required_capability=Capability.ORDER_CONFIRM)

        assert RequireCapability().has_permission(self.request, view)

    def test_required_capability_denies_missing_capability_with_code(self):
        view = SimpleNamespace(required_capability=Capability.REFUND_CREATE)

        try:
            RequireCapability().has_permission(self.request, view)
        except AccessPermissionDenied as exc:
            assert exc.detail["code"] == "CAPABILITY_REQUIRED"
            assert exc.detail["capability"] == Capability.REFUND_CREATE
        else:
            raise AssertionError("missing capability should be denied")


class RecentReauthenticationPermissionTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Reauth Bar", slug="reauth-bar")
        self.staff = StaffMember.objects.create(
            display_name="Rafa",
            login_identifier="rafa-reauth",
        )
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.MANAGER,
        )
        self.session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.request = SimpleNamespace(auth=self.session)

    def test_permission_returns_reauth_required_without_recent_proof(self):
        try:
            RequireRecentReauthentication().has_permission(self.request, SimpleNamespace())
        except AccessPermissionDenied as exc:
            assert exc.detail["code"] == "REAUTH_REQUIRED"
        else:
            raise AssertionError("stale privileged action should require reauthentication")

    def test_permission_accepts_recent_reauthentication(self):
        self.session.recently_reauthenticated_at = timezone.now()
        self.session.save(update_fields=["recently_reauthenticated_at"])

        assert RequireRecentReauthentication().has_permission(
            self.request,
            SimpleNamespace(),
        )

    def test_permission_rejects_expired_reauthentication_window(self):
        self.session.recently_reauthenticated_at = timezone.now() - timedelta(minutes=6)
        self.session.save(update_fields=["recently_reauthenticated_at"])

        try:
            RequireRecentReauthentication().has_permission(self.request, SimpleNamespace())
        except AccessPermissionDenied as exc:
            assert exc.detail["code"] == "REAUTH_REQUIRED"
        else:
            raise AssertionError("expired reauthentication should be rejected")
