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
        self.cancelled = Product.objects.create(
            venue=self.venue,
            name="Petisco lançado em duplicidade",
            price_cents=600,
            fulfillment_station=FulfillmentStation.KITCHEN,
        )
        self.post_production = Product.objects.create(
            venue=self.venue,
            name="Prato preparado e cancelado",
            price_cents=900,
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
                    {"product_id": str(self.cancelled.id), "quantity": 1},
                    {"product_id": str(self.post_production.id), "quantity": 1},
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

        # Once production has begun, an exception remains visible in both
        # operational and financial history. It requires manager reauth and
        # does not pretend the work never happened.
        prepared_item = staff_order["items"][3]
        self.post(self.staff, f"/order-items/{prepared_item['id']}/transition/", {"state": "ACCEPTED"})
        self.post(self.staff, f"/order-items/{prepared_item['id']}/transition/", {"state": "PREPARING"})
        self.post(self.staff, "/auth/reauthenticate/", {"pin": "0420"})
        post_production_cancel = self.post(
            self.staff,
            f"/order-items/{prepared_item['id']}/corrections/post-production/",
            {
                "kind": "CANCEL_ITEM",
                "reason_code": "CUSTOMER_LEFT",
                "reason_text": "Preparado, mas cliente saiu",
                "idempotency_key": "joao-preparing-cancel",
            },
        )
        self.assertEqual(post_production_cancel["order_item_state"], "CANCELLED")
        self.assertEqual(post_production_cancel["adjustments_cents"], -900)

        # A remake creates a separate production item and compensating
        # courtesy adjustment; the delivered original remains historical.
        remake = self.post(
            self.staff,
            f"/order-items/{bar_item['id']}/corrections/post-production/",
            {
                "kind": "REMAKE",
                "reason_code": "QUALITY_ISSUE",
                "reason_text": "Bebida devolvida após entrega",
                "idempotency_key": "joao-bar-remake",
            },
        )
        self.assertIsNotNone(remake["replacement_order_item_id"])

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

        # A pre-production staff mistake appends an immutable negative ledger
        # fact. The original 600-cent Charge remains historical and the Tab
        # retains the rest of its independently payable responsibility.
        cancelled = self.post(
            self.staff,
            f"/order-items/{staff_order['items'][2]['id']}/corrections/cancel/",
            {
                "kind": "WRONG_ITEM_ENTERED",
                "reason_code": "DUPLICATE_ENTRY",
                "reason_text": "Lançado duas vezes no atendimento",
                "idempotency_key": "joao-duplicate-item",
            },
        )
        self.assertEqual(cancelled["adjustments_cents"], -2700)
        self.assertEqual(cancelled["exposure_cents"], 3600)

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
        joao_card = self.post(
            self.staff,
            f"/tabs/{joao['id']}/payments/",
            {"amount_cents": 2400, "method": "CARD", "idempotency_key": "joao-card"},
        )
        # A later paid mistake does not rewrite either the card payment or the
        # item. It first becomes an explicit refund-required correction, then
        # a recently reauthenticated manager settles its refund and reversal.
        paid_correction = self.post(
            self.staff,
            f"/order-items/{staff_order['items'][1]['id']}/corrections/cancel/",
            {
                "kind": "CUSTOMER_CHANGED_MIND",
                "reason_code": "CUSTOMER_LEFT",
                "reason_text": "Cliente desistiu antes da cozinha iniciar",
                "idempotency_key": "joao-paid-kitchen-cancel",
            },
        )
        self.assertEqual(paid_correction["financial_disposition"], "REFUND_REQUIRED")
        self.post(self.staff, "/auth/reauthenticate/", {"pin": "0420"})
        settled = self.post(
            self.staff,
            f"/corrections/{paid_correction['id']}/settle-refund/",
            {
                "payment_id": joao_card["id"],
                "amount_cents": 2400,
                "refund_idempotency_key": "joao-paid-kitchen-refund",
            },
        )
        self.assertEqual(settled["exposure_cents"], 0)
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

        # Cash custody is append-only as well. Supply and withdrawal happen
        # before the independent physical count; the deliberate difference is
        # reviewed instead of hidden by a fabricated movement.
        self.post(
            self.staff,
            f"/cash/shifts/{shift['id']}/supply/",
            {"amount_cents": 500, "reason": "Troco para pico", "idempotency_key": "shift-supply"},
        )
        self.post(
            self.staff,
            f"/cash/shifts/{shift['id']}/withdrawal/",
            {"amount_cents": 200, "reason": "Envio ao cofre", "idempotency_key": "shift-withdrawal"},
        )
        counting = self.post(self.staff, f"/cash/shifts/{shift['id']}/count/start/")
        closed = self.post(
            self.staff,
            f"/cash/shifts/{shift['id']}/close/",
            {
                "counted_amount_cents": 12_600,
                "review_threshold_cents": 0,
                "expected_version": counting["version"],
            },
        )
        self.assertEqual(closed["discrepancy_cents"], -100)
        self.assertEqual(closed["review_status"], "PENDING")
        self.post(self.staff, "/auth/reauthenticate/", {"pin": "0420"})
        reviewed = self.post(
            self.staff,
            f"/cash/shifts/{shift['id']}/review/",
            {"reason": "Diferença anotada no cofre"},
        )
        self.assertEqual(reviewed["review_status"], "REVIEWED")
