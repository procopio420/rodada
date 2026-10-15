"""Spec025 signed Host matrix for the concurrently integrated Spec028 boundary.

Only pytest's disposable database. Proof is a native capability; manager sessions
and issued machine credentials remain Venue/Host scoped.
"""
import secrets
import uuid

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from modules.access.models import AgentCredential
from modules.documents_printing.models import PrintAgent, PrintPairingRequest
from modules.venue.models import Venue, VenueDomain
from tests.test_print_pairing import KEY, PREFIX, manager
from tests.test_spec025_host_security import SECRET, signed


@override_settings(RODADA_AGENT_PAIRING_SECRET=KEY, RODADA_BFF_HOST_SECRET=SECRET)
class PairingTenantHostTests(TestCase):
    def setUp(self):
        self.rows = []
        self.device = APIClient()
        for label in ("a", "b"):
            venue = Venue.objects.create(
                name=f"Disposable pairing {label}", slug=f"pairing-host-{label}",
                print_agents_enabled=True,
            )
            host = f"e2e{label}.rodada.bar"
            VenueDomain.objects.create(
                venue=venue, hostname=host, is_active=True, is_verified=True,
            )
            session, client = manager(venue)
            proof = "rpp_" + secrets.token_urlsafe(32)
            start = self.device.post(PREFIX + "pairing/start/", {
                "installation_id": str(uuid.uuid4()), "label": f"QA {label}", "proof": proof,
            }, format="json")
            self.assertEqual(start.status_code, 201)
            approve = client.post(PREFIX + "pairing/approve/", {
                "code": start.data["code"], "installation_id": start.data["installation_id"],
            }, format="json")
            self.assertEqual(approve.status_code, 200)
            status = self.device.post(PREFIX + "pairing/status/", {
                "request_id": start.data["request_id"], "proof": proof,
            }, format="json")
            self.assertEqual(status.status_code, 200)
            machine = APIClient()
            machine.credentials(HTTP_AUTHORIZATION="Bearer " + status.data["credential"])
            self.rows.append((venue, host, session, client, machine, approve.data["agent_id"], start.data))

    def test_manager_and_machine_signed_host_matrix_has_no_foreign_effects(self):
        for venue, host, _, client, machine, agent_id, _ in self.rows:
            for other_venue, target_host, _, _, _, foreign_id, _ in self.rows:
                own = venue == other_venue
                path = PREFIX
                response = client.get(path, **signed(target_host, path))
                self.assertEqual(response.status_code, 200 if own else 403)
                if own:
                    self.assertEqual([row["id"] for row in response.data["results"]], [agent_id])
                else:
                    self.assertEqual(response.data["code"], "VENUE_HOST_MISMATCH")
                    self.assertNotIn("results", response.data)
                path = PREFIX + "enabled/"
                response = client.post(path, {"enabled": True}, format="json",
                                       **signed(target_host, path, verb="POST"))
                self.assertEqual(response.status_code, 200 if own else 403)
                path = PREFIX + "me/heartbeat/"
                before = PrintAgent.objects.get(pk=agent_id).last_seen_at
                response = machine.post(path, {"protocol_version": 1, "version": "0.2.0"},
                                        format="json", **signed(target_host, path, verb="POST"))
                self.assertEqual(response.status_code, 200 if own else 403)
                if not own:
                    self.assertEqual(PrintAgent.objects.get(pk=agent_id).last_seen_at, before)
                path = PREFIX + foreign_id + "/revoke/"
                if not own:
                    response = client.post(path, {"reason": "Foreign ID must not revoke"},
                                           format="json", **signed(host, path, verb="POST"))
                    self.assertEqual(response.status_code, 404)
                    self.assertIsNone(PrintAgent.objects.get(pk=foreign_id).revoked_at)
        self.assertEqual(AgentCredential.objects.filter(revoked_at__isnull=True).count(), 2)

    def test_invalid_pairing_proof_rejected_on_both_hosts_without_credential(self):
        for _, _, _, _, _, _, started in self.rows:
            for _, target_host, *_ in self.rows:
                path = PREFIX + "pairing/status/"
                response = self.device.post(path, {
                    "request_id": started["request_id"],
                    "proof": "rpp_" + secrets.token_urlsafe(32),
                }, format="json", **signed(target_host, path, verb="POST"))
                self.assertEqual(response.status_code, 401)
                self.assertNotIn("credential", response.data)
        self.assertEqual(AgentCredential.objects.filter(revoked_at__isnull=True).count(), 2)

    def test_wrong_host_approval_cannot_consume_or_replay_pairing(self):
        for venue, own_host, _, client, _, _, _ in self.rows:
            other_host = next(row[1] for row in self.rows if row[0] != venue)
            start = self.device.post(PREFIX + "pairing/start/", {
                "installation_id": str(uuid.uuid4()), "label": "Disposable approval matrix",
                "proof": "rpp_" + secrets.token_urlsafe(32),
            }, format="json")
            self.assertEqual(start.status_code, 201)
            path = PREFIX + "pairing/approve/"
            body = {"code": start.data["code"], "installation_id": start.data["installation_id"]}
            before = AgentCredential.objects.count()
            denied = client.post(path, body, format="json",
                                 **signed(other_host, path, verb="POST"))
            self.assertEqual(denied.status_code, 403)
            self.assertIsNone(PrintPairingRequest.objects.get(pk=start.data["request_id"]).consumed_at)
            self.assertEqual(AgentCredential.objects.count(), before)
            allowed = client.post(path, body, format="json",
                                  **signed(own_host, path, verb="POST"))
            self.assertEqual(allowed.status_code, 200)
            self.assertEqual(allowed.data["venue_id"], str(venue.id))
            self.assertEqual(AgentCredential.objects.count(), before + 1)
            replay = client.post(path, body, format="json",
                                 **signed(own_host, path, verb="POST"))
            self.assertEqual(replay.status_code, 400)
            self.assertEqual(AgentCredential.objects.count(), before + 1)
