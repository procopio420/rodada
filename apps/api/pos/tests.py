from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from audit.models import AuditEvent
from cash.models import CashShift
from catalog.models import Product
from ledger.models import Adjustment, Charge, Payment
from pos.models import Order, OrderItem, ServicePoint, StaffMember, Tab, Venue, Zone
from pos.services import cancel_order_item, close_tab, confirm_order, exposure_cents, record_payment, transition_order_item


class PosDomainTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Test bar")
        self.manager = StaffMember.objects.create(venue=self.venue, display_name="Manager", role=StaffMember.Role.MANAGER)
        self.staff = StaffMember.objects.create(venue=self.venue, display_name="Staff")
        self.product = Product.objects.create(venue=self.venue, name="Beer", current_price_cents=1000, fulfillment_station="BAR")
        self.tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        CashShift.objects.create(venue=self.venue, opened_by=self.manager)

    def confirmed_item(self):
        order = Order.objects.create(tab=self.tab, created_by=self.staff)
        item = OrderItem.objects.create(order=order, product=self.product, quantity=2)
        confirm_order(order.id, self.staff)
        return order, item

    def test_price_is_snapshotted_at_confirmation(self):
        _, item = self.confirmed_item()
        self.product.current_price_cents = 1200; self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.unit_price_cents, 1000)
        self.assertEqual(item.charge.amount_cents, 2000)

    def test_confirm_retry_creates_exactly_one_charge(self):
        order, item = self.confirmed_item()
        confirm_order(order.id, self.staff)
        self.assertEqual(Charge.objects.filter(order_item=item).count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="order.confirmed").count(), 1)

    def test_confirmed_cancellation_preserves_charge_and_reverses_exposure(self):
        _, item = self.confirmed_item()
        cancel_order_item(item.id, self.manager, "Customer changed mind")
        item.refresh_from_db()
        self.assertEqual(item.state, OrderItem.State.CANCELLED)
        self.assertEqual(Charge.objects.filter(order_item=item).count(), 1)
        self.assertEqual(item.reversal_adjustment.amount_cents, -2000)
        self.assertEqual(exposure_cents(self.tab), 0)
        self.assertTrue(AuditEvent.objects.filter(action="order_item.cancelled").exists())

    def test_confirmed_payment_reduces_exposure_but_other_states_do_not(self):
        self.confirmed_item()
        record_payment(self.tab.id, self.staff, amount_cents=500, method=Payment.Method.CASH, status=Payment.Status.CONFIRMED)
        record_payment(self.tab.id, self.staff, amount_cents=300, method=Payment.Method.CARD, status=Payment.Status.FAILED)
        self.assertEqual(exposure_cents(self.tab), 1500)
        self.assertTrue(AuditEvent.objects.filter(action="payment.recorded", entity_type="ledger.Payment").exists())

    def test_payment_cannot_create_negative_exposure(self):
        self.confirmed_item()
        with self.assertRaises(Exception):
            record_payment(self.tab.id, self.staff, amount_cents=2001, method=Payment.Method.CASH)
        self.assertEqual(exposure_cents(self.tab), 2000)

    def test_normal_close_requires_zero_exposure(self):
        self.confirmed_item()
        with self.assertRaises(Exception): close_tab(self.tab.id, self.manager)
        record_payment(self.tab.id, self.staff, amount_cents=2000, method=Payment.Method.PIX)
        closed = close_tab(self.tab.id, self.manager)
        self.assertEqual(closed.status, Tab.Status.CLOSED)
        self.assertTrue(AuditEvent.objects.filter(action="tab.closed", entity_id=closed.id).exists())

    def test_closed_tab_rejects_direct_order_confirmation(self):
        order = Order.objects.create(tab=self.tab, created_by=self.staff)
        OrderItem.objects.create(order=order, product=self.product, quantity=1)
        close_tab(self.tab.id, self.manager)
        with self.assertRaises(Exception):
            confirm_order(order.id, self.staff)

    def test_regular_staff_cannot_close_tab(self):
        with self.assertRaises(Exception):
            close_tab(self.tab.id, self.staff)

    def test_closed_tab_rejects_fulfillment_mutation(self):
        _, item = self.confirmed_item()
        record_payment(self.tab.id, self.staff, amount_cents=2000, method=Payment.Method.PIX)
        close_tab(self.tab.id, self.manager)
        with self.assertRaises(Exception):
            transition_order_item(item.id, OrderItem.State.ACCEPTED, self.staff)

    def test_service_point_move_does_not_mutate_orders_or_ledger(self):
        zone = Zone.objects.create(venue=self.venue, name="Rua")
        point = ServicePoint.objects.create(venue=self.venue, zone=zone, code="P37")
        _, item = self.confirmed_item()
        charge_id, order_id = item.charge.id, item.order_id
        self.tab.service_point = point; self.tab.save()
        item.refresh_from_db(); self.tab.refresh_from_db()
        self.assertEqual((item.order_id, item.charge.id), (order_id, charge_id))
        self.assertEqual(self.tab.service_point, point)

    def test_transitions_record_timestamps(self):
        _, item = self.confirmed_item()
        transition_order_item(item.id, OrderItem.State.ACCEPTED, self.staff)
        transition_order_item(item.id, OrderItem.State.READY, self.staff)
        item.refresh_from_db()
        self.assertIsNotNone(item.accepted_at); self.assertIsNotNone(item.ready_at)

    def test_cash_shift_groups_confirmed_payments_by_method(self):
        self.confirmed_item()
        record_payment(self.tab.id, self.staff, amount_cents=1000, method=Payment.Method.CASH)
        record_payment(self.tab.id, self.staff, amount_cents=1000, method=Payment.Method.CARD)
        shift = CashShift.objects.get(venue=self.venue, closed_at__isnull=True)
        self.assertEqual(sum(p.amount_cents for p in shift.payments.filter(method=Payment.Method.CASH, status=Payment.Status.CONFIRMED)), 1000)
        self.assertEqual(sum(p.amount_cents for p in shift.payments.filter(method=Payment.Method.CARD, status=Payment.Status.CONFIRMED)), 1000)


class PosApiFlowTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="API bar")
        self.staff = StaffMember.objects.create(venue=self.venue, display_name="Cashier", role=StaffMember.Role.CASHIER)
        self.product = Product.objects.create(venue=self.venue, name="Soda", current_price_cents=700, fulfillment_station="BAR")
        CashShift.objects.create(venue=self.venue, opened_by=self.staff)
        self.client = APIClient(); self.client.credentials(HTTP_X_STAFF_ID=str(self.staff.id))

    def charged_tab(self):
        tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        order = Order.objects.create(tab=tab, created_by=self.staff)
        OrderItem.objects.create(order=order, product=self.product, quantity=2)
        confirm_order(order.id, self.staff)
        return tab

    def test_staff_can_complete_http_vertical_flow(self):
        tab = self.client.post("/api/tabs/", {"venue_id": self.venue.id, "label": "Walk-in"}, format="json").json()
        order = self.client.post(f"/api/tabs/{tab['id']}/orders/", {"items": [{"product_id": self.product.id, "quantity": 2}]}, format="json").json()
        confirmed = self.client.post(f"/api/orders/{order['id']}/confirm/", {}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        detail = self.client.get(f"/api/tabs/{tab['id']}/").json()
        self.assertEqual(detail["exposure_cents"], 1400)
        payment = self.client.post(f"/api/tabs/{tab['id']}/payments/", {"amount_cents": 1400, "method": "CASH", "idempotency_key": "example-payment"}, format="json")
        self.assertEqual(payment.status_code, 201)
        closed = self.client.post(f"/api/tabs/{tab['id']}/close/", {}, format="json")
        self.assertEqual(closed.status_code, 200)
        self.assertEqual(closed.json()["status"], "CLOSED")

    def test_invalid_order_is_atomic_and_returns_400(self):
        tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        response = self.client.post(f"/api/tabs/{tab.id}/orders/", {"items": [
            {"product_id": self.product.id, "quantity": 1},
            {"product_id": self.product.id, "quantity": 0},
        ]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.filter(tab=tab).exists())

    def test_order_command_is_idempotent_for_offline_replay(self):
        tab = Tab.objects.create(venue=self.venue, opened_by=self.staff)
        payload = {"items": [{"product_id": self.product.id, "quantity": 2}], "idempotency_key": "offline-order-1"}
        first = self.client.post(f"/api/tabs/{tab.id}/orders/", payload, format="json")
        second = self.client.post(f"/api/tabs/{tab.id}/orders/", payload, format="json")
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(Order.objects.filter(tab=tab).count(), 1)

    def test_payment_endpoint_does_not_accept_client_financial_status(self):
        tab = self.charged_tab()
        response = self.client.post(f"/api/tabs/{tab.id}/payments/", {
            "amount_cents": 700, "method": "PIX", "status": "FAILED", "idempotency_key": "forced-status",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Payment.objects.get(pk=response.json()["id"]).status, Payment.Status.CONFIRMED)

    def test_idempotency_key_rejects_different_payment_payload(self):
        tab = self.charged_tab()
        first = self.client.post(f"/api/tabs/{tab.id}/payments/", {
            "amount_cents": 700, "method": "PIX", "idempotency_key": "same-command",
        }, format="json")
        second = self.client.post(f"/api/tabs/{tab.id}/payments/", {
            "amount_cents": 800, "method": "PIX", "idempotency_key": "same-command",
        }, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Payment.objects.filter(tab=tab).count(), 1)

    def test_local_web_origin_receives_cors_header(self):
        response = self.client.options(
            "/api/tabs/",
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-staff-id",
        )
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertIn("x-staff-id", response["Access-Control-Allow-Headers"].lower())

    def test_read_endpoints_are_scoped_to_staff_venue(self):
        other_venue = Venue.objects.create(name="Other bar")
        Product.objects.create(venue=other_venue, name="Secret product", current_price_cents=999)
        other_staff = StaffMember.objects.create(venue=other_venue, display_name="Other")
        other_tab = Tab.objects.create(venue=other_venue, opened_by=other_staff)

        products = self.client.get("/api/products/").json()
        tabs = self.client.get("/api/tabs/").json()
        self.assertEqual([row["id"] for row in products], [self.product.id])
        self.assertNotIn(other_tab.id, [row["id"] for row in tabs])
        self.assertEqual(self.client.get(f"/api/tabs/{other_tab.id}/").status_code, 404)

    def test_read_endpoints_require_staff_identity(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.get("/api/products/").status_code, 403)
        self.assertEqual(anonymous.get("/api/tabs/").status_code, 403)

    def test_staff_can_login_with_seed_style_pin_and_use_session(self):
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        logged_in = self.client.post("/api/auth/login/", {
            "venue_id": self.venue.id, "display_name": self.staff.display_name, "pin": "1234",
        }, format="json")
        self.assertEqual(logged_in.status_code, 201)
        session_client = APIClient()
        session_client.credentials(HTTP_AUTHORIZATION=f"Bearer {logged_in.json()['session_token']}")
        self.assertEqual(session_client.get("/api/auth/session/").json()["staff"]["id"], self.staff.id)
        self.assertEqual(session_client.get("/api/products/").status_code, 200)
