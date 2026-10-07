from django.test import TestCase

from modules.access.capabilities import Capability, effective_capabilities, has_capability
from modules.access.models import MembershipStatus, StaffMember, StaffRole, VenueStaffMembership
from modules.venue.models import Venue


class CapabilityResolutionTests(TestCase):
    def setUp(self):
        self.venue_a = Venue.objects.create(name="Bar A", slug="bar-a")
        self.venue_b = Venue.objects.create(name="Bar B", slug="bar-b")
        self.staff = StaffMember.objects.create(
            display_name="Ana",
            login_identifier="ana",
        )

    def membership(self, venue, role=StaffRole.STAFF, **kwargs):
        return VenueStaffMembership.objects.create(
            venue=venue,
            staff_member=self.staff,
            role=role,
            **kwargs,
        )

    def test_staff_role_cannot_refund(self):
        membership = self.membership(self.venue_a, StaffRole.STAFF)

        assert has_capability(membership, Capability.ORDER_CONFIRM)
        assert not has_capability(membership, Capability.REFUND_CREATE)

    def test_manager_role_can_refund(self):
        membership = self.membership(self.venue_a, StaffRole.MANAGER)

        assert has_capability(membership, Capability.REFUND_CREATE)
        assert has_capability(membership, Capability.VENUE_CONFIGURE)

    def test_owner_receives_all_known_capabilities(self):
        membership = self.membership(self.venue_a, StaffRole.OWNER)

        assert Capability.STAFF_MANAGE in effective_capabilities(membership)
        assert Capability.CASH_ADJUSTMENT_CREATE in effective_capabilities(membership)

    def test_explicit_deny_removes_role_capability(self):
        membership = self.membership(
            self.venue_a,
            StaffRole.MANAGER,
            capability_overrides={"deny": [Capability.REFUND_CREATE]},
        )

        assert not has_capability(membership, Capability.REFUND_CREATE)

    def test_explicit_allow_can_extend_baseline(self):
        membership = self.membership(
            self.venue_a,
            StaffRole.STAFF,
            capability_overrides={"allow": [Capability.PAYMENT_COLLECT]},
        )

        assert has_capability(membership, Capability.PAYMENT_COLLECT)

    def test_inactive_membership_has_no_capabilities(self):
        membership = self.membership(
            self.venue_a,
            StaffRole.OWNER,
            status=MembershipStatus.REVOKED,
        )

        assert effective_capabilities(membership) == frozenset()

    def test_membership_does_not_grant_other_venue(self):
        membership_a = self.membership(self.venue_a, StaffRole.MANAGER)

        assert membership_a.venue_id == self.venue_a.id
        assert not VenueStaffMembership.objects.filter(
            venue=self.venue_b,
            staff_member=self.staff,
            status=MembershipStatus.ACTIVE,
        ).exists()
