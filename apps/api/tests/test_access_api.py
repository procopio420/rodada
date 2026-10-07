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


class StaffSwitchAndReauthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Bar do Aderlan", slug="aderlan-switch")

        self.ana = StaffMember.objects.create(display_name="Ana", login_identifier="ana-switch")
        self.ana.set_pin("1111")
        self.ana.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.ana,
            role=StaffRole.CASHIER,
        )

        self.bruno = StaffMember.objects.create(display_name="Bruno", login_identifier="bruno-switch")
        self.bruno.set_pin("2222")
        self.bruno.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.bruno,
            role=StaffRole.MANAGER,
        )

        response = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.ana.login_identifier,
                "pin": "1111",
                "installation_id": "shared-terminal-1",
                "platform": "WEB",
                "friendly_label": "Caixa compartilhado",
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        self.ana_tokens = response.json()

    def bearer(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def trust_current_device(self):
        device = DeviceRegistration.objects.get(venue=self.venue)
        device.trust_state = DeviceTrustState.TRUSTED
        device.save(update_fields=["trust_state"])
        return device

    def test_untrusted_device_cannot_fast_switch(self):
        self.bearer(self.ana_tokens["access_token"])

        response = self.client.post(
            "/auth/switch-operator/",
            {"login_identifier": self.bruno.login_identifier, "pin": "2222"},
            format="json",
        )

        assert response.status_code == 403
        assert response.json()["code"] == "TRUSTED_DEVICE_REQUIRED"

    def test_trusted_device_switches_actor_and_supersedes_previous_session(self):
        device = self.trust_current_device()
        self.bearer(self.ana_tokens["access_token"])

        response = self.client.post(
            "/auth/switch-operator/",
            {"login_identifier": self.bruno.login_identifier, "pin": "2222"},
            format="json",
        )

        assert response.status_code == 200, response.json()
        bruno_tokens = response.json()
        assert bruno_tokens["staff"]["id"] == str(self.bruno.id)
        assert bruno_tokens["device"]["id"] == str(device.id)
        assert bruno_tokens["role"] == StaffRole.MANAGER

        self.bearer(self.ana_tokens["access_token"])
        stale = self.client.get("/auth/me/")
        assert stale.status_code == 401
        assert stale.json()["code"] == "SESSION_SUPERSEDED"

        self.bearer(bruno_tokens["access_token"])
        current = self.client.get("/auth/me/")
        assert current.status_code == 200
        assert current.json()["staff"]["id"] == str(self.bruno.id)

        event = AuditEvent.objects.get(venue=self.venue, event_type="auth.operator_switched")
        assert event.actor_staff_id == self.bruno.id
        assert event.device_id == device.id
        assert event.metadata["previous_staff_id"] == str(self.ana.id)

    def test_wrong_switch_pin_keeps_current_operator_active(self):
        self.trust_current_device()
        self.bearer(self.ana_tokens["access_token"])

        response = self.client.post(
            "/auth/switch-operator/",
            {"login_identifier": self.bruno.login_identifier, "pin": "9999"},
            format="json",
        )

        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"

        current = self.client.get("/auth/me/")
        assert current.status_code == 200
        assert current.json()["staff"]["id"] == str(self.ana.id)

    def test_switch_pin_failures_are_throttled_without_replacing_operator(self):
        self.trust_current_device()
        self.bearer(self.ana_tokens["access_token"])

        for _ in range(5):
            response = self.client.post(
                "/auth/switch-operator/",
                {"login_identifier": self.bruno.login_identifier, "pin": "9999"},
                format="json",
            )
            assert response.status_code == 401

        response = self.client.post(
            "/auth/switch-operator/",
            {"login_identifier": self.bruno.login_identifier, "pin": "9999"},
            format="json",
        )
        assert response.status_code == 429
        assert response.json()["code"] == "AUTH_THROTTLED"

        current = self.client.get("/auth/me/")
        assert current.status_code == 200
        assert current.json()["staff"]["id"] == str(self.ana.id)

    def test_reauthentication_requires_current_actors_own_pin(self):
        self.bearer(self.ana_tokens["access_token"])

        wrong = self.client.post(
            "/auth/reauthenticate/",
            {"pin": "2222"},
            format="json",
        )
        assert wrong.status_code == 401
        assert wrong.json()["code"] == "INVALID_CREDENTIALS"

        response = self.client.post(
            "/auth/reauthenticate/",
            {"pin": "1111"},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["reauthenticated_at"]
        assert response.json()["valid_until"]

        event = AuditEvent.objects.get(venue=self.venue, event_type="auth.reauth_succeeded")
        assert event.actor_staff_id == self.ana.id
