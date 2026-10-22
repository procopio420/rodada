"""Spec033 client telemetry: authenticated tenant isolation and replay safety."""
import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.venue.models import Venue, AttendanceTelemetryDaily

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
