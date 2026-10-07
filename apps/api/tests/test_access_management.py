from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import (
    DeviceRegistration,
    DeviceTrustState,
    MembershipStatus,
    StaffMember,
    StaffRole,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.venue.models import Venue


class AccessManagementAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Bar A", slug="manage-bar-a")
        self.other_venue = Venue.objects.create(name="Bar B", slug="manage-bar-b")

        self.owner = StaffMember.objects.create(
            display_name="Owner",
            login_identifier="owner-manage",
        )
        self.owner.set_pin("1111")
        self.owner.save(update_fields=["pin_hash"])
        self.owner_membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.owner,
            role=StaffRole.OWNER,
        )

        self.manager = StaffMember.objects.create(
            display_name="Manager",
            login_identifier="manager-manage",
        )
        self.manager.set_pin("2222")
        self.manager.save(update_fields=["pin_hash"])
        self.manager_membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.manager,
            role=StaffRole.MANAGER,
        )

        self.staff = StaffMember.objects.create(
            display_name="Staff",
            login_identifier="staff-manage",
        )
        self.staff.set_pin("3333")
        self.staff.save(update_fields=["pin_hash"])
        self.staff_membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.STAFF,
        )

        response = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.owner.login_identifier,
                "pin": "1111",
                "installation_id": "owner-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        self.owner_tokens = response.json()
        self.owner_device = DeviceRegistration.objects.get(
            venue=self.venue,
            installation_key_hash__isnull=False,
        )

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def reauth_owner(self):
        self.bearer(self.owner_tokens["access_token"])
        response = self.client.post(
            "/auth/reauthenticate/",
            {"pin": "1111"},
            format="json",
        )
        assert response.status_code == 200, response.json()

    def create_staff_session(self, *, device=None):
        return StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.staff_membership,
            device=device,
            access_token_hash=None,
            refresh_token_hash=None,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_owner_can_list_memberships_devices_sessions_and_audit(self):
        self.bearer(self.owner_tokens["access_token"])

        memberships = self.client.get("/manage/access/memberships/")
        devices = self.client.get("/manage/access/devices/")
        sessions = self.client.get("/manage/access/sessions/")
        audit = self.client.get("/manage/access/audit/")

        assert memberships.status_code == 200
        assert len(memberships.json()["results"]) == 3
        assert devices.status_code == 200
        assert len(devices.json()["results"]) == 1
        assert sessions.status_code == 200
        assert len(sessions.json()["results"]) >= 1
        assert audit.status_code == 200
        assert any(
            item["event_type"] == "auth.login_succeeded"
            for item in audit.json()["results"]
        )

    def test_manager_without_staff_manage_is_denied(self):
        response = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.manager.login_identifier,
                "pin": "2222",
                "installation_id": "manager-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert response.status_code == 200
        self.bearer(response.json()["access_token"])

        denied = self.client.get("/manage/access/memberships/")

        assert denied.status_code == 403
        assert denied.json()["code"] == "CAPABILITY_REQUIRED"

    def test_management_mutation_requires_recent_reauth(self):
        self.bearer(self.owner_tokens["access_token"])

        response = self.client.patch(
            f"/manage/access/memberships/{self.staff_membership.id}/",
            {
                "expected_version": self.staff_membership.version,
                "role": StaffRole.CASHIER,
            },
            format="json",
        )

        assert response.status_code == 403
        assert response.json()["code"] == "REAUTH_REQUIRED"

    def test_membership_role_update_uses_version_and_audit(self):
        self.reauth_owner()

        response = self.client.patch(
            f"/manage/access/memberships/{self.staff_membership.id}/",
            {
                "expected_version": 1,
                "role": StaffRole.CASHIER,
                "reason": "vai operar caixa",
            },
            format="json",
        )

        assert response.status_code == 200, response.json()
        assert response.json()["role"] == StaffRole.CASHIER
        assert response.json()["version"] == 2

        stale = self.client.patch(
            f"/manage/access/memberships/{self.staff_membership.id}/",
            {
                "expected_version": 1,
                "role": StaffRole.MANAGER,
            },
            format="json",
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "VERSION_CONFLICT"

        event = AuditEvent.objects.get(
            venue=self.venue,
            event_type="membership.role_changed",
        )
        assert event.actor_staff_id == self.owner.id
        assert event.metadata["target_staff_id"] == str(self.staff.id)

    def test_owner_cannot_change_own_role_through_same_session(self):
        self.reauth_owner()

        response = self.client.patch(
            f"/manage/access/memberships/{self.owner_membership.id}/",
            {
                "expected_version": 1,
                "role": StaffRole.STAFF,
            },
            format="json",
        )

        assert response.status_code == 409
        assert response.json()["code"] == "SELF_ROLE_CHANGE_FORBIDDEN"

    def test_suspending_membership_revokes_existing_target_sessions(self):
        target_session = self.create_staff_session()
        self.reauth_owner()

        response = self.client.patch(
            f"/manage/access/memberships/{self.staff_membership.id}/",
            {
                "expected_version": 1,
                "status": MembershipStatus.SUSPENDED,
                "reason": "fim do turno",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["status"] == MembershipStatus.SUSPENDED

        target_session.refresh_from_db()
        assert target_session.revoked_at is not None
        assert target_session.revocation_reason == "MEMBERSHIP_SUSPENDED"

    def test_trusting_device_then_revoking_it_kills_bound_sessions(self):
        device = DeviceRegistration.objects.create(
            venue=self.venue,
            installation_key_hash="target-device-hash",
            platform="ANDROID",
            trust_state=DeviceTrustState.UNTRUSTED,
        )
        target_session = self.create_staff_session(device=device)
        self.reauth_owner()

        trusted = self.client.patch(
            f"/manage/access/devices/{device.id}/",
            {"trust_state": DeviceTrustState.TRUSTED},
            format="json",
        )
        assert trusted.status_code == 200
        assert trusted.json()["trust_state"] == DeviceTrustState.TRUSTED

        revoked = self.client.patch(
            f"/manage/access/devices/{device.id}/",
            {
                "trust_state": DeviceTrustState.REVOKED,
                "reason": "aparelho perdido",
            },
            format="json",
        )
        assert revoked.status_code == 200
        assert revoked.json()["trust_state"] == DeviceTrustState.REVOKED

        target_session.refresh_from_db()
        assert target_session.revoked_at is not None
        assert target_session.revocation_reason == "DEVICE_REVOKED"

        event = AuditEvent.objects.get(
            venue=self.venue,
            event_type="auth.device_revoked",
        )
        assert event.actor_staff_id == self.owner.id
        assert event.metadata["target_device_id"] == str(device.id)

    def test_admin_can_revoke_specific_session(self):
        target_session = self.create_staff_session()
        self.reauth_owner()

        response = self.client.post(
            f"/manage/access/sessions/{target_session.id}/revoke/",
            {"reason": "sessao suspeita"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["revoked_at"] is not None

        target_session.refresh_from_db()
        assert target_session.revocation_reason == "sessao suspeita"

    def test_other_venue_resources_are_not_manageable(self):
        outsider = StaffMember.objects.create(
            display_name="Other",
            login_identifier="other-manage",
        )
        outsider_membership = VenueStaffMembership.objects.create(
            venue=self.other_venue,
            staff_member=outsider,
            role=StaffRole.STAFF,
        )
        self.reauth_owner()

        response = self.client.patch(
            f"/manage/access/memberships/{outsider_membership.id}/",
            {
                "expected_version": 1,
                "role": StaffRole.CASHIER,
            },
            format="json",
        )

        assert response.status_code == 404
        assert response.json()["code"] == "NOT_FOUND"
