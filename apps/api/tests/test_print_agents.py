"""Spec 028 S1: real machine authentication and schema security regressions."""

import importlib.util
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from modules.access.agent_credentials import issue_credential, revoke_agent, token_digest
from modules.access.logging import redact_auth_secrets
from modules.access.models import (
    AgentCredential,
    DeviceRegistration,
    StaffMember,
    StaffSession,
    VenueStaffMembership,
)
from modules.access.services import hash_token
from modules.audit.models import AuditEvent
from modules.documents_printing.agent_contracts import validate_destination
from modules.documents_printing.agent_models import AgentState, PrinterTransport
from modules.documents_printing.agent_routes import configure_route
from modules.documents_printing.models import (
    AgentPrinterRoute,
    DiscoveredPrinter,
    PrintAgent,
    PrinterEndpoint,
    PrintPairingRequest,
)
from modules.venue.models import Venue

CONTRACT = "/printing/agents/v1/me/contract/"


def fixture():
    venue = Venue.objects.create(
        name="Synthetic Print Lab", slug="print-lab", print_agents_enabled=True
    )
    other = Venue.objects.create(name="Synthetic Other", slug="print-other")
    staff = StaffMember.objects.create(
        display_name="Synthetic Manager", login_identifier="print-manager"
    )
    member = VenueStaffMembership.objects.create(venue=venue, staff_member=staff, role="MANAGER")
    session = StaffSession.objects.create(
        venue=venue,
        staff_member=staff,
        membership=member,
        access_token_hash=hash_token("rat_synthetic"),
        access_expires_at=timezone.now() + timedelta(hours=1),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    device = DeviceRegistration.objects.create(
        venue=venue,
        installation_key_hash=token_digest("synthetic-installation"),
        platform="WINDOWS",
        trust_state="TRUSTED",
    )
    agent = PrintAgent.objects.create(
        venue=venue,
        device=device,
        paired_at=timezone.now(),
        installation_id=uuid.uuid4(),
        label="Synthetic Print PC",
    )
    printer = DiscoveredPrinter.objects.create(
        agent=agent,
        local_id="queue-1",
        label="Synthetic Queue",
        transport="TCP_LAN",
        last_seen_at=timezone.now(),
    )
    endpoint = PrinterEndpoint.objects.create(
        venue=venue, label="Synthetic Endpoint", adapter="FILE"
    )
    route = AgentPrinterRoute.objects.create(
        endpoint=endpoint,
        printer=printer,
        transport="TCP_LAN",
        destination="192.168.1.50",
        profile_id="generic-ascii",
    )
    return venue, other, session, agent, route


class AgentFoundationTests(TestCase):
    def setUp(self):
        self.venue, self.other, self.session, self.agent, self.route = fixture()
        self.raw = issue_credential(agent_id=self.agent.id, session=self.session)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.raw)

    def test_contract_is_scoped_without_delivery_or_secrets(self):
        response = self.client.get(CONTRACT, HTTP_X_VENUE_ID=str(self.other.id))
        assert response.status_code == 200
        assert response.json() == {
            "protocol_version": 1,
            "agent_id": str(self.agent.id),
            "venue_id": str(self.venue.id),
            "scope": "PRINT_AGENT_V1",
            "operations": ["contract", "activate", "heartbeat"],
            "delivery_enabled": False,
        }
        assert self.raw not in repr(response.data)
        assert AgentCredential.objects.get(agent=self.agent).token_hash == token_digest(self.raw)
        assert not StaffSession.objects.filter(access_token_hash=token_digest(self.raw)).exists()

    def test_signed_foreign_host_denied_own_host_and_native_allowed(self):
        import hashlib
        import hmac
        import time

        from django.test import override_settings

        from modules.venue.models import VenueDomain

        secret = "synthetic-host-assertion-key"
        for venue in (self.venue, self.other):
            hostname = venue.slug + ".rodada.bar"
            VenueDomain.objects.create(
                venue=venue, hostname=hostname, is_active=True, is_verified=True
            )
            timestamp = str(int(time.time()))
            signature = hmac.new(
                secret.encode(),
                f"{timestamp}\nGET\n{CONTRACT}\n{hostname}".encode(),
                hashlib.sha256,
            ).hexdigest()
            with override_settings(RODADA_BFF_HOST_SECRET=secret):
                response = self.client.get(
                    CONTRACT,
                    HTTP_X_RODADA_BFF_HOST=hostname,
                    HTTP_X_RODADA_BFF_TIME=timestamp,
                    HTTP_X_RODADA_BFF_SIGNATURE=signature,
                )
            assert response.status_code == (200 if venue == self.venue else 403)
        assert self.client.get(CONTRACT).status_code == 200

    def test_invalid_machine_tokens_are_denied(self):
        for raw in ("", "rpa_bad", "rpa_" + "x" * 43, "rat_synthetic", "rrt_fake"):
            self.client.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
            assert self.client.get(CONTRACT).status_code == 401

    def test_expired_token_is_denied(self):
        # Insert expired credential directly: timestamps must still form a valid lifetime.
        AgentCredential.objects.filter(agent=self.agent).update(revoked_at=timezone.now())
        raw = "rpa_" + "e" * 43
        expired = AgentCredential.objects.create(
            agent=self.agent,
            token_hash=token_digest(raw),
            expires_at=timezone.now() + timedelta(seconds=1),
        )
        # Expiry is immutable on PostgreSQL; advance the authentication clock instead.
        from unittest.mock import patch

        with patch(
            "modules.access.agent_credentials.timezone.now", return_value=expired.expires_at
        ):
            self.client.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
            assert self.client.get(CONTRACT).status_code == 401

    def test_rotation_invalidates_old_token_and_audits(self):
        new = issue_credential(agent_id=self.agent.id, session=self.session, rotate=True)
        assert self.client.get(CONTRACT).status_code == 401
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + new)
        assert self.client.get(CONTRACT).status_code == 200
        assert (
            AgentCredential.objects.filter(agent=self.agent, revoked_at__isnull=True).count() == 1
        )
        assert AuditEvent.objects.filter(event_type="print.agent_credential_rotated").count() == 1

    def test_duplicate_issue_denied_without_rotation(self):
        with pytest.raises(ValidationError):
            issue_credential(agent_id=self.agent.id, session=self.session)

    def test_revoke_is_idempotent_preserves_history_and_other_agents(self):
        device = DeviceRegistration.objects.create(
            venue=self.venue,
            installation_key_hash=token_digest("other-install"),
            platform="WINDOWS",
            trust_state="TRUSTED",
        )
        other = PrintAgent.objects.create(
            venue=self.venue,
            device=device,
            paired_at=timezone.now(),
            installation_id=uuid.uuid4(),
            label="Other PC",
        )
        raw = issue_credential(agent_id=other.id, session=self.session)
        for _ in range(2):
            revoke_agent(
                agent_id=self.agent.id, session=self.session, reason="Synthetic retirement"
            )
        assert self.client.get(CONTRACT).status_code == 401
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
        assert self.client.get(CONTRACT).status_code == 200
        assert AgentPrinterRoute.objects.filter(id=self.route.id).exists()
        assert AuditEvent.objects.filter(event_type="print.agent_revoked").count() == 1

    def test_revocation_possible_with_flag_off(self):
        Venue.objects.filter(id=self.venue.id).update(print_agents_enabled=False)
        assert self.client.get(CONTRACT).status_code == 403
        revoke_agent(agent_id=self.agent.id, session=self.session, reason="Flag disabled")
        assert self.client.get(CONTRACT).status_code == 401

    def test_flag_default_off_and_device_revocation_denies(self):
        assert self.other.print_agents_enabled is False
        DeviceRegistration.objects.filter(id=self.agent.device_id).update(trust_state="REVOKED")
        assert self.client.get(CONTRACT).status_code == 401

    def test_machine_cannot_escalate_into_staff_or_legacy_printing(self):
        for path in ("/printing/endpoints/", "/printing/jobs/", "/tabs/", "/access/devices/"):
            assert self.client.get(path).status_code in (401, 404)
        assert (
            self.client.post(
                "/printing/bridge/claim/",
                {"endpoint_ids": [str(self.route.endpoint_id)]},
                format="json",
            ).status_code
            == 401
        )
        assert (
            self.client.post(CONTRACT, {"scope": "staff.manage"}, format="json").status_code == 405
        )

    def test_staff_cannot_authenticate_as_machine(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer rat_synthetic")
        assert self.client.get(CONTRACT).status_code == 401
        assert self.client.get("/printing/endpoints/").status_code == 200

    def test_cross_venue_and_unprivileged_issue_revoke_denied(self):
        for role, venue in (("STAFF", self.venue), ("OWNER", self.other)):
            member = VenueStaffMembership.objects.create(
                venue=venue,
                staff_member=StaffMember.objects.create(
                    display_name="Synthetic Unprivileged", login_identifier=str(uuid.uuid4())
                ),
                role=role,
            )
            session = StaffSession.objects.create(
                venue=venue,
                staff_member=member.staff_member,
                membership=member,
                expires_at=timezone.now() + timedelta(hours=1),
            )
            with pytest.raises(PermissionDenied):
                issue_credential(agent_id=self.agent.id, session=session, rotate=True)
            with pytest.raises(PermissionDenied):
                revoke_agent(agent_id=self.agent.id, session=session, reason="Denied")
        assert self.client.get(CONTRACT).status_code == 200

    def test_route_cas_audit_and_destination_safety(self):
        args = {
            "route_id": self.route.id,
            "session": self.session,
            "expected_version": 1,
            "priority": 1,
            "profile_id": "generic-ascii",
            "destination": "192.168.1.51",
            "port": 9100,
        }
        route = configure_route(**args)
        assert route.version == 2 and route.enabled is False
        with pytest.raises(ValidationError):
            configure_route(**args)
        args.update(expected_version=2, destination="8.8.8.8")
        with pytest.raises(ValidationError):
            configure_route(**args)
        assert AuditEvent.objects.filter(event_type="print.agent_route_configured").count() == 1

    def test_constraints(self):
        for mutation in (
            lambda: PrintAgent.objects.create(
                installation_id=uuid.uuid4(), label="Invalid", venue=self.venue
            ),
            lambda: AgentCredential.objects.create(
                agent=self.agent,
                token_hash="x" * 64,
                scope="staff.manage",
                expires_at=timezone.now() + timedelta(days=1),
            ),
            lambda: DiscoveredPrinter.objects.create(
                agent=self.agent,
                local_id="queue-1",
                label="Duplicate",
                transport="TCP_LAN",
                last_seen_at=timezone.now(),
            ),
            lambda: AgentPrinterRoute.objects.filter(id=self.route.id).update(version=0),
            lambda: PrintPairingRequest.objects.create(
                agent=self.agent,
                code_hash="c" * 64,
                proof_hash="p" * 64,
                expires_at=timezone.now() - timedelta(seconds=1),
            ),
        ):
            with pytest.raises(IntegrityError), transaction.atomic():
                mutation()

    def test_state_layers_are_independent(self):
        assert self.agent.state == AgentState.OFFLINE
        self.agent.last_seen_at = timezone.now()
        assert self.agent.state == AgentState.ONLINE
        assert self.route.printer.health == "UNKNOWN"
        self.agent.last_seen_at -= timedelta(seconds=45)
        assert self.agent.state == AgentState.STALE
        self.agent.last_seen_at -= timedelta(seconds=90)
        assert self.agent.state == AgentState.OFFLINE

    def test_redaction(self):
        assert self.raw not in redact_auth_secrets("credential=" + self.raw)
        assert "rpp_test" not in redact_auth_secrets("rpp_test")


@pytest.mark.parametrize(
    "address,port",
    [
        ("8.8.8.8", 9100),
        ("127.0.0.1", 9100),
        ("169.254.169.254", 9100),
        ("0.0.0.0", 9100),
        ("printer.example", 9100),
        ("192.168.1.2", 80),
        ("::1", 9100),
        ("::ffff:192.168.1.2", 9100),
        ("192.168.1.2\n", 9100),
    ],
)
def test_network_safety(address, port):
    with pytest.raises(ValidationError):
        validate_destination("TCP_LAN", address, port)


def test_standalone_contract_matches_backend():
    path = Path(__file__).resolve().parents[2] / "printer-agent/rodada_printer_agent/contracts.py"
    spec = importlib.util.spec_from_file_location("printer_contracts", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert set(module.TransportKind) == set(PrinterTransport.values)
    assert set(module.AgentState) == set(AgentState.values)
    assert "PRINTED" not in module.SubmissionOutcome
    assert module.PrinterCapabilities(width_mm=80).cut == "UNSUPPORTED"


class AgentPostgresTests(TransactionTestCase):
    def setUp(self):
        assert connection.vendor == "postgresql", "Spec 028 security/races require PostgreSQL"
        self.venue, self.other, self.session, self.agent, self.route = fixture()

    def test_bulk_cross_tenant_and_identity_rewrites_are_rejected(self):
        for mutation in (
            lambda: PrintAgent.objects.filter(id=self.agent.id).update(venue=self.other),
            lambda: DeviceRegistration.objects.filter(id=self.agent.device_id).update(
                venue=self.other
            ),
            lambda: PrinterEndpoint.objects.filter(id=self.route.endpoint_id).update(
                venue=self.other
            ),
            lambda: DiscoveredPrinter.objects.filter(id=self.route.printer_id).update(
                agent=PrintAgent.objects.create(installation_id=uuid.uuid4(), label="Unpaired")
            ),
            lambda: AgentPrinterRoute.objects.create(
                endpoint=PrinterEndpoint.objects.create(
                    venue=self.other, label="Other", adapter="FILE"
                ),
                printer=self.route.printer,
                transport="TCP_LAN",
                profile_id="ascii",
                destination="192.168.1.1",
            ),
        ):
            with pytest.raises(IntegrityError), transaction.atomic():
                mutation()

    def test_credential_cannot_be_rebound_or_resurrected(self):
        issue_credential(agent_id=self.agent.id, session=self.session)
        credential = AgentCredential.objects.get(agent=self.agent)
        with pytest.raises(IntegrityError), transaction.atomic():
            AgentCredential.objects.filter(id=credential.id).update(scope="staff.manage")
        revoke_agent(agent_id=self.agent.id, session=self.session, reason="Retired")
        with pytest.raises(IntegrityError), transaction.atomic():
            AgentCredential.objects.filter(id=credential.id).update(revoked_at=None)
        with pytest.raises(IntegrityError), transaction.atomic():
            PrintAgent.objects.filter(id=self.agent.id).update(revoked_at=None)

    def test_concurrent_issue_creates_one_credential(self):
        barrier = Barrier(2)

        def worker(_):
            close_old_connections()
            try:
                session = StaffSession.objects.get(id=self.session.id)
                barrier.wait(timeout=10)
                try:
                    issue_credential(agent_id=self.agent.id, session=session)
                    return "issued"
                except ValidationError:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(worker, range(2))) == ["conflict", "issued"]
        assert (
            AgentCredential.objects.filter(agent=self.agent, revoked_at__isnull=True).count() == 1
        )
        assert AuditEvent.objects.filter(event_type="print.agent_credential_issued").count() == 1

    def test_concurrent_route_cas_one_winner(self):
        barrier = Barrier(2)

        def worker(priority):
            close_old_connections()
            try:
                session = StaffSession.objects.get(id=self.session.id)
                barrier.wait(timeout=10)
                try:
                    configure_route(
                        route_id=self.route.id,
                        session=session,
                        expected_version=1,
                        priority=priority,
                        profile_id="ascii",
                        destination="192.168.1.1",
                        port=9100,
                    )
                    return "updated"
                except ValidationError:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(worker, (1, 2))) == ["conflict", "updated"]
        assert AuditEvent.objects.filter(event_type="print.agent_route_configured").count() == 1

    def test_concurrent_rotation_and_revocation_leave_no_live_credential(self):
        issue_credential(agent_id=self.agent.id, session=self.session)
        barrier = Barrier(2)

        def worker(action):
            close_old_connections()
            try:
                session = StaffSession.objects.get(id=self.session.id)
                barrier.wait(timeout=10)
                if action == "revoke":
                    revoke_agent(
                        agent_id=self.agent.id, session=session, reason="Concurrent retirement"
                    )
                else:
                    from rest_framework.exceptions import AuthenticationFailed

                    try:
                        issue_credential(agent_id=self.agent.id, session=session, rotate=True)
                    except AuthenticationFailed:
                        pass  # Revocation acquired the agent lock first.
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(worker, ("rotate", "revoke")))
        assert (
            AgentCredential.objects.filter(agent=self.agent, revoked_at__isnull=True).count() == 0
        )
        assert AuditEvent.objects.filter(event_type="print.agent_revoked").count() == 1


class AgentMigrationTests(TransactionTestCase):
    def test_additive_migrations_reverse_and_reapply_with_legacy_data(self):
        from django.db.migrations.executor import MigrationExecutor

        assert connection.vendor == "postgresql", "Migration gate requires PostgreSQL"
        old = [
            ("documents_printing", "0005_kds_health"),
            ("access", "0003_access_invalidation_event"),
            ("venue", "0011_venue_guest_mutations_blocked_and_more"),
        ]
        executor = MigrationExecutor(connection)
        # The venue base is obtained from the actual additive migration dependency.
        from importlib import import_module

        venue_migration = import_module("modules.venue.migrations.0012_venue_print_agents_enabled")
        old[-1] = venue_migration.Migration.dependencies[0]
        latest = executor.loader.graph.leaf_nodes()
        try:
            executor.migrate(old)
            state = executor.loader.project_state(old).apps
            venue = state.get_model("venue", "Venue").objects.create(
                name="Legacy Lab", slug="legacy-lab"
            )
            endpoint = state.get_model("documents_printing", "PrinterEndpoint").objects.create(
                venue=venue, label="Legacy File", adapter="FILE"
            )
            MigrationExecutor(connection).migrate(latest)
            assert Venue.objects.get(id=venue.id).print_agents_enabled is False
            assert PrinterEndpoint.objects.get(id=endpoint.id).adapter == "FILE"
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM pg_trigger WHERE tgname='printing_tenant_guard'"
                )
                assert cursor.fetchone()[0] == 7
            MigrationExecutor(connection).migrate(old)
            state = MigrationExecutor(connection).loader.project_state(old).apps
            assert (
                state.get_model("documents_printing", "PrinterEndpoint")
                .objects.get(id=endpoint.id)
                .label
                == "Legacy File"
            )
        finally:
            MigrationExecutor(connection).migrate(latest)
