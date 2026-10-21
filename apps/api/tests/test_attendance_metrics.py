"""Spec033 timings: tenant, authorization, coverage and read-only proof."""
from datetime import UTC, date, datetime, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import Product
from modules.dispatch.models import DispatchTask
from modules.management.attendance_metrics import attendance_metrics
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


class AttendanceMetricsTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="A", slug="observed-a", business_day_cutoff_hour=4)
        self.foreign = Venue.objects.create(name="B", slug="observed-b")
        staff = StaffMember.objects.create(display_name="Metrics", login_identifier="observed-manager")
        staff.set_pin("4321")
        staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(venue=self.venue,
            staff_member=staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {"venue_slug": self.venue.slug,
            "login_identifier": staff.login_identifier, "pin": "4321",
            "installation_id": "observed-metrics-test", "platform": "WEB"}, format="json")
        assert login.status_code == 200
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.when = datetime(2026, 10, 21, 12, tzinfo=UTC)

    def report(self, **extra):
        return self.client.get("/management/attendance-metrics/",
            {"start": "2026-10-21", "end": "2026-10-21", **extra})

    def item(self, venue, *, accepted=20, ready=60, station="BAR", confirmed=None):
        tab = Tab.objects.create(venue=venue)
        order = Order.objects.create(tab=tab, source="STAFF")
        when = confirmed or self.when
        Order.objects.filter(pk=order.pk).update(confirmed_at=when)
        product, _ = Product.objects.get_or_create(venue=venue, name="Snapshot", defaults={
            "price_cents": 100, "fulfillment_station": "KITCHEN"})
        item = OrderItem.objects.create(order=order, product=product, product_name_snapshot="Snapshot",
            unit_price_cents=100, quantity=1, fulfillment_station_snapshot=station)
        OrderItem.objects.filter(pk=item.pk).update(
            accepted_at=None if accepted is None else when + timedelta(seconds=accepted),
            ready_at=None if ready is None else when + timedelta(seconds=ready))

    def task(self, venue, kind, *, source="", completed=60, tab=None):
        task = DispatchTask.objects.create(venue=venue, task_type=kind,
            requested_tab=tab, completion_source=source)
        DispatchTask.objects.filter(pk=task.pk).update(created_at=self.when,
            ready_at=self.when + timedelta(seconds=10), claimed_at=self.when + timedelta(seconds=15),
            completed_at=None if completed is None else self.when + timedelta(seconds=completed))

    def test_coverage_station_cutoff_and_constant_queries(self):
        self.item(self.venue)
        self.item(self.venue, accepted=None, ready=None)
        self.item(self.venue, accepted=-1, ready=-1)
        self.item(self.venue, station="", accepted=0, ready=0)
        self.item(self.foreign, accepted=999, ready=999)
        self.item(self.venue, confirmed=self.when.replace(hour=6, minute=59, second=59))
        before = list(OrderItem.objects.values())
        with self.assertNumQueries(2):
            result = attendance_metrics(venue=self.venue, start=date(2026, 10, 21), end=date(2026, 10, 21))
        bucket = result["production"]["BAR"]["confirmed_to_accepted"]
        assert [bucket[k] for k in ("eligible", "observed", "missing", "invalid", "mean_seconds")] == [3, 1, 1, 1, 20]
        assert result["production"]["KITCHEN"]["confirmed_to_ready"]["eligible"] == 0
        assert result["production"]["UNKNOWN"]["confirmed_to_ready"]["mean_seconds"] == 0
        assert list(OrderItem.objects.values()) == before
        assert self.report().status_code == 200

    def test_provenance_and_foreign_tab_are_not_confirmed(self):
        tab = Tab.objects.create(venue=self.venue, closed_at=self.when + timedelta(seconds=90))
        foreign_tab = Tab.objects.create(venue=self.foreign, closed_at=self.when + timedelta(seconds=999))
        self.task(self.venue, "DELIVERY", source="MANUAL")
        self.task(self.venue, "DELIVERY", source="")
        self.task(self.foreign, "DELIVERY", source="MANUAL", completed=999)
        self.task(self.venue, "BILL_REQUEST", tab=tab)
        self.task(self.venue, "BILL_REQUEST", tab=foreign_tab)
        self.task(self.venue, "SERVICE_REQUEST", completed=None)
        first = self.report().json()
        assert first == self.report().json()
        assert first["manual_delivery"]["observed"] == 1
        assert first["manual_delivery"]["unverified"] == 1
        assert first["manual_delivery"]["mean_seconds"] == 50
        assert first["bill_to_tab_closed"]["mean_seconds"] == 90
        assert first["bill_to_tab_closed"]["missing"] == 1
        assert first["calls"]["SERVICE_REQUEST"]["created_to_completed"]["missing"] == 1
        assert "client_intent_started" in first["not_instrumented"]
        assert str(foreign_tab.pk) not in str(first)

    def test_permissions_and_anonymous(self):
        self.membership.role = StaffRole.STAFF
        self.membership.save(update_fields=["role"])
        assert self.report().status_code == 403
        self.client.credentials()
        assert self.report().status_code in (401, 403)

    def test_period_validation_and_no_write_methods(self):
        for values in ({"end": "2026-10-20"}, {"end": "2026-11-21"}, {"start": "oops"}):
            assert self.report(**values).status_code == 400
        assert self.report(end="2026-11-20").status_code == 200
        assert self.client.post("/management/attendance-metrics/", {}, format="json").status_code == 405
