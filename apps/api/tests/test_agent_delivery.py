"""S3 confirmed document/lease/fencing on genuine PostgreSQL."""

import base64
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.agent_credentials import issue_credential
from modules.access.context import ActorContext
from modules.access.models import AgentCredential
from modules.catalog.models import Product
from modules.documents_printing import agent_delivery
from modules.documents_printing.models import (
    PrintAgent,
    PrintAttempt,
    PrintJob,
    StationPrinterBinding,
)
from modules.documents_printing.services import (
    claim_job,
    create_document,
    recover_expired,
    request_job,
)
from modules.ordering.models import Order, OrderItem, Tab
from tests.test_print_agents import fixture

PREFIX = "/printing/agents/v1/"


def setup_delivery():
    venue, other, session, agent, route = fixture()
    agent.version, agent.last_seen_at = "0.3.0", timezone.now()
    agent.save(update_fields=["version", "last_seen_at"])
    endpoint = route.endpoint
    endpoint.adapter = "AGENT"
    endpoint.save(update_fields=["adapter"])
    route.enabled, route.raw_escpos_verified, route.profile_id = True, True, "escpos-ascii-v1"
    route.save()
    raw = issue_credential(agent_id=agent.id, session=session)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
    actor = ActorContext.from_session(session)
    tab = Tab.objects.create(venue=venue, display_label="Synthetic Tab")
    order = Order.objects.create(tab=tab, source="STAFF", status="CONFIRMED")
    product = Product.objects.create(
        venue=venue, name="Synthetic item", price_cents=1000, fulfillment_station="BAR"
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name_snapshot=product.name,
        unit_price_cents=1000,
        quantity=1,
        fulfillment_station_snapshot="BAR",
        customization_snapshot={},
    )
    StationPrinterBinding.objects.create(endpoint=endpoint, station="BAR")
    document = create_document(
        tab_id=tab.id, kind="PRODUCTION_TICKET", source_id=order.id, station="BAR", actor=actor
    )
    job = request_job(document=document, endpoint=endpoint, key="synthetic-initial", actor=actor)
    return venue, other, session, agent, route, client, raw, job


class AgentDeliveryFixture(TestCase):
    def setUp(self):
        (
            self.venue,
            self.other,
            self.session,
            self.agent,
            self.route,
            self.client,
            self.raw,
            self.job,
        ) = setup_delivery()

    def claim(self, **extra):
        return self.client.post(
            PREFIX + "me/claim/", {"protocol_version": 1, **extra}, format="json"
        )

    def result(self, job, outcome="SPOOL_ACCEPTED"):
        return self.client.post(
            PREFIX + f"me/jobs/{job['job_id']}/result/",
            {
                **{key: job[key] for key in ("attempt_token", "route_id", "route_version")},
                "outcome": outcome,
            },
            format="json",
        )


class AgentDeliveryTests(AgentDeliveryFixture):
    def test_confirmed_document_claim_result_replay_never_marks_printed(self):
        claimed = self.claim()
        assert claimed.status_code == 200, claimed.data
        job = claimed.data["job"]
        assert job["job_id"] == str(self.job.id)
        content = base64.b64decode(job["content"])
        assert b"DOCUMENTO NAO FISCAL" in content and b"Synthetic item" in content
        assert b"\x1d" not in content
        assert self.claim().data["job"] is None
        assert self.result(job).data["accepted"] is True
        assert self.result(job).data["accepted"] is True
        assert self.result(job, "FAILED_RETRYABLE").data["accepted"] is False
        self.job.refresh_from_db()
        assert self.job.state == "SPOOL_ACCEPTED"
        attempt = PrintAttempt.objects.get(job=self.job)
        assert (
            attempt.agent_id == self.agent.id
            and attempt.route_id == self.route.id
            and attempt.route_version == 1
        )
        assert Order.objects.get(pk=self.job.document.source_id).status == "CONFIRMED"

    def test_expiry_is_uncertain_and_never_reclaimed(self):
        job = self.claim().data["job"]
        PrintJob.objects.filter(pk=self.job.pk).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        assert self.result(job).data["accepted"] is False
        self.job.refresh_from_db()
        assert self.job.state == "DELIVERY_UNCERTAIN"
        assert self.claim().data["job"] is None
        recover_expired()
        assert PrintAttempt.objects.filter(job=self.job).count() == 1

    def test_no_client_endpoint_or_foreign_route(self):
        assert self.claim(endpoint_ids=[str(self.route.endpoint_id)]).status_code == 400
        claimed = self.claim().data["job"]
        claimed["route_id"] = str(uuid.uuid4())
        assert self.result(claimed).status_code == 404
        assert self.client.post(
            "/printing/bridge/claim/",
            {"endpoint_ids": [str(self.route.endpoint_id)]},
            format="json",
        ).status_code in (401, 403)

    def test_unverified_or_stale_cannot_claim(self):
        self.route.raw_escpos_verified = False
        self.route.save(update_fields=["raw_escpos_verified"])
        assert self.claim().data["job"] is None
        self.route.raw_escpos_verified = True
        self.route.save(update_fields=["raw_escpos_verified"])
        PrintAgent.objects.filter(pk=self.agent.pk).update(
            last_seen_at=timezone.now() - timedelta(minutes=2)
        )
        assert self.claim().data["job"] is None

    def test_legacy_claim_cannot_take_agent_endpoint(self):
        assert claim_job([self.route.endpoint_id]) is None
        self.job.refresh_from_db()
        assert self.job.state == "QUEUED"

    def test_discovery_rejects_venue_injection_or_duplicate_identity(self):
        row = {
            "local_id": "queue-x",
            "label": "Synthetic queue",
            "queue_name": "Queue X",
            "transport": "WINDOWS_DRIVER",
            "driver_name": "Synthetic",
            "health": "UNKNOWN",
        }
        response = self.client.post(
            PREFIX + "me/discovery/", {"protocol_version": 1, "printers": [row]}, format="json"
        )
        assert response.status_code == 200, response.data
        assert (
            self.client.post(
                PREFIX + "me/discovery/",
                {"protocol_version": 1, "printers": [row], "venue_id": str(self.other.id)},
                format="json",
            ).status_code
            == 400
        )
        assert (
            self.client.post(
                PREFIX + "me/discovery/",
                {"protocol_version": 1, "printers": [row, row]},
                format="json",
            ).status_code
            == 400
        )


class AgentClaimRaceTests(TransactionTestCase):
    def test_concurrent_poll_receives_only_one_attempt(self):
        assert connection.vendor == "postgresql"
        _, _, _, agent, _, _, _, job = setup_delivery()
        credential_id = AgentCredential.objects.get(agent=agent).id
        barrier = Barrier(2)

        def claim():
            close_old_connections()
            try:
                identity = PrintAgent.objects.get(pk=agent.id)
                barrier.wait(timeout=10)
                return agent_delivery.claim(identity, credential_id)["job"]
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))
        assert sum(result is not None for result in results) == 1
        assert PrintAttempt.objects.filter(job=job).count() == 1


class AgentDeliverySecurityTests(AgentDeliveryFixture):
    def manager_client(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer rat_synthetic")
        return client

    def route_values(self):
        return {
            "id": str(self.route.id),
            "endpoint_id": str(self.route.endpoint_id),
            "printer_id": str(self.route.printer_id),
            "printer_fingerprint": agent_delivery.printer_fingerprint(self.route.printer),
            "expected_version": self.route.version,
            "transport": "TCP_LAN",
            "profile_id": "escpos-ascii-v1",
            "destination": self.route.destination,
            "port": 9100,
            "enabled": True,
            "raw_escpos_verified": True,
        }

    def test_cas_and_inflight_route_change_do_not_reassign_attempt(self):
        claimed = self.claim().data["job"]
        values = self.route_values()
        values["enabled"] = False
        manager = self.manager_client()
        changed = manager.post(PREFIX + "routes/", values, format="json")
        assert changed.status_code == 200, changed.data
        assert changed.data["version"] == 2
        assert manager.post(PREFIX + "routes/", values, format="json").status_code == 400
        assert self.result(claimed).data["accepted"] is True
        assert PrintAttempt.objects.get(job=self.job).route_version == 1

    def test_raw_and_private_network_authorization_negative(self):
        manager, values = self.manager_client(), self.route_values()
        values["raw_escpos_verified"] = False
        assert manager.post(PREFIX + "routes/", values, format="json").status_code == 400
        values["raw_escpos_verified"] = True
        for destination in ("8.8.8.8", "127.0.0.1", "169.254.169.254", "printer.example"):
            values["destination"] = destination
            assert manager.post(PREFIX + "routes/", values, format="json").status_code == 400

    def test_revoked_or_expired_credential_cannot_deliver(self):
        from modules.access.agent_credentials import revoke_agent

        claimed = self.claim().data["job"]
        revoke_agent(agent_id=self.agent.id, session=self.session, reason="Synthetic revocation")
        assert self.claim().status_code == 401
        assert self.result(claimed).status_code == 401
        self.job.refresh_from_db()
        assert self.job.state == "SENDING"
        PrintJob.objects.filter(pk=self.job.pk).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        recover_expired()
        self.job.refresh_from_db()
        assert self.job.state == "DELIVERY_UNCERTAIN"

    def test_staff_cannot_manage_and_machine_cannot_use_manager_operations(self):
        from tests.test_print_pairing import manager

        _, staff = manager(self.venue, "STAFF")
        assert staff.get(PREFIX + "routes/").status_code == 403
        assert staff.post(PREFIX + "routes/", self.route_values(), format="json").status_code == 403
        assert self.client.get(PREFIX + "routes/").status_code in (401, 403)
        assert self.manager_client().post(
            PREFIX + "me/claim/", {"protocol_version": 1}, format="json"
        ).status_code in (401, 403)

    def test_agent_cannot_read_foreign_jobs_or_configuration(self):
        from modules.access.models import DeviceRegistration
        from tests.test_print_pairing import manager

        self.other.print_agents_enabled = True
        self.other.save(update_fields=["print_agents_enabled"])
        session, other_manager = manager(self.other)
        device = DeviceRegistration.objects.create(
            venue=self.other,
            installation_key_hash="f" * 64,
            platform="WINDOWS",
            trust_state="TRUSTED",
        )
        agent = PrintAgent.objects.create(
            venue=self.other,
            device=device,
            paired_at=timezone.now(),
            last_seen_at=timezone.now(),
            installation_id=uuid.uuid4(),
            label="Synthetic foreign",
            version="0.3.0",
        )
        raw = issue_credential(agent_id=agent.pk, session=session)
        foreign = APIClient()
        foreign.credentials(HTTP_AUTHORIZATION="Bearer " + raw)
        assert (
            foreign.post(PREFIX + "me/claim/", {"protocol_version": 1}, format="json").data["job"]
            is None
        )
        claimed = self.claim().data["job"]
        body = {key: claimed[key] for key in ("attempt_token", "route_id", "route_version")}
        assert (
            foreign.post(
                PREFIX + f"me/jobs/{self.job.id}/result/",
                {**body, "outcome": "SPOOL_ACCEPTED"},
                format="json",
            ).status_code
            == 404
        )
        assert (
            other_manager.post(PREFIX + "routes/", self.route_values(), format="json").status_code
            == 404
        )

    def test_attempt_owner_cannot_be_rewritten_by_bulk_write(self):
        from django.db import IntegrityError, transaction

        self.claim()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PrintAttempt.objects.filter(job=self.job).update(
                agent=None, route=None, route_version=None
            )


class AgentPipelineTests(AgentDeliveryFixture):
    def test_real_api_worker_to_mock_windows_spool_preserves_original_job(self):
        import copy
        from unittest.mock import MagicMock

        from rodada_printer_agent.delivery import DeliveryCycle
        from rodada_printer_agent.transports import Transports
        from rodada_printer_agent.worker import InstallationState, Worker

        from modules.documents_printing.models import DiscoveredPrinter

        self.route.enabled = False
        self.route.save(update_fields=["enabled"])
        row = {
            "local_id": "queue:synthetic",
            "label": "Synthetic Windows",
            "queue_name": "Synthetic Windows",
            "transport": "WINDOWS_DRIVER",
            "driver_name": "Synthetic driver",
            "health": "UNKNOWN",
        }
        printer = DiscoveredPrinter.objects.create(
            agent=self.agent, last_seen_at=timezone.now(), **row
        )
        saved = agent_delivery.save_route(
            self.session,
            {
                "printer_id": printer.id,
                "printer_fingerprint": agent_delivery.printer_fingerprint(printer),
                "endpoint_id": self.route.endpoint_id,
                "expected_version": 0,
                "transport": "WINDOWS_DRIVER",
                "profile_id": "windows-driver-v1",
                "destination": row["queue_name"],
                "port": 9100,
                "enabled": True,
                "raw_escpos_verified": False,
            },
        )
        windows = MagicMock()
        windows.enumerate.return_value = [row]
        windows.rendered.return_value = "42"

        class Store:
            state = InstallationState(credential=self.raw, activated=True)

            def load(inner):
                return copy.deepcopy(inner.state)

            def save(inner, state):
                inner.state = copy.deepcopy(state)

            def diagnostic(inner, state):
                pass

        client = self.client

        class Api:
            def post(inner, path, body, token=""):
                response = client.post(PREFIX + path, body, format="json")
                assert response.status_code == 200, response.data
                return response.data

        store = Store()
        Worker(store, Api(), DeliveryCycle(Transports(windows))).tick("Synthetic service")
        self.job.refresh_from_db()
        assert self.job.state == "SPOOL_ACCEPTED"
        assert self.job.attempt_count == 1 and store.state.pending_result == {}
        windows.raw.assert_not_called()
        windows.rendered.assert_called_once()
        assert "DOCUMENTO NÃO FISCAL" in windows.rendered.call_args.args[1]
        assert "Synthetic item" in windows.rendered.call_args.args[1]
        assert PrintAttempt.objects.get(job=self.job).route_id == uuid.UUID(saved["id"])


class DiscoveryConfigurationRaceTests(TransactionTestCase):
    def test_discovery_change_while_route_approval_waits_rejects_stale_attestation(self):
        from threading import Event
        from unittest.mock import patch

        from rest_framework.exceptions import ValidationError

        from modules.documents_printing.models import DiscoveredPrinter

        _venue, _, session, agent, route, _, _, _ = setup_delivery()
        values = {
            "id": route.id,
            "endpoint_id": route.endpoint_id,
            "printer_id": route.printer_id,
            "printer_fingerprint": agent_delivery.printer_fingerprint(route.printer),
            "expected_version": 1,
            "transport": "TCP_LAN",
            "profile_id": "escpos-ascii-v1",
            "destination": route.destination,
            "port": 9100,
            "enabled": True,
            "raw_escpos_verified": True,
        }
        read, changed = Event(), Event()
        original = agent_delivery.get_object_or_404

        def get(*args, **kwargs):
            found = original(*args, **kwargs)
            if isinstance(found, DiscoveredPrinter) and "agent__venue_id" in kwargs:
                read.set()
                assert changed.wait(10)
            return found

        def configure():
            close_old_connections()
            try:
                with patch.object(agent_delivery, "get_object_or_404", get):
                    try:
                        agent_delivery.save_route(session, values)
                    except ValidationError as error:
                        return str(error)
                return "unexpected acceptance"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            configured = pool.submit(configure)
            assert read.wait(10)
            try:
                agent_delivery.discover(
                    agent,
                    AgentCredential.objects.get(agent=agent).id,
                    [
                        {
                            "local_id": route.printer.local_id,
                            "label": "Changed synthetic printer",
                            "queue_name": "Changed queue",
                            "driver_name": "Changed driver",
                            "transport": "TCP_LAN",
                            "health": "UNKNOWN",
                        }
                    ],
                )
            finally:
                changed.set()
            assert "observation changed" in configured.result(timeout=10)
        route.refresh_from_db()
        assert route.enabled is False and route.raw_escpos_verified is False and route.version == 2
