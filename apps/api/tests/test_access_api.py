from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import (
    DeviceRegistration,
    DeviceTrustState,
    MembershipStatus,
    StaffMember,
    StaffRole,
    VenueStaffMembership,
)
from modules.audit.models import AuditEvent
from modules.venue.models import Venue


class StaffAuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Bar do Aderlan", slug="aderlan")
        self.staff = StaffMember.objects.create(
            display_name="Ana",
            login_identifier="ana",
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.CASHIER,
        )
        self.login_payload = {
            "venue_slug": self.venue.slug,
            "login_identifier": "ANA",
            "pin": "1234",
            "installation_id": "android-installation-1",
            "platform": "ANDROID",
            "friendly_label": "Atendimento 1",
        }

    def login(self):
        response = self.client.post("/auth/login/", self.login_payload, format="json")
        assert response.status_code == 200, response.json()
        return response.json()

    def bearer(self, token: str):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_login_issues_opaque_tokens_and_me_exposes_effective_actor(self):
        payload = self.login()

        assert payload["access_token"].startswith("rat_")
        assert payload["refresh_token"].startswith("rrt_")
        assert payload["role"] == StaffRole.CASHIER
        assert "payment.collect" in payload["capabilities"]

        device = DeviceRegistration.objects.get(venue=self.venue)
        assert device.trust_state == DeviceTrustState.UNTRUSTED
        assert device.installation_key_hash != self.login_payload["installation_id"]

        self.bearer(payload["access_token"])
        response = self.client.get("/auth/me/")

        assert response.status_code == 200
        assert response.json()["staff"]["id"] == str(self.staff.id)
        assert response.json()["venue"]["id"] == str(self.venue.id)
        assert response.json()["membership"]["role"] == StaffRole.CASHIER

    def test_wrong_pin_is_throttled_after_repeated_failures(self):
        bad = {**self.login_payload, "pin": "0000"}

        for _ in range(5):
            response = self.client.post("/auth/login/", bad, format="json")
            assert response.status_code == 401
            assert response.json()["code"] == "INVALID_CREDENTIALS"

        response = self.client.post("/auth/login/", bad, format="json")

        assert response.status_code == 429
        assert response.json()["code"] == "AUTH_THROTTLED"
        assert response.json()["retry_after_seconds"] >= 1
        assert int(response["Retry-After"]) == response.json()["retry_after_seconds"]

    def test_refresh_rotates_tokens_and_old_refresh_token_stops_working(self):
        first = self.login()

        response = self.client.post(
            "/auth/refresh/",
            {"refresh_token": first["refresh_token"]},
            format="json",
        )
        assert response.status_code == 200
        second = response.json()

        assert second["access_token"] != first["access_token"]
        assert second["refresh_token"] != first["refresh_token"]

        stale = self.client.post(
            "/auth/refresh/",
            {"refresh_token": first["refresh_token"]},
            format="json",
        )
        assert stale.status_code == 401
        assert stale.json()["code"] == "AUTH_REQUIRED"

    def test_revoked_membership_blocks_existing_session_and_refresh(self):
        tokens = self.login()
        self.membership.status = MembershipStatus.REVOKED
        self.membership.save(update_fields=["status"])

        self.bearer(tokens["access_token"])
        response = self.client.get("/auth/me/")

        assert response.status_code == 403
        assert response.json()["code"] == "MEMBERSHIP_REVOKED"

        self.client.credentials()
        response = self.client.post(
            "/auth/refresh/",
            {"refresh_token": tokens["refresh_token"]},
            format="json",
        )

        assert response.status_code == 403
        assert response.json()["code"] == "MEMBERSHIP_REVOKED"

    def test_revoked_device_blocks_existing_session(self):
        tokens = self.login()
        device = DeviceRegistration.objects.get(venue=self.venue)
        device.trust_state = DeviceTrustState.REVOKED
        device.save(update_fields=["trust_state"])

        self.bearer(tokens["access_token"])
        response = self.client.get("/auth/me/")

        assert response.status_code == 403
        assert response.json()["code"] == "DEVICE_REVOKED"

    def test_lock_revokes_session_idempotently_for_future_requests(self):
        tokens = self.login()
        self.bearer(tokens["access_token"])

        response = self.client.post("/auth/lock/", {}, format="json")
        assert response.status_code == 204

        response = self.client.get("/auth/me/")
        assert response.status_code == 401
        assert response.json()["code"] == "SESSION_REVOKED"

    def test_cross_venue_login_requires_membership(self):
        other = Venue.objects.create(name="Outro Bar", slug="outro")
        response = self.client.post(
            "/auth/login/",
            {**self.login_payload, "venue_slug": other.slug},
            format="json",
        )

        assert response.status_code == 403
        assert response.json()["code"] == "MEMBERSHIP_REQUIRED"

    def test_audit_never_persists_pin_or_raw_tokens(self):
        tokens = self.login()
        serialized = "\n".join(
            str({"event_type": event.event_type, "metadata": event.metadata})
            for event in AuditEvent.objects.filter(venue=self.venue)
        )

        assert self.login_payload["pin"] not in serialized
        assert tokens["access_token"] not in serialized
        assert tokens["refresh_token"] not in serialized
