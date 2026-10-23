"""Spec033 AC-23: first browser-viewport receipt, not prep or human acknowledgment."""
import hashlib
import uuid
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import Product
from modules.ordering.models import Order, OrderItem, OrderSource, Tab
from modules.venue.calendar import business_date
from modules.venue.models import (
    AttendanceTelemetryDaily, AttendanceTelemetryReceipt, ProductionScreenReceipt, Venue,
)


class ProductionScreenObservationTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Station observation", slug="station-observation")
        self.other = Venue.objects.create(name="Other station", slug="other-station")
        staff = StaffMember.objects.create(display_name="Observer", login_identifier="screen-observer")
        staff.set_pin("1234")
        staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=staff, role=StaffRole.MANAGER,
        )
        self.client = APIClient()
        login = self.client.post("/auth/login/", {
            "venue_slug": self.venue.slug, "login_identifier": staff.login_identifier,
            "pin": "1234", "installation_id": "production-browser", "platform": "WEB",
        }, format="json")
        self.assertEqual(login.status_code, 200, login.json())
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.session_id = self.client.get("/auth/me/").json()["session"]["id"]

    def make_order(self, stations=("BAR",), *, key=None):
        tab = self.client.post("/tabs/", {
            "display_label": "Screen ack",
        }, format="json")
        self.assertEqual(tab.status_code, 201, tab.json())
        lines = []
        for station in stations:
            product = Product.objects.create(
                venue=self.venue, name=f"Screen {station} {uuid.uuid4()}",
                price_cents=100, fulfillment_station=station,
            )
            lines.append({"product_id": str(product.id), "quantity": 1})
        key = key or str(uuid.uuid4())
        result = self.client.post(f"/tabs/{tab.json()['id']}/orders/confirm/", {
            "idempotency_key": key, "lines": lines,
        }, format="json")
        self.assertEqual(result.status_code, 201, result.json())
        return result.json()["id"], key, tab.json()["id"]

    def observe(self, order_id, station="BAR"):
        return self.client.post("/production/screen-observations/", {
            "station": station, "order_ids": [order_id],
        }, format="json")

    def test_first_viewport_receipt_links_only_server_ingress_and_deduplicates(self):
        key = str(uuid.uuid4())
        event = {
            "event_id": str(uuid.uuid4()), "version": 2, "platform": "WEB",
            "event": "intent_started", "origin_session": self.session_id,
            "intent_ref": hashlib.sha256(key.encode()).hexdigest(),
        }
        self.assertEqual(self.client.post("/attendance/telemetry/", event, format="json").status_code, 202)
        order_id, _, tab_id = self.make_order(key=key)
        before = self.client.get(f"/tabs/{tab_id}/").json()
        first = self.observe(order_id)
        self.assertEqual(first.status_code, 202, first.json())
        self.assertEqual(first.json()["first_seen"], 1)
        again = self.observe(order_id)
        self.assertEqual(again.status_code, 202, again.json())
        self.assertEqual((again.json()["first_seen"], again.json()["duplicate"]), (0, 1))
        self.assertEqual(self.client.get(f"/tabs/{tab_id}/").json(), before)

        self.assertEqual(ProductionScreenReceipt.objects.filter(venue=self.venue).count(), 1)
        daily = AttendanceTelemetryDaily.objects.get(
            venue=self.venue, event="screen_bar", platform="WEB",
        )
        self.assertEqual((daily.count, daily.duration_observed), (1, 1))
        self.assertGreaterEqual(daily.duration_total_ms, 0)
        today = business_date(self.venue)
        report = self.client.get("/management/attendance-metrics/", {
            "start": today.isoformat(), "end": today.isoformat(),
        })
        self.assertEqual(report.status_code, 200, report.json())
        metric = report.json()["production_screen"]["BAR"]
        self.assertEqual((metric["eligible"], metric["observed"], metric["missing"]), (1, 1, 0))
        self.assertEqual((metric["latency_observed"], metric["latency_missing"]), (1, 0))
        self.assertIsNotNone(metric["mean_intent_ingest_to_screen_seconds"])
        self.assertNotIn(order_id, str(report.json()))
        self.assertNotIn(key, str(report.json()))
        self.assertNotIn(event["intent_ref"], str(report.json()))

    def test_missing_intent_receipt_is_missing_latency_not_fake_zero(self):
        order_id, _, _ = self.make_order()
        self.assertEqual(self.observe(order_id).status_code, 202)
        today = business_date(self.venue)
        report = self.client.get("/management/attendance-metrics/", {
            "start": today.isoformat(), "end": today.isoformat(),
        }).json()["production_screen"]["BAR"]
        self.assertEqual((report["eligible"], report["observed"]), (1, 1))
        self.assertEqual((report["latency_observed"], report["latency_missing"]), (0, 1))
        self.assertIsNone(report["mean_intent_ingest_to_screen_seconds"])

    def test_both_stations_are_independent_and_wrong_station_cannot_claim(self):
        order_id, _, _ = self.make_order(("BAR", "KITCHEN"))
        for station in ("BAR", "KITCHEN"):
            self.assertEqual(self.observe(order_id, station).json()["first_seen"], 1)
        today = business_date(self.venue)
        report = self.client.get("/management/attendance-metrics/", {
            "start": today.isoformat(), "end": today.isoformat(),
        }).json()["production_screen"]
        for station in ("BAR", "KITCHEN"):
            self.assertEqual((report[station]["eligible"], report[station]["observed"]), (1, 1))
        bar_only, _, _ = self.make_order()
        self.assertEqual(self.observe(bar_only, "KITCHEN").status_code, 404)
        self.assertEqual(ProductionScreenReceipt.objects.count(), 2)

    def test_tenant_unknown_order_and_mixed_batch_are_rejected_atomically(self):
        valid_id, _, _ = self.make_order()
        foreign_tab = Tab.objects.create(venue=self.other, display_label="Not accessible")
        foreign_order = Order.objects.create(tab=foreign_tab, source=OrderSource.STAFF)
        foreign_product = Product.objects.create(
            venue=self.other, name="Private product", price_cents=100,
            fulfillment_station="BAR",
        )
        OrderItem.objects.create(
            order=foreign_order, product=foreign_product, product_name_snapshot="Private",
            unit_price_cents=100, quantity=1, fulfillment_station_snapshot="BAR",
        )
        for ids in ([foreign_order.id], [uuid.uuid4()], [uuid.UUID(valid_id), foreign_order.id]):
            response = self.client.post("/production/screen-observations/", {
                "station": "BAR", "order_ids": [str(x) for x in ids],
            }, format="json")
            self.assertEqual(response.status_code, 404)
        self.assertFalse(ProductionScreenReceipt.objects.exists())

    def test_schema_auth_bounds_and_retention_do_not_mutate_order(self):
        order_id, _, _ = self.make_order()
        for payload in (
            {"station": "KITCHEN", "order_ids": [order_id]},
            {"station": "BAR", "order_ids": [order_id, order_id]},
            {"station": "BAR", "order_ids": [order_id], "staff_id": "private"},
            {"station": "BAR", "order_ids": []},
            {"station": "BAR", "order_ids": [order_id] * 21},
        ):
            self.assertNotEqual(self.client.post(
                "/production/screen-observations/", payload, format="json",
            ).status_code, 202)
        self.assertEqual(self.client.generic(
            "POST", "/production/screen-observations/", b" " * 8193,
            content_type="application/json",
        ).status_code, 413)
        self.client.credentials()
        self.assertEqual(self.client.post("/production/screen-observations/", {
            "station": "BAR", "order_ids": [order_id],
        }, format="json").status_code, 401)
        self.assertFalse(ProductionScreenReceipt.objects.exists())

    def test_old_first_receipts_are_pruned_without_losing_daily_aggregates(self):
        order_id, _, _ = self.make_order()
        self.assertEqual(self.observe(order_id).status_code, 202)
        receipt = ProductionScreenReceipt.objects.get()
        ProductionScreenReceipt.objects.filter(pk=receipt.pk).update(
            observed_at=timezone.now() - timedelta(days=8),
        )
        call_command("prune_attendance_telemetry", batch_size=10, max_batches=1)
        self.assertFalse(ProductionScreenReceipt.objects.exists())
        daily = AttendanceTelemetryDaily.objects.get(event="screen_bar")
        self.assertEqual(daily.count, 1)
        # A receipt pruned after 7 days cannot create another count for an old
        # order, even if a long-lived board renders the item again.
        Order.objects.filter(pk=order_id).update(
            confirmed_at=timezone.now() - timedelta(days=8),
        )
        self.assertEqual(self.observe(order_id).json()["expired"], 1)
        self.assertEqual(AttendanceTelemetryDaily.objects.get(event="screen_bar").count, 1)
