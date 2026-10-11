"""Isolated test-money shift across canonical APIs and new closure contracts.

Clock-controlled server simulation, not Android process-death or hardware proof.
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TransactionTestCase
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffSession, VenueStaffMembership
from modules.cash.models import CashPoint, DailyClose
from modules.cash.services import (close_cash_shift, record_late_cash_correction,
                                  review_cash_discrepancy, start_cash_count)
from modules.catalog.models import Product
from modules.documents_printing.models import PrintJob
from modules.hospitality.models import Table
from modules.ordering.models import Order
from modules.venue.calendar import business_boundary
from modules.venue.models import Venue


class FourTrackShiftTests(TransactionTestCase):
    def call(self, client, path, body=None, expected=200):
        response = client.get(path) if body is None else client.post(path, body, format="json")
        self.assertEqual(response.status_code, expected, response.content)
        return response.json()

    def login(self):
        client = APIClient()
        login = self.call(client, "/auth/login/", {
            "venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": "2468", "installation_id": "four-track-test", "platform": "WEB"})
        client.credentials(HTTP_AUTHORIZATION="Bearer " + login["access_token"])
        self.call(client, "/auth/reauthenticate/", {"pin": "2468"})
        return client, ActorContext.from_session(StaffSession.objects.get(pk=login["session_id"]))

    def test_qr_mixed_order_retry_station_block_payment_and_immutable_close(self):
        self.venue = Venue.objects.create(name="Aderlan simulated", slug="four-track-shift",
            timezone="America/Sao_Paulo", business_day_cutoff_hour=4)
        self.staff = StaffMember.objects.create(display_name="Test manager", login_identifier="four-track-manager")
        self.staff.set_pin("2468")
        self.staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=self.staff, role="MANAGER")
        day = date(2026, 10, 10)
        start = business_boundary(self.venue, day) + timedelta(hours=2)
        boundary = business_boundary(self.venue, day + timedelta(days=1))
        with patch("django.utils.timezone.now", return_value=start):
            manager, actor = self.login()
            table = Table.objects.create(venue=self.venue, label="Test 01", guest_ordering_mode="DIRECT")
            bar = Product.objects.create(venue=self.venue, name="Test drink", price_cents=1000, fulfillment_station="BAR")
            kitchen = Product.objects.create(venue=self.venue, name="Test food", price_cents=2000, fulfillment_station="KITCHEN")
            point = CashPoint.objects.create(venue=self.venue, label="Test drawer")
            shift = self.call(manager, "/cash/shifts/", {"cash_point_id": str(point.pk),
                "opening_float_cents": 5000, "business_date": day.isoformat(), "idempotency_key": "shift"}, 201)
            guest = APIClient()
            qr = self.call(guest, "/guest/qr/resolve/", {"token": table.public_token}, 201)
            guest.credentials(HTTP_X_GUEST_SESSION=qr["guest_session_token"])
            tab = self.call(guest, "/guest/tabs/", {"display_label": "Test guest"}, 201)
            payload = {"idempotency_key": "original-offline-intent", "lines": [
                {"product_id": str(bar.pk), "quantity": 1}, {"product_id": str(kitchen.pk), "quantity": 1}]}
            # Discarding the first acknowledged result models a lost response after commit.
            first = self.call(manager, f"/tabs/{tab['id']}/orders/confirm/", payload, 201)
            replay = self.call(manager, f"/tabs/{tab['id']}/orders/confirm/", payload, 201)
            self.assertEqual(first["id"], replay["id"])
            self.assertEqual(Order.objects.count(), 1)
            for station in ("BAR", "KITCHEN"):
                rows = self.call(manager, f"/production/{station}/")["results"]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["order_id"], first["id"])
            self.call(manager, "/management/stations/KITCHEN/apply/", {
                "expected_version": 1, "enabled": False, "reason": "Unsafe maintenance"}, 409)
            for item in first["items"]:
                for state in ("ACCEPTED", "PREPARING", "READY"):
                    self.call(manager, f"/order-items/{item['id']}/transition/", {"state": state})
            for task in self.call(manager, "/dispatch/delivery/")["results"]:
                self.call(manager, f"/dispatch/delivery/{task['id']}/complete/", {})
            self.call(manager, "/printing/kds/BAR/heartbeat/", {"queue_observed": True})
            payment = self.call(manager, f"/tabs/{tab['id']}/payments/", {
                "amount_cents": 3000, "amount_tendered_cents": 3000, "cash_point_id": str(point.pk),
                "method": "CASH", "idempotency_key": "test-payment"}, 201)
            # Audited manual refund and replacement receipt preserve original payment.
            self.call(manager, f"/payments/{payment['id']}/refunds/", {
                "amount_cents": 100, "cash_point_id": str(point.pk), "idempotency_key": "test-refund",
                "reason": "Test correction"}, 201)
            self.call(manager, f"/tabs/{tab['id']}/payments/", {
                "amount_cents": 100, "method": "OTHER", "idempotency_key": "test-replacement"}, 201)
            self.call(manager, f"/tabs/{tab['id']}/close/", {})
            pending = self.call(manager, "/management/daily-closes/", {
                "business_date": day.isoformat(), "idempotency_key": "before-close"}, 201)
            self.assertEqual(pending["status"], "INCOMPLETE")
            counting = start_cash_count(shift_id=shift["id"], actor=actor)
            closed = close_cash_shift(shift_id=counting.pk, counted_amount_cents=7800,
                review_threshold_cents=0, expected_version=counting.version, actor=actor)
            self.assertEqual(closed.discrepancy_cents, -100)
        # New authentication at the next boundary models manager final review.
        with patch("django.utils.timezone.now", return_value=boundary + timedelta(minutes=1)):
            manager, actor = self.login()
            kds = self.call(manager, "/printing/kds/")["results"]
            self.assertEqual(next(row for row in kds if row["station"] == "BAR")["state"], "UNHEALTHY")
            self.assertEqual(PrintJob.objects.count(), 0)  # Fallback remains disabled in D1.
            review_cash_discrepancy(shift_id=closed.pk, reason="Test shortage reviewed", actor=actor)
            ready = self.call(manager, "/management/daily-closes/", {
                "business_date": day.isoformat(), "idempotency_key": "final-close"}, 201)
            self.assertEqual(ready["status"], "READY_FOR_REVIEW")
            self.assertEqual(ready["original"]["receipts"]["paid_cents"], 3100)
            self.assertEqual(ready["original"]["receipts"]["refunds_cents"], 100)
            reviewed = self.call(manager, f"/management/daily-closes/{ready['id']}/review/", {
                "expected_version": ready["version"], "reason": "Test shift checked"})
            self.assertEqual(reviewed["status"], "REVIEWED")
            original = DailyClose.objects.get(pk=ready["id"]).snapshot
            record_late_cash_correction(shift_id=closed.pk, amount_cents=-100,
                idempotency_key="late-test-correction", reason="Test omitted withdrawal", actor=actor)
            corrected = self.call(manager, f"/management/daily-closes/{ready['id']}/")
            self.assertEqual(corrected["original"], original)
            self.assertEqual(corrected["corrected_cash_delta_cents"], -100)
            self.assertEqual(corrected["status"], "REVIEWED")
