import logging
from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.capabilities import Capability
from modules.access.context import ActorContext
from modules.access.logging import CredentialRedactionFilter, redact_auth_secrets
from modules.access.models import (
    DeviceRegistration,
    DeviceTrustState,
    StaffMember,
    StaffRole,
    StaffSession,
    VenueStaffMembership,
)
from modules.access.services import AccessServiceError, authorize_replayed_command
from modules.venue.models import Venue


class ReplayedCommandAuthorizationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Replay Bar", slug="replay-bar")
        self.staff = StaffMember.objects.create(
            display_name="Manager",
            login_identifier="replay-manager",
        )
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            role=StaffRole.MANAGER,
        )
        self.device = DeviceRegistration.objects.create(
            venue=self.venue,
            installation_key_hash="replay-device",
            platform="ANDROID",
            trust_state=DeviceTrustState.TRUSTED,
        )
        self.session = StaffSession.objects.create(
            venue=self.venue,
            staff_member=self.staff,
            membership=self.membership,
            device=self.device,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_replay_reloads_current_capabilities_instead_of_captured_role(self):
        initial = authorize_replayed_command(
            session_id=self.session.id,
            required_capability=Capability.REFUND_CREATE,
        )
        assert isinstance(initial, ActorContext)

        self.membership.role = StaffRole.STAFF
        self.membership.version += 1
        self.membership.save(update_fields=["role", "version"])

        with pytest.raises(AccessServiceError) as exc:
            authorize_replayed_command(
                session_id=self.session.id,
                required_capability=Capability.REFUND_CREATE,
            )

        assert exc.value.code == "CAPABILITY_REQUIRED"
        assert exc.value.status_code == 403

    def test_replay_reloads_device_revocation(self):
        self.device.trust_state = DeviceTrustState.REVOKED
        self.device.revoked_at = timezone.now()
        self.device.save(update_fields=["trust_state", "revoked_at"])

        with pytest.raises(AccessServiceError) as exc:
            authorize_replayed_command(
                session_id=self.session.id,
                required_capability=Capability.ORDER_CONFIRM,
            )

        assert exc.value.code == "DEVICE_REVOKED"


class StaffCredentialNamespaceTests(TestCase):
    def test_guest_like_bearer_cannot_authenticate_as_staff(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer rgt_guest-session-token")

        response = client.get("/auth/me/")

        assert response.status_code == 401
        assert response.json()["code"] == "AUTH_REQUIRED"


class CredentialRedactionTests(TestCase):
    def test_redacts_pin_access_refresh_and_authorization_header(self):
        raw = (
            'payload={"pin":"1234","access":"rat_secret-access",'
            '"refresh":"rrt_secret-refresh"} '
            "Authorization: Bearer rat_header-secret pin=9876"
        )

        redacted = redact_auth_secrets(raw)

        assert "1234" not in redacted
        assert "9876" not in redacted
        assert "rat_secret-access" not in redacted
        assert "rrt_secret-refresh" not in redacted
        assert "rat_header-secret" not in redacted
        assert "[REDACTED_PIN]" in redacted
        assert "[REDACTED_TOKEN]" in redacted

    def test_logging_filter_rewrites_message_before_handler_output(self):
        record = logging.LogRecord(
            name="rodada.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg='login pin=%s token=%s',
            args=("2468", "rat_super-secret"),
            exc_info=None,
        )

        assert CredentialRedactionFilter().filter(record)
        message = record.getMessage()

        assert "2468" not in message
        assert "rat_super-secret" not in message
        assert "[REDACTED_PIN]" in message
        assert "[REDACTED_TOKEN]" in message
