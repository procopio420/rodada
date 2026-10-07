from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.invalidation import AccessInvalidationType
from modules.access.models import (
    AccessInvalidationEvent,
    DeviceRegistration,
    DeviceTrustState,
    StaffMember,
    StaffRole,
    StaffSession,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.audit.services import record_audit_event
from modules.venue.models import Venue


class ActorContextTests(TestCase):
    def test_actor_context_carries_venue_staff_session_and_device_into_audit(self):
        venue = Venue.objects.create(name="Context Bar", slug="context-bar")
        staff = StaffMember.objects.create(
            display_name="Ana",
            login_identifier="actor-context-ana",
        )
        membership = VenueStaffMembership.objects.create(
            venue=venue,
            staff_member=staff,
            role=StaffRole.MANAGER,
        )
        device = DeviceRegistration.objects.create(
            venue=venue,
            installation_key_hash="actor-context-device",
            platform="ANDROID",
        )
        session = StaffSession.objects.create(
            venue=venue,
            staff_member=staff,
            membership=membership,
            device=device,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        event = record_audit_event(
            actor=ActorContext.from_session(session),
            event_type="test.domain_mutation",
            entity_type="TestEntity",
            entity_id="123",
        )

        assert event.venue_id == venue.id
        assert event.actor_staff_id == staff.id
        assert event.actor_session_id == session.id
        assert event.device_id == device.id


class AccessInvalidationFeedTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Feed Bar", slug="feed-bar")

        self.owner = StaffMember.objects.create(
            display_name="Owner",
            login_identifier="feed-owner",
        )
        self.owner.set_pin("1111")
        self.owner.save(update_fields=["pin_hash"])
        self.owner_membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.owner,
            role=StaffRole.OWNER,
        )

        self.staff = StaffMember.objects.create(
            display_name="Staff",
            login_identifier="feed-staff",
        )
        self.staff.set_pin("2222")
        self.staff.save(update_fields=["pin_hash"])
        self.staff_membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.STAFF,
        )

        self.owner_tokens = self.login(self.owner.login_identifier, "1111", "feed-owner-device")
        self.staff_tokens = self.login(self.staff.login_identifier, "2222", "feed-staff-device")

    def login(self, login_identifier, pin, installation_id):
        response = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": login_identifier,
                "pin": pin,
                "installation_id": installation_id,
                "platform": "WEB",
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        return response.json()

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def reauth_owner(self):
        self.bearer(self.owner_tokens["access_token"])
        response = self.client.post(
            "/auth/reauthenticate/",
            {"pin": "1111"},
            format="json",
        )
        assert response.status_code == 200, response.json()

    def test_role_change_is_visible_to_target_staff_with_cursor(self):
        self.bearer(self.staff_tokens["access_token"])
        initial = self.client.get("/auth/invalidation-events/")
        assert initial.status_code == 200
        cursor = initial.json()["cursor"]

        self.reauth_owner()
        changed = self.client.patch(
            f"/manage/access/memberships/{self.staff_membership.id}/",
            {
                "expected_version": 1,
                "role": StaffRole.CASHIER,
                "reason": "operar caixa",
            },
            format="json",
        )
        assert changed.status_code == 200, changed.json()

        self.bearer(self.staff_tokens["access_token"])
        feed = self.client.get(f"/auth/invalidation-events/?after={cursor}")

        assert feed.status_code == 200, feed.json()
        assert len(feed.json()["results"]) == 1
        event = feed.json()["results"][0]
        assert event["event_type"] == AccessInvalidationType.MEMBERSHIP_CHANGED
        assert event["metadata"]["role"] == StaffRole.CASHIER
        assert feed.json()["cursor"] == event["id"]

        empty = self.client.get(
            f"/auth/invalidation-events/?after={feed.json()['cursor']}"
        )
        assert empty.status_code == 200
        assert empty.json()["results"] == []

    def test_device_trust_change_is_visible_to_session_bound_to_device(self):
        self.bearer(self.staff_tokens["access_token"])
        me = self.client.get("/auth/me/")
        assert me.status_code == 200
        device_id = me.json()["device"]["id"]
        cursor = self.client.get("/auth/invalidation-events/").json()["cursor"]

        self.reauth_owner()
        changed = self.client.patch(
            f"/manage/access/devices/{device_id}/",
            {"trust_state": DeviceTrustState.TRUSTED},
            format="json",
        )
        assert changed.status_code == 200, changed.json()

        self.bearer(self.staff_tokens["access_token"])
        feed = self.client.get(f"/auth/invalidation-events/?after={cursor}")
        assert feed.status_code == 200
        assert any(
            item["event_type"] == AccessInvalidationType.DEVICE_CHANGED
            and item["metadata"]["trust_state"] == DeviceTrustState.TRUSTED
            for item in feed.json()["results"]
        )

    def test_revoked_session_is_rejected_by_api_even_without_consuming_feed(self):
        target_session = StaffSession.objects.get(
            id=self.staff_tokens["session_id"],
        )

        self.reauth_owner()
        response = self.client.post(
            f"/manage/access/sessions/{target_session.id}/revoke/",
            {"reason": "lost terminal"},
            format="json",
        )
        assert response.status_code == 200

        event = AccessInvalidationEvent.objects.get(
            session=target_session,
            event_type=AccessInvalidationType.SESSION_REVOKED,
        )
        assert event.reason == "lost terminal"

        self.bearer(self.staff_tokens["access_token"])
        denied = self.client.get("/auth/invalidation-events/")
        assert denied.status_code == 401
        assert denied.json()["code"] == "SESSION_REVOKED"
