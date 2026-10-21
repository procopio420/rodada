"""S4: distinct installations and actual PostgreSQL locks, never two send tokens."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone

from modules.access.agent_credentials import issue_credential, revoke_agent
from modules.access.models import AgentCredential, DeviceRegistration
from modules.documents_printing import agent_delivery
from modules.documents_printing.models import (
    AgentPrinterRoute,
    DiscoveredPrinter,
    PrintAgent,
    PrintAttempt,
    PrintJob,
)
from modules.documents_printing.services import recover_expired
from tests.test_agent_delivery import setup_delivery


def peer(venue, session, endpoint):
    device = DeviceRegistration.objects.create(
        venue=venue, installation_key_hash=uuid.uuid4().hex, platform="WINDOWS",
        trust_state="TRUSTED",
    )
    agent = PrintAgent.objects.create(
        venue=venue, device=device, paired_at=timezone.now(), installation_id=uuid.uuid4(),
        label="Synthetic second PC", version="0.3.0", last_seen_at=timezone.now(),
    )
    printer = DiscoveredPrinter.objects.create(
        agent=agent, local_id="independently-assigned-lan", label="Synthetic LAN",
        transport="TCP_LAN", queue_name="192.168.1.50", last_seen_at=timezone.now(),
    )
    route = AgentPrinterRoute.objects.create(
        endpoint=endpoint, printer=printer, transport="TCP_LAN", destination="192.168.1.50",
        profile_id="escpos-ascii-v1", raw_escpos_verified=True, enabled=True,
    )
    issue_credential(agent_id=agent.id, session=session)
    return agent, route, AgentCredential.objects.get(agent=agent).id


class MultiagentTests(TransactionTestCase):
    def setUp(self):
        assert connection.vendor == "postgresql"
        self.venue, _, self.session, self.a, self.route, _, _, self.job = setup_delivery()
        self.ca = AgentCredential.objects.get(agent=self.a).id
        self.b, self.rb, self.cb = peer(self.venue, self.session, self.route.endpoint)

    def claim(self, agent=None, credential=None):
        return agent_delivery.claim(agent or self.a, credential or self.ca)["job"]

    def report(self, claimed, outcome, agent=None, credential=None):
        return agent_delivery.result(agent or self.a, credential or self.ca, self.job.id, {
            "attempt_token": claimed["attempt_token"], "route_id": claimed["route_id"],
            "route_version": claimed["route_version"], "outcome": outcome,
        })

    def test_distinct_installations_race_for_same_endpoint_one_token(self):
        barrier = Barrier(2)

        def run(values):
            close_old_connections()
            try:
                agent, credential = values
                barrier.wait(timeout=10)
                return self.claim(agent, credential)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [(self.a, self.ca), (self.b, self.cb)]))
        assert sum(r is not None for r in results) == 1
        assert PrintAttempt.objects.filter(job=self.job).count() == 1
        winner = next(r for r in results if r)
        attempt = PrintAttempt.objects.get(job=self.job)
        assert str(attempt.token) == winner["attempt_token"]
        assert attempt.agent_id in (self.a.id, self.b.id)
        assert self.claim(self.b, self.cb) is None and self.claim() is None

    def test_pre_send_failure_can_fail_over_with_new_fence(self):
        first = self.claim()
        assert self.report(first, "FAILED_RETRYABLE")["accepted"]
        PrintJob.objects.filter(pk=self.job.pk).update(available_at=timezone.now())
        second = self.claim(self.b, self.cb)
        assert second and second["attempt_token"] != first["attempt_token"]
        assert not self.report(first, "SPOOL_ACCEPTED")["accepted"]
        assert self.report(second, "SPOOL_ACCEPTED", self.b, self.cb)["accepted"]
        assert PrintAttempt.objects.filter(job=self.job).count() == 2

    def test_uncertain_expiry_never_fails_over(self):
        first = self.claim()
        PrintJob.objects.filter(pk=self.job.pk).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
        recover_expired()
        assert self.claim(self.b, self.cb) is None
        assert not self.report(first, "SPOOL_ACCEPTED")["accepted"]
        assert PrintAttempt.objects.filter(job=self.job).count() == 1

    def test_absent_or_offline_queue_is_not_claimable_then_recovers(self):
        agent_delivery.discover(self.a, self.ca, [])
        assert self.claim() is None
        assert self.claim(self.b, self.cb) is not None
        self.route.printer.refresh_from_db()
        assert self.route.printer.health == "OFFLINE"

    def test_revoked_owner_does_not_transfer_inflight_attempt(self):
        import pytest
        from rest_framework.exceptions import AuthenticationFailed

        first = self.claim()
        revoke_agent(agent_id=self.a.id, session=self.session, reason="Synthetic retirement")
        with pytest.raises(AuthenticationFailed):
            self.report(first, "SPOOL_ACCEPTED")
        assert self.claim(self.b, self.cb) is None

    def test_peer_cannot_submit_owners_result(self):
        import pytest
        from django.http import Http404

        first = self.claim()
        with pytest.raises(Http404):
            self.report(first, "SPOOL_ACCEPTED", self.b, self.cb)
        assert self.report(first, "SPOOL_ACCEPTED")["accepted"]

    def test_manager_can_enable_second_route_through_cas_api(self):
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer rat_synthetic")
        values = agent_delivery.route_payload(self.rb)
        values.pop("version")
        values.update(expected_version=1, printer_fingerprint=agent_delivery.printer_fingerprint(self.rb.printer))
        response = client.post("/printing/agents/v1/routes/", values, format="json")
        assert response.status_code == 200, response.data
        assert response.data["version"] == 2
        assert AgentPrinterRoute.objects.filter(endpoint=self.route.endpoint, enabled=True).count() == 2

    def test_discovery_reappearance_restores_only_its_assigned_queue(self):
        agent_delivery.discover(self.a, self.ca, [])
        assert self.claim() is None
        printer = self.route.printer
        agent_delivery.discover(self.a, self.ca, [{
            "local_id": printer.local_id, "label": printer.label,
            "queue_name": printer.queue_name, "transport": printer.transport,
            "driver_name": printer.driver_name, "health": "UNKNOWN",
        }])
        assert self.claim() is not None
        assert self.claim(self.b, self.cb) is None
