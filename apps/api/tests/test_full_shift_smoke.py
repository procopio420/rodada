"""Canonical persisted assisted-shift smoke path.

This is intentionally one cross-domain scenario instead of a collection of UI
fixtures: each action travels through the public API and later stages consume
the state persisted by earlier ones.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import FulfillmentStation, Product
from modules.hospitality.models import TableStatus
from modules.venue.models import Venue


class FullShiftSmokeTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Shift smoke", slug="shift-smoke")
        self.manager = StaffMember.objects.create(display_name="Ana", login_identifier="shift-ana")
        self.manager.set_pin("0420")
        self.manager.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.manager, role=StaffRole.MANAGER
        )
        self.staff = APIClient()
        login = self.staff.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": "shift-ana",
                "pin": "0420",
                "installation_id": "shift-smoke-manager-device",
                "platform": "WEB",
            },
            format="json",
        )
        self.assertEqual(login.status_code, 200, login.json())
        self.staff.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.bar = Product.objects.create(
            venue=self.venue,
            name="Brahma smoke",
            price_cents=1200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        self.kitchen = Product.objects.create(
            venue=self.venue,
            name="Fritas smoke",
            price_cents=2400,
            fulfillment_station=FulfillmentStation.KITCHEN,
        )

    def post(self, client, path, body=None):
        response = client.post(path, body or {}, format="json")
        self.assertLess(response.status_code, 300, response.json())
        return response.json()

    def test_qr_to_delivery_to_cash_close_and_table_release(self):
        point = self.post(self.staff, "/cash/points/create/", {"label": "Caixa smoke"})
        shift = self.post(
            self.staff,
            "/cash/shifts/",
            {
                "cash_point_id": point["id"],
                "opening_float_cents": 10_000,
                "business_date": "2026-10-07",
                "idempotency_key": "shift-open",
            },
        )
        table = self.post(
            self.staff,
            "/hospitality/tables/",
            {"label": "24", "guest_ordering_mode": "DIRECT"},
        )
        occupancy = self.post(self.staff, f"/hospitality/tables/{table['id']}/occupy/")

        joao = self.post(self.staff, "/tabs/", {"display_label": "João"})
        self.post(
            self.staff,
            f"/hospitality/occupancies/{occupancy['id']}/tabs/",
            {"tab_id": joao["id"]},
        )
        staff_order = self.post(
            self.staff,
            f"/tabs/{joao['id']}/orders/confirm/",
            {
                "idempotency_key": "joao-order",
                "lines": [
                    {"product_id": str(self.bar.id), "quantity": 1},
                    {"product_id": str(self.kitchen.id), "quantity": 1},
                ],
            },
        )

        guest = APIClient()
        context = self.post(guest, "/guest/qr/resolve/", {"token": table["public_token"]})
        guest.credentials(HTTP_X_GUEST_SESSION=context["guest_session_token"])
        ana = self.post(guest, "/guest/tabs/", {"display_label": "Ana"})
        guest_order = self.post(
            guest,
            "/guest/orders/confirm/",
            {
                "idempotency_key": "ana-order",
                "lines": [{"product_id": str(self.bar.id), "quantity": 1}],
            },
        )
        self.assertEqual(guest_order["source"], "GUEST")

        # Per-item readiness creates per-item delivery work; no order-wide READY fiction.
        bar_item = staff_order["items"][0]
        self.post(self.staff, f"/order-items/{bar_item['id']}/transition/", {"state": "ACCEPTED"})
        self.post(self.staff, f"/order-items/{bar_item['id']}/transition/", {"state": "READY"})
        deliveries = self.staff.get("/dispatch/delivery/")
        self.assertEqual(deliveries.status_code, 200, deliveries.json())
        delivery = next(row for row in deliveries.json()["results"] if row["order_item_id"] == bar_item["id"])
        self.assertEqual(delivery["destination_label"], "Mesa 24")
        completed = self.post(self.staff, f"/dispatch/delivery/{delivery['id']}/complete/")
        self.assertEqual(completed["state"], "DONE")

        # The stale availability guard applies to the same guest catalog/order pipeline.
        self.post(
            self.staff,
            f"/catalog/products/{self.kitchen.id}/availability/",
            {"state": "UNAVAILABLE"},
        )
        stale = guest.post(
            "/guest/orders/confirm/",
            {
                "idempotency_key": "ana-stale-cart",
                "lines": [{"product_id": str(self.kitchen.id), "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["code"], "PRODUCTS_NOT_CONFIRMABLE")

        # Partial cash records net drawer effects; the remaining staff payment is canonical too.
        self.post(
            self.staff,
            f"/tabs/{joao['id']}/payments/",
            {
                "amount_cents": 1200,
                "amount_tendered_cents": 1200,
                "method": "CASH",
                "cash_point_id": point["id"],
                "idempotency_key": "joao-cash",
            },
        )
        self.post(
            self.staff,
            f"/tabs/{joao['id']}/payments/",
            {"amount_cents": 2400, "method": "CARD", "idempotency_key": "joao-card"},
        )
        self.post(self.staff, f"/tabs/{joao['id']}/close/")
        self.post(
            self.staff,
            f"/tabs/{ana['id']}/payments/",
            {
                "amount_cents": 1200,
                "amount_tendered_cents": 2000,
                "method": "CASH",
                "cash_point_id": point["id"],
                "idempotency_key": "ana-cash",
            },
        )
        self.post(self.staff, f"/tabs/{ana['id']}/close/")

        # Closing tabs never releases a physical table; staff releases/cleans it explicitly.
        released = self.post(self.staff, f"/hospitality/tables/{table['id']}/release/")
        self.assertIsNotNone(released["released_at"])
        self.post(self.staff, f"/hospitality/tables/{table['id']}/cleaning/start/")
        self.post(self.staff, f"/hospitality/tables/{table['id']}/cleaning/complete/")
        listed = self.staff.get("/hospitality/tables/").json()["results"]
        self.assertEqual(next(row for row in listed if row["id"] == table["id"])["status"], TableStatus.AVAILABLE)

        counting = self.post(self.staff, f"/cash/shifts/{shift['id']}/count/start/")
        closed = self.post(
            self.staff,
            f"/cash/shifts/{shift['id']}/close/",
            {
                "counted_amount_cents": 12_400,
                "review_threshold_cents": 0,
                "expected_version": counting["version"],
            },
        )
        self.assertEqual(closed["discrepancy_cents"], 0)
