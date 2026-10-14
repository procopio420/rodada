"""Spec 028 S2: bootstrap, PoP, replay, host/capability and real DB approval races."""

import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from modules.access.models import AgentCredential, StaffMember, StaffSession, VenueStaffMembership
from modules.access.services import hash_token
from modules.audit.models import AuditEvent
from modules.documents_printing import pairing
from modules.documents_printing.models import PrintAgent, PrintPairingRequest
from modules.venue.models import Venue

PREFIX = "/printing/agents/v1/"
KEY = "synthetic-pairing-key-not-a-real-secret-028"


def manager(venue, role="MANAGER"):
    staff = StaffMember.objects.create(
        display_name="Synthetic operator", login_identifier=str(uuid.uuid4())
    )
    membership = VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role=role)
    raw = "rat_" + secrets.token_urlsafe(48)
    session = StaffSession.objects.create(
        venue=venue,
        staff_member=staff,
        membership=membership,
        access_token_hash=hash_token(raw),
        access_expires_at=timezone.now() + timedelta(hours=1),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
    return session, client


@override_settings(RODADA_AGENT_PAIRING_SECRET=KEY)
class PairingTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name="Synthetic Pairing Lab", slug="pairing-lab", print_agents_enabled=True
        )
        self.other = Venue.objects.create(
            name="Synthetic Other", slug="pairing-other", print_agents_enabled=True
        )
        self.session, self.manager = manager(self.venue)
        self.device = APIClient()
        self.proof = "rpp_" + secrets.token_urlsafe(32)
        self.installation = uuid.uuid4()

    def start(self):
        response = self.device.post(
            PREFIX + "pairing/start/",
            {
                "installation_id": str(self.installation),
                "label": "Synthetic PC",
                "proof": self.proof,
            },
            format="json",
        )
        assert response.status_code == 201, response.data
        return response.data

    def approve(self, started):
        response = self.manager.post(
            PREFIX + "pairing/approve/",
            {"code": started["code"], "installation_id": started["installation_id"]},
            format="json",
        )
        assert response.status_code == 200, response.data
        assert "credential" not in response.data
        return response.data

    def status(self, started, proof=None):
        return self.device.post(
            PREFIX + "pairing/status/",
            {"request_id": started["request_id"], "proof": proof or self.proof},
            format="json",
        )

    def test_full_pair_recovery_ack_heartbeat_revoke(self):
        started = self.start()
        assert self.start() == started  # Lost start response does not change identity/code.
        assert self.status(started).data["state"] == "PENDING_PAIRING"
        inspect = self.manager.post(
            PREFIX + "pairing/inspect/", {"code": started["code"]}, format="json"
        )
        assert inspect.status_code == 200 and inspect.data["venue_name"] == self.venue.name
        approved = self.approve(started)
        response = self.status(started)
        assert response["Cache-Control"] == "no-store"
        raw = response.data["credential"]
        assert self.status(started).data["credential"] == raw  # Lost status response recoverable.
        self.device.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
        assert self.device.post(PREFIX + "me/activate/", {}, format="json").status_code == 200
        assert self.device.post(PREFIX + "me/activate/", {}, format="json").status_code == 200
        self.device.credentials()
        assert "credential" not in self.status(started).data
        self.device.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
        heartbeat = self.device.post(
            PREFIX + "me/heartbeat/", {"protocol_version": 1, "version": "0.2.0"}, format="json"
        )
        assert heartbeat.status_code == 200 and heartbeat.data["state"] == "ONLINE"
        assert heartbeat.data["delivery_enabled"] is False
        assert PrintAgent.objects.get(id=approved["agent_id"]).version == "0.2.0"
        revoked = self.manager.post(
            PREFIX + approved["agent_id"] + "/revoke/",
            {"reason": "Synthetic retirement"},
            format="json",
        )
        assert revoked.status_code == 200
        assert (
            self.device.post(
                PREFIX + "me/heartbeat/", {"protocol_version": 1, "version": "0.2.0"}, format="json"
            ).status_code
            == 401
        )
        assert AuditEvent.objects.filter(event_type="print.agent_paired").count() == 1
        assert AgentCredential.objects.count() == 1
        assert StaffSession.objects.count() == 1

    def test_second_device_wrong_proof_and_installation_hijack_denied(self):
        started = self.start()
        self.approve(started)
        other_proof = "rpp_" + secrets.token_urlsafe(32)
        assert self.status(started, other_proof).status_code == 401
        assert (
            self.device.post(
                PREFIX + "pairing/start/",
                {
                    "installation_id": str(self.installation),
                    "label": "Malicious",
                    "proof": other_proof,
                },
                format="json",
            ).status_code
            == 401
        )
        assert PrintAgent.objects.count() == 1
        assert self.status(started).status_code == 200

    def test_unpaired_installation_proof_cannot_be_replaced(self):
        self.start()
        other_proof = "rpp_" + secrets.token_urlsafe(32)
        assert (
            self.device.post(
                PREFIX + "pairing/start/",
                {
                    "installation_id": str(self.installation),
                    "label": "Malicious",
                    "proof": other_proof,
                },
                format="json",
            ).status_code
            == 401
        )

    def test_approval_near_expiry_has_independent_recovery_window(self):
        started = self.start()
        request = PrintPairingRequest.objects.get(id=started["request_id"])
        approved_at = request.expires_at - timedelta(seconds=1)
        with patch("modules.documents_printing.pairing.timezone.now", return_value=approved_at):
            self.approve(started)
        with patch(
            "modules.documents_printing.pairing.timezone.now",
            return_value=approved_at + timedelta(seconds=11),
        ):
            recovered = self.status(started)
            assert recovered.status_code == 200 and recovered.data["state"] == "APPROVED"
        with patch(
            "modules.documents_printing.pairing.timezone.now",
            return_value=approved_at + timedelta(minutes=10),
        ):
            assert self.status(started).status_code == 410
        self.device.credentials(HTTP_AUTHORIZATION="Bearer " + recovered.data["credential"])
        assert self.device.post(PREFIX + "me/activate/", {}, format="json").status_code == 200
        self.device.credentials()
        with patch(
            "modules.documents_printing.pairing.timezone.now",
            return_value=approved_at + timedelta(minutes=11),
        ):
            assert self.status(started).data == {
                "state": "PAIRED",
                "agent_id": recovered.data["agent_id"],
            }

    def test_expiry_and_approval_replay_are_rejected(self):
        started = self.start()
        request = PrintPairingRequest.objects.get(id=started["request_id"])
        with patch(
            "modules.documents_printing.pairing.timezone.now", return_value=request.expires_at
        ):
            assert self.status(started).status_code == 410
            assert (
                self.manager.post(
                    PREFIX + "pairing/approve/",
                    {"code": started["code"], "installation_id": str(self.installation)},
                    format="json",
                ).status_code
                == 400
            )
        self.approve(started)
        assert (
            self.manager.post(
                PREFIX + "pairing/approve/",
                {"code": started["code"], "installation_id": str(self.installation)},
                format="json",
            ).status_code
            == 400
        )
        assert AgentCredential.objects.count() == 1

    def test_unprivileged_flag_off_and_wrong_confirmation_denied(self):
        started = self.start()
        _, staff = manager(self.venue, "STAFF")
        payload = {"code": started["code"], "installation_id": str(self.installation)}
        assert staff.post(PREFIX + "pairing/approve/", payload, format="json").status_code == 403
        assert (
            self.manager.post(
                PREFIX + "pairing/approve/",
                {**payload, "installation_id": str(uuid.uuid4())},
                format="json",
            ).status_code
            == 400
        )
        self.manager.post(PREFIX + "enabled/", {"enabled": False}, format="json")
        assert (
            self.manager.post(PREFIX + "pairing/approve/", payload, format="json").status_code
            == 403
        )
        assert AgentCredential.objects.count() == 0

    def test_cross_venue_manager_reads_and_revocation_denied(self):
        started = self.start()
        approved = self.approve(started)
        _, other = manager(self.other)
        assert other.get(PREFIX).data["results"] == []
        assert (
            other.post(
                PREFIX + approved["agent_id"] + "/revoke/", {"reason": "Denied"}, format="json"
            ).status_code
            == 404
        )
        assert (
            other.post(
                PREFIX + "pairing/approve/",
                {"code": started["code"], "installation_id": str(self.installation)},
                format="json",
            ).status_code
            == 400
        )

    def test_dedicated_key_required_and_tokens_not_used_for_bootstrap(self):
        with override_settings(RODADA_AGENT_PAIRING_SECRET=""):
            response = self.device.post(
                PREFIX + "pairing/start/",
                {"installation_id": str(self.installation), "label": "PC", "proof": self.proof},
                format="json",
            )
            assert response.status_code == 503
        assert self.manager.post(PREFIX + "pairing/start/", {}, format="json").status_code == 403

    def test_input_scope_and_client_clock_cannot_be_injected(self):
        started = self.start()
        self.approve(started)
        raw = self.status(started).data["credential"]
        self.device.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
        for payload in (
            {"protocol_version": 2, "version": "0.2.0"},
            {"protocol_version": 1, "version": "0.2.0", "venue_id": str(self.other.pk)},
            {"protocol_version": 1, "version": "0.2.0", "last_seen_at": timezone.now().isoformat()},
        ):
            assert (
                self.device.post(PREFIX + "me/heartbeat/", payload, format="json").status_code
                == 400
            )

    def test_brute_force_budget_persists_after_denial(self):
        for _ in range(60):
            response = self.manager.post(
                PREFIX + "pairing/inspect/", {"code": "A" * 16}, format="json"
            )
            assert response.status_code == 400
        assert (
            self.manager.post(
                PREFIX + "pairing/inspect/", {"code": "A" * 16}, format="json"
            ).status_code
            == 429
        )


@override_settings(RODADA_AGENT_PAIRING_SECRET=KEY)
class ConcurrentPairingTests(TransactionTestCase):
    def test_two_venues_can_only_approve_installation_once(self):
        assert connection.vendor == "postgresql"
        first = Venue.objects.create(name="Synthetic A", slug="pair-a", print_agents_enabled=True)
        second = Venue.objects.create(name="Synthetic B", slug="pair-b", print_agents_enabled=True)
        sessions = [manager(venue)[0].pk for venue in (first, second)]
        started = pairing.start_pairing(
            installation_id=uuid.uuid4(),
            label="Synthetic shared PC",
            proof="rpp_" + secrets.token_urlsafe(32),
        )
        barrier = Barrier(2)

        def approve(session_id):
            close_old_connections()
            try:
                session = StaffSession.objects.get(pk=session_id)
                barrier.wait(timeout=10)
                try:
                    pairing.approve_pairing(
                        code=started["code"],
                        installation_id=uuid.UUID(started["installation_id"]),
                        session=session,
                    )
                    return "approved"
                except ValidationError:
                    return "rejected"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(approve, sessions)) == ["approved", "rejected"]
        assert AgentCredential.objects.count() == 1
        assert AuditEvent.objects.filter(event_type="print.agent_paired").count() == 1
