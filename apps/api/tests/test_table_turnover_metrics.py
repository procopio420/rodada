"""Deterministic, multi-Venue Spec 004 TABLE-005 report regressions."""
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.hospitality.models import Table, TableOccupancy
from modules.ordering.models import Order, Tab
from modules.venue.models import Venue


class TableTurnoverMetricsTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Venue A", slug="metrics-venue-a", business_day_cutoff_hour=4)
        self.foreign = Venue.objects.create(name="Venue B", slug="metrics-venue-b", business_day_cutoff_hour=4)
        self.staff = StaffMember.objects.create(display_name="Gerente", login_identifier="metrics-manager")
        self.staff.set_pin("4321")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {
            "venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": "4321", "installation_id": "metrics-test-installation", "platform": "WEB",
        }, format="json")
        assert login.status_code == 200, login.json()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])

    def visit(self, venue, label, *, started_at, released_at=None, cleaning_started_at=None, ready_at=None):
        table = Table.objects.create(venue=venue, label=label)
        occupancy = TableOccupancy.objects.create(table=table, generation=1)
        TableOccupancy.objects.filter(pk=occupancy.pk).update(
            started_at=started_at, released_at=released_at,
            cleaning_started_at=cleaning_started_at, ready_at=ready_at,
        )
        return table

    def order(self, venue, source, when, status="CONFIRMED"):
        tab = Tab.objects.create(venue=venue)
        order = Order.objects.create(tab=tab, source=source, status=status)
        Order.objects.filter(pk=order.pk).update(confirmed_at=when)

    def report(self, day):
        response = self.client.get("/management/table-turnover/", {"start": day, "end": day})
        assert response.status_code == 200, response.json()
        return response.json()

    def test_canonical_timings_coverage_and_guest_vs_staff(self):
        tz = ZoneInfo("America/Sao_Paulo")
        started = datetime(2026, 10, 14, 19, 0, tzinfo=tz)
        released = started + timedelta(hours=2)
        self.visit(self.venue, "Mesa 1", started_at=started, released_at=released,
                   cleaning_started_at=released + timedelta(minutes=10),
                   ready_at=released + timedelta(minutes=15))
        self.visit(self.venue, "Mesa 2", started_at=started, released_at=released)
        self.visit(self.venue, "Mesa 3", started_at=started)
        self.visit(self.foreign, "Segredo", started_at=started, released_at=released,
                   cleaning_started_at=released, ready_at=released)
        self.order(self.venue, "GUEST", released)
        self.order(self.venue, "GUEST", released)
        self.order(self.venue, "STAFF", released)
        self.order(self.venue, "CASHIER", released)
        self.order(self.venue, "GUEST", released, status="CANCELLED")
        self.order(self.foreign, "GUEST", released)
        report = self.report("2026-10-14")
        assert report["summary"]["started"] == 3
        assert report["summary"]["released"] == 2
        assert report["summary"]["ready"] == 1
        occupancy = report["summary"]["timings"]["occupancy"]
        assert occupancy == {"eligible": 2, "observed": 2, "missing": 0, "invalid": 0, "mean_seconds": 7200}
        cleaning = report["summary"]["timings"]["cleaning"]
        assert cleaning == {"eligible": 2, "observed": 1, "missing": 1, "invalid": 0, "mean_seconds": 300}
        assert report["summary"]["timings"]["wait_to_clean"]["mean_seconds"] == 600
        assert report["summary"]["timings"]["release_to_ready"]["mean_seconds"] == 900
        assert report["summary"]["orders"] == {
            "guest": 2, "staff": 2, "cancelled": 1, "unknown_source": 0,
            "denominator": 4, "guest_percent": 50.0,
        }
        assert len(report["tables"]) == 3
        assert all(row["label"] != "Segredo" for row in report["tables"])

    def test_cutoff_boundary_and_late_cleaning(self):
        tz = ZoneInfo("America/Sao_Paulo")
        early = datetime(2026, 10, 15, 3, 59, tzinfo=tz)
        start = early - timedelta(hours=1)
        self.visit(self.venue, "A", started_at=start, released_at=early,
                   cleaning_started_at=early + timedelta(minutes=4),
                   ready_at=early + timedelta(minutes=6))
        day = self.report("2026-10-14")
        assert day["summary"]["released"] == 1
        assert day["summary"]["ready"] == 0
        assert day["summary"]["timings"]["release_to_ready"]["mean_seconds"] == 360
        next_day = self.report("2026-10-15")
        assert next_day["summary"]["released"] == 0
        assert next_day["summary"]["ready"] == 1
        assert next_day["summary"]["timings"]["release_to_ready"]["mean_seconds"] is None

    def test_bad_chronology_and_no_observations_are_not_zero_durations(self):
        tz = ZoneInfo("America/Sao_Paulo")
        t = datetime(2026, 10, 14, 21, tzinfo=tz)
        self.visit(self.venue, "A", started_at=t, released_at=t - timedelta(minutes=1),
                   cleaning_started_at=t + timedelta(minutes=1), ready_at=t + timedelta(minutes=2))
        data = self.report("2026-10-14")["summary"]
        assert data["timings"]["occupancy"]["invalid"] == 1
        assert data["timings"]["occupancy"]["mean_seconds"] is None
        assert data["orders"]["guest_percent"] is None

    def test_dst_cutoff_uses_venue_calendar(self):
        self.venue.timezone = "America/New_York"
        self.venue.save(update_fields=["timezone"])
        before = datetime(2026, 11, 1, 8, 59, tzinfo=dt_timezone.utc)
        after = datetime(2026, 11, 1, 9, 0, tzinfo=dt_timezone.utc)
        self.visit(self.venue, "A", started_at=before - timedelta(minutes=1), released_at=before)
        self.visit(self.venue, "B", started_at=after - timedelta(minutes=1), released_at=after)
        assert self.report("2026-10-31")["summary"]["released"] == 1
        assert self.report("2026-11-01")["summary"]["released"] == 1

    def test_requires_auth_scopes_venue_and_valid_dates(self):
        unauthorized = APIClient().get("/management/table-turnover/", {"start": "2026-10-14", "end": "2026-10-14"})
        assert unauthorized.status_code in (401, 403)
        assert self.client.get("/management/table-turnover/", {"start": "2026-10-16", "end": "2026-10-14"}).status_code == 400
        assert self.client.get("/management/table-turnover/", {"start": "2024-01-01", "end": "2026-10-14"}).status_code == 400
