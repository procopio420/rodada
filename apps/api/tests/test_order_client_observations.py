"""Best-effort telemetry must never become order authority or leak another Venue."""
import io
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.ordering.models import Order, OrderClientObservation, Tab
from modules.venue.models import Venue


class OrderClientObservationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.venue = Venue.objects.create(name="Observation fixture", slug="observation-fixture")
        self.foreign = Venue.objects.create(name="Other fixture", slug="other-observation-fixture")
        staff = StaffMember.objects.create(display_name="Fixture", login_identifier="observation-fixture")
        staff.set_pin("1234")
        staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(venue=self.venue,
            staff_member=staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {"venue_slug": self.venue.slug,
            "login_identifier": staff.login_identifier, "pin": "1234",
            "installation_id": "observation-fixture", "platform": "WEB"}, format="json")
        assert login.status_code == 200
        self.token = login.json()["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)
        self.session = self.client.get("/auth/me/").json()["session"]["id"]
        self.batch = {"origin_venue": str(self.venue.id), "origin_session": self.session,
            "events": [self.event()]}

    def event(self, **extra):
        return {"event_id": str(uuid.uuid4()), "intent_ref": "a" * 64,
            "kind": "INTENT_SAVED", "channel": "WEB", "ux_version": "033-ux2",
            "app_version": "web-033", **extra}

    def post(self, batch=None):
        return self.client.post("/attendance-observations/", batch or self.batch, format="json")

    def test_dedup_conflict_and_batch_rollback_do_not_change_order_facts(self):
        tab = Tab.objects.create(venue=self.venue)
        before = list(Tab.objects.values())
        assert self.post().status_code == 204
        assert self.post().status_code == 204
        assert OrderClientObservation.objects.count() == 1
        conflict = {**self.batch["events"][0], "app_version": "another-build"}
        assert self.post({**self.batch, "events": [self.event(), conflict]}).status_code == 409
        assert OrderClientObservation.objects.count() == 1
        assert list(Tab.objects.values()) == before
        assert not Order.objects.filter(tab=tab).exists()

    def test_origin_capability_auth_schema_and_bounds(self):
        assert self.post({**self.batch, "origin_venue": str(self.foreign.id)}).status_code == 403
        assert self.post({**self.batch, "origin_session": str(uuid.uuid4())}).status_code == 403
        for event in [self.event(note="never accept free text"), self.event(intent_ref="original-intent-key"),
                self.event(duration_ms=4), self.event(kind="ATTEMPT_FINISHED"),
                self.event(kind="ATTEMPT_FINISHED", attempt_id=str(uuid.uuid4()),
                    outcome="CONFIRMED", reason="UNCERTAIN"),
                self.event(app_version="URL/with/PII")]:
            assert self.post({**self.batch, "events": [event]}).status_code == 400
        assert self.post({**self.batch, "events": [self.event() for _ in range(9)]}).status_code == 400
        oversized = self.client.generic("POST", "/attendance-observations/", b" " * 8193,
            content_type="application/json")
        assert oversized.status_code == 413
        self.membership.capability_overrides = {"deny": ["order.confirm"]}
        self.membership.save(update_fields=["capability_overrides"])
        assert self.post().status_code == 403
        self.client.credentials()
        assert self.post().status_code == 401
        assert not OrderClientObservation.objects.exists()

    def test_aggregates_only_retained_same_venue_without_correlation_ids(self):
        event = self.event(kind="ATTEMPT_FINISHED", attempt_id=str(uuid.uuid4()),
            outcome="CONFIRMED", duration_ms=120, recovery=True)
        assert self.post({**self.batch, "events": [event]}).status_code == 204
        assert self.post().status_code == 204
        foreign = OrderClientObservation.objects.first()
        foreign.pk = None
        foreign.venue = self.foreign
        foreign.save()
        old = OrderClientObservation.objects.get(venue=self.venue, kind="INTENT_SAVED")
        OrderClientObservation.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=8))
        response = self.client.get("/management/attendance-observations/")
        assert response.status_code == 200
        report = response.json()
        assert report["source"] == "CLIENT_REPORTED_BEST_EFFORT"
        assert len(report["groups"]) == 1
        assert report["groups"][0]["mean_duration_ms"] == 120
        assert report["groups"][0]["events"] == report["groups"][0]["intents"] == 1
        assert all(key not in response.content.decode() for key in ("intent_ref", "event_id", "attempt_id", self.session))
        output = io.StringIO()
        call_command("prune_order_observations", batch_size=1, max_batches=1, stdout=output)
        assert OrderClientObservation.objects.count() == 2
        assert "Deleted 1" in output.getvalue()

    def test_attempt_coverage_unknown_preflight_and_throttle(self):
        events = [self.event(kind="ATTEMPT_FINISHED", attempt_id=str(uuid.uuid4()),
                    outcome="UNKNOWN", reason="UNCERTAIN", duration_ms=None),
            self.event(kind="ATTEMPT_FINISHED", attempt_id=str(uuid.uuid4()),
                    outcome="PREFLIGHT", reason="SESSION_CHANGED", duration_ms=12)]
        assert self.post({**self.batch, "events": events}).status_code == 204
        for _ in range(119):
            assert self.post().status_code == 204
        assert self.post().status_code == 429
        assert OrderClientObservation.objects.count() == 3


# Actual PostgreSQL only: unique-index races cannot be proven on SQLite.
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase


@skipUnless(connection.vendor == "postgresql", "PostgreSQL concurrency gate")
class OrderObservationConcurrencyTests(TransactionTestCase):
    setUp = OrderClientObservationTests.setUp
    event = OrderClientObservationTests.event

    def test_concurrent_replays_deduplicate_and_conflicts_fail_closed(self):
        def run_pair(batches):
            barrier = Barrier(2)

            def send(batch):
                close_old_connections()
                try:
                    client = APIClient()
                    client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)
                    barrier.wait(timeout=10)
                    return client.post("/attendance-observations/", batch, format="json").status_code
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                return list(executor.map(send, batches))

        assert run_pair([self.batch, self.batch]) == [204, 204]
        assert OrderClientObservation.objects.count() == 1
        event = self.event()
        first = {**self.batch, "events": [event]}
        other = {**self.batch, "events": [{**event, "app_version": "another-build"}]}
        assert sorted(run_pair([first, other])) == [204, 409]
        assert OrderClientObservation.objects.count() == 2
        assert Order.objects.count() == Tab.objects.count() == 0
