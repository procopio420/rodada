import secrets
from datetime import date, datetime, timezone as tz
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.ordering.models import Tab
from modules.venue.models import Venue


class NightTabHistoryTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="History fixture", slug="history-fixture",
            timezone="America/Sao_Paulo", business_day_cutoff_hour=6)
        staff = StaffMember.objects.create(display_name="Atendimento", login_identifier="history-staff")
        pin = str(secrets.randbelow(900000) + 100000)
        staff.set_pin(pin)
        staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=StaffRole.STAFF)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {"venue_slug": self.venue.slug,
            "login_identifier": staff.login_identifier, "pin": pin,
            "installation_id": "history-fixture", "platform": "ANDROID"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])

    def test_current_night_respects_cutoff_closure_time_and_tenant(self):
        # At 01:00 local, the business date still belongs to the preceding night.
        now = datetime(2026, 10, 18, 4, tzinfo=tz.utc)
        lower = datetime(2026, 10, 17, 9, tzinfo=tz.utc)
        wanted = Tab.objects.create(venue=self.venue, state="CLOSED", closed_at=lower)
        Tab.objects.create(venue=self.venue, state="CLOSED", closed_at=datetime(2026, 10, 17, 8, 59, tzinfo=tz.utc))
        Tab.objects.create(venue=self.venue, state="CLOSED", closed_at=datetime(2026, 10, 18, 9, tzinfo=tz.utc))
        Tab.objects.create(venue=self.venue, state="OPEN")
        foreign = Venue.objects.create(name="Other fixture", slug="other-history")
        Tab.objects.create(venue=foreign, state="CLOSED", closed_at=now)
        cancelled = Tab.objects.create(venue=self.venue, state="CANCELLED")
        event = AuditEvent.objects.create(venue=self.venue, entity_type="Tab",
            entity_id=str(cancelled.id), event_type="tab.cancelled")
        AuditEvent.objects.filter(pk=event.pk).update(occurred_at=now)
        from modules.venue.calendar import business_date
        self.assertEqual(business_date(self.venue, now), date(2026, 10, 17))
        with patch("modules.venue.calendar.business_date", return_value=date(2026, 10, 17)):
            response = self.client.get("/tabs/?history_day=current")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["history_business_date"], "2026-10-17")
        self.assertEqual({row["id"] for row in response.json()["results"]}, {str(wanted.id), str(cancelled.id)})
        self.assertEqual(self.client.get("/tabs/?history_day=2026-10-17").json()["results"], response.json()["results"])

    def test_history_pagination_keeps_explicit_business_date(self):
        instant = datetime(2026, 10, 17, 20, tzinfo=tz.utc)
        Tab.objects.bulk_create([Tab(venue=self.venue, state="CLOSED", closed_at=instant) for _ in range(201)])
        first = self.client.get("/tabs/?history_day=2026-10-17&summary=true").json()
        self.assertEqual(first["next_offset"], 200)
        second = self.client.get(f"/tabs/?history_day={first['history_business_date']}&summary=true&offset=200").json()
        ids = [row["id"] for row in first["results"] + second["results"]]
        self.assertEqual(len(ids), 201)
        self.assertEqual(len(set(ids)), 201)
        self.assertIsNone(second["next_offset"])

    def test_history_requires_auth_and_valid_non_active_query(self):
        self.assertNotIn("history_business_date", self.client.get("/tabs/").json())
        self.assertEqual(self.client.get("/tabs/?history_day=bad").status_code, 400)
        self.assertEqual(self.client.get("/tabs/?history_day=current&active=true").status_code, 400)
        self.client.credentials()
        self.assertEqual(self.client.get("/tabs/?history_day=current").status_code, 401)
