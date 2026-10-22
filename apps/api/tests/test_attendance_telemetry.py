"""Spec033 client telemetry: authenticated tenant isolation and replay safety."""
import uuid
import hashlib
from django.test import TestCase
from rest_framework.test import APIClient
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.venue.models import Venue, AttendanceTelemetryDaily, AttendanceTelemetryReceipt
from modules.venue.calendar import business_date

class AttendanceTelemetryTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Telemetry", slug="telemetry-venue")
        staff = StaffMember.objects.create(display_name="Telemetry Staff", login_identifier="telemetry-staff")
        staff.set_pin("4321")
        staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {"venue_slug": self.venue.slug,
            "login_identifier": staff.login_identifier, "pin": "4321",
            "installation_id": "telemetry-test", "platform": "WEB"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.session_id = self.client.get("/auth/me/").json()["session"]["id"]

    def test_replay_is_idempotent_and_report_is_aggregated(self):
        payload = {"version": 1, "event_id": str(uuid.uuid4()), "platform": "WEB",
            "event": "confirm_acknowledged", "duration_ms": 1200}
        first = self.client.post("/attendance/telemetry/", payload, format="json")
        self.assertEqual(first.status_code, 202)
        second = self.client.post("/attendance/telemetry/", payload, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["duplicate"])
        row = AttendanceTelemetryDaily.objects.get(venue=self.venue)
        self.assertEqual((row.count, row.duration_observed, row.duration_total_ms), (1, 1, 1200))

    def test_rejects_arbitrary_dimensions_and_duration(self):
        payload = {"version": 1, "event_id": str(uuid.uuid4()), "platform": "WEB",
            "event": "confirm_failed", "duration_ms": 100, "staff_id": "secret"}
        self.assertEqual(self.client.post("/attendance/telemetry/", payload, format="json").status_code, 400)

    def test_replayed_uuid_with_different_payload_is_a_conflict(self):
        event_id = str(uuid.uuid4())
        first = {"version": 1, "event_id": event_id, "platform": "WEB",
            "event": "confirm_attempted"}
        self.assertEqual(self.client.post("/attendance/telemetry/", first, format="json").status_code, 202)
        different = {**first, "event": "confirm_failed"}
        self.assertEqual(self.client.post("/attendance/telemetry/", different, format="json").status_code, 409)
        self.assertEqual(AttendanceTelemetryDaily.objects.filter(venue=self.venue).count(), 1)
        self.assertEqual(AttendanceTelemetryDaily.objects.get(venue=self.venue).count, 1)

    def test_foreign_uuid_is_never_treated_as_local_replay(self):
        other = Venue.objects.create(name="Other telemetry", slug="telemetry-foreign")
        event_id = uuid.uuid4()
        AttendanceTelemetryReceipt.objects.create(
            id=event_id, venue=other, fingerprint="a" * 64)
        payload = {"version": 1, "event_id": str(event_id), "platform": "ANDROID",
            "event": "confirm_attempted"}
        self.assertEqual(self.client.post("/attendance/telemetry/", payload, format="json").status_code, 409)
        self.assertFalse(AttendanceTelemetryDaily.objects.filter(venue=self.venue).exists())

    def test_denies_large_payload_and_unauthenticated_requests(self):
        oversized = self.client.generic("POST", "/attendance/telemetry/", b" " * 8193,
            content_type="application/json")
        self.assertEqual(oversized.status_code, 413)
        self.client.credentials()
        payload = {"version": 1, "event_id": str(uuid.uuid4()), "platform": "WEB",
            "event": "confirm_attempted"}
        self.assertEqual(self.client.post("/attendance/telemetry/", payload, format="json").status_code, 401)
        self.assertFalse(AttendanceTelemetryDaily.objects.filter(venue=self.venue).exists())

    def v2(self, event="confirm_acknowledged", **fields):
        return {"version": 2, "event_id": str(uuid.uuid4()), "platform": "WEB",
            "event": event, "origin_session": self.session_id,
            "intent_ref": hashlib.sha256(b"independent-random-order-key").hexdigest(), **fields}

    def test_v2_correlates_only_by_ephemeral_hash_and_reports_observed_steps(self):
        started = self.v2("intent_started")
        acknowledged = self.v2(essential_steps=4, duration_ms=1500)
        self.assertEqual(self.client.post("/attendance/telemetry/", started, format="json").status_code, 202)
        self.assertEqual(self.client.post("/attendance/telemetry/", acknowledged, format="json").status_code, 202)
        self.assertEqual(self.client.post("/attendance/telemetry/", acknowledged, format="json").status_code, 200)
        receipts = list(AttendanceTelemetryReceipt.objects.values("intent_ref"))
        self.assertEqual({row["intent_ref"] for row in receipts}, {started["intent_ref"]})
        totals = AttendanceTelemetryDaily.objects.get(venue=self.venue, event="confirm_acknowledged")
        self.assertEqual((totals.count, totals.essential_steps_total, totals.essential_steps_observed,
            totals.duration_total_ms, totals.duration_observed), (1, 4, 1, 1500, 1))
        today = business_date(self.venue)
        response = self.client.get("/management/attendance-metrics/", {"start": today.isoformat(), "end": today.isoformat()})
        self.assertEqual(response.status_code, 200)
        results = response.json()["client_telemetry"]
        confirmed = next(x for x in results if x["event"] == "confirm_acknowledged")
        self.assertEqual(confirmed["essential_steps_eligible"], 1)
        self.assertEqual(confirmed["essential_steps_missing"], 0)
        self.assertEqual(confirmed["mean_essential_steps"], 4.0)
        self.assertNotIn("intent_ref", str(results))
        self.assertNotIn("origin_session", str(results))

    def test_missing_step_count_is_coverage_not_a_zero(self):
        self.assertEqual(self.client.post("/attendance/telemetry/", self.v2(duration_ms=500), format="json").status_code, 202)
        today = business_date(self.venue)
        response = self.client.get("/management/attendance-metrics/", {"start": today.isoformat(), "end": today.isoformat()})
        self.assertEqual(response.status_code, 200)
        confirmed = next(x for x in response.json()["client_telemetry"] if x["event"] == "confirm_acknowledged")
        self.assertEqual((confirmed["essential_steps_eligible"], confirmed["essential_steps_observed"],
            confirmed["essential_steps_missing"], confirmed["mean_essential_steps"]), (1, 0, 1, None))

    def test_v2_is_session_scoped_and_schema_bounded(self):
        for data in [
            self.v2(origin_session=str(uuid.uuid4())),
            self.v2(intent_ref="original-order-id"),
            self.v2(essential_steps=201),
            self.v2("confirm_attempted", essential_steps=2),
            {k: v for k, v in self.v2().items() if k != "intent_ref"},
            {**self.v2(), "staff_id": "PII"},
            {**self.v2(), "version": 1},
        ]:
            response = self.client.post("/attendance/telemetry/", data, format="json")
            self.assertEqual(response.status_code, 403 if data.get("origin_session") != self.session_id else 400, data)
        self.assertFalse(AttendanceTelemetryDaily.objects.filter(venue=self.venue).exists())
