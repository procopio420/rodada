"""Cross-role history readback through the public API, using disposable test data."""

import secrets

from django.test import TestCase
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.ledger.models import Charge, Payment
from modules.ordering.models import Tab
from modules.venue.calendar import business_date
from modules.venue.models import Venue


class ManagerTabLifecycleTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Lifecycle fixture", slug="lifecycle-fixture")
        self.waiter, self.waiter_record, self.membership = self.login(
            "waiter-fixture", StaffRole.STAFF, "ANDROID", allow=["payment.collect"]
        )
        self.manager, _, _ = self.login("manager-fixture", StaffRole.MANAGER, "WEB")
        self.product = Product.objects.create(
            venue=self.venue,
            name="Item do teste de histórico",
            price_cents=1000,
            fulfillment_station="BAR",
        )

    def login(self, identifier, role, platform, allow=None, venue=None):
        venue = venue or self.venue
        staff = StaffMember.objects.create(display_name=identifier, login_identifier=identifier)
        pin = str(secrets.randbelow(900000) + 100000)
        staff.set_pin(pin)
        staff.save()
        member = VenueStaffMembership.objects.create(
            venue=venue,
            staff_member=staff,
            role=role,
            capability_overrides={"allow": allow or []},
        )
        client = APIClient()
        response = client.post(
            "/auth/login/",
            {
                "venue_slug": venue.slug,
                "login_identifier": identifier,
                "pin": pin,
                "platform": platform,
                "installation_id": identifier,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + response.json()["access_token"])
        return client, staff, member

    def open_tab(self, label="Comanda do atendimento"):
        response = self.waiter.post("/tabs/", {"display_label": label}, format="json")
        self.assertEqual(response.status_code, 201)
        return response.json()["id"]

    def order(self, tab_id):
        response = self.waiter.post(
            f"/tabs/{tab_id}/orders/confirm/",
            {
                "idempotency_key": f"order-{tab_id}",
                "lines": [{"product_id": str(self.product.id), "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return self.detail(tab_id)["orders"][0]["items"][0]["id"]

    def detail(self, tab_id):
        response = self.manager.get(f"/tabs/{tab_id}/")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def list_ids(self, query):
        response = self.manager.get(f"/tabs/?{query}")
        self.assertEqual(response.status_code, 200)
        return {row["id"]: row for row in response.json()["results"]}

    def history(self):
        return self.list_ids("history_day=current")

    def report(self):
        day = business_date(self.venue)
        response = self.manager.get(f"/management/reports/?start={day}&end={day}")
        self.assertEqual(response.status_code, 200)
        return response.json()["totals"]

    def payment(self, tab_id, amount, key):
        return self.waiter.post(
            f"/tabs/{tab_id}/payments/",
            {
                "amount_cents": amount,
                "method": "CARD",
                "idempotency_key": key,
            },
            format="json",
        )

    def cancel(self, tab_id, key="cancel-fixture"):
        return self.waiter.post(
            f"/tabs/{tab_id}/operations/",
            {
                "kind": "CANCEL_EMPTY",
                "expected_version": self.detail(tab_id)["version"],
                "idempotency_key": key,
                "reason": "Abertura duplicada no teste",
            },
            format="json",
        )

    def test_waiter_open_partial_and_paid_are_canonical_for_manager(self):
        tab_id = self.open_tab()
        self.order(tab_id)
        self.assertEqual(self.list_ids("active=true")[tab_id]["exposure_cents"], 2000)
        self.assertNotIn(tab_id, self.history())
        self.assertEqual(self.payment(tab_id, 1000, "partial-fixture").status_code, 201)
        self.assertEqual(self.detail(tab_id)["state"], "OPEN")
        self.assertEqual(self.detail(tab_id)["exposure_cents"], 1000)
        self.assertEqual(self.report()["paid_cents"], 1000)
        self.assertEqual(self.report()["current_open_exposure_cents"], 1000)
        self.assertIn(tab_id, self.list_ids("active=true"))
        self.assertNotIn(tab_id, self.history())

        paid = self.payment(tab_id, 1000, "final-fixture")
        self.assertEqual(paid.status_code, 201)
        replay = self.payment(tab_id, 1000, "final-fixture")
        self.assertEqual(replay.json()["id"], paid.json()["id"])
        detail = self.detail(tab_id)
        self.assertEqual(detail["state"], "CLOSED")
        self.assertIsNotNone(detail["closed_at"])
        self.assertEqual(detail["payable_cents"], 2000)
        self.assertEqual(detail["payments_cents"], 2000)
        self.assertEqual(detail["exposure_cents"], 0)
        self.assertEqual(len(detail["payments"]), 2)
        self.assertEqual(detail["orders"][0]["items"][0]["product_name"], self.product.name)
        self.assertNotIn(tab_id, self.list_ids("active=true"))
        self.assertEqual(self.history()[tab_id]["state"], "CLOSED")
        self.assertEqual(Payment.objects.filter(tab_id=tab_id).count(), 2)
        self.assertEqual(Charge.objects.filter(tab_id=tab_id).count(), 1)
        event = AuditEvent.objects.get(event_type="tab.closed", entity_id=tab_id)
        self.assertEqual(event.actor_staff_id, self.waiter_record.id)
        self.assertEqual(Tab.objects.get(pk=tab_id).opened_by_id, self.waiter_record.id)
        self.assertEqual(self.report()["paid_cents"], 2000)
        self.assertEqual(self.report()["current_open_exposure_cents"], 0)
        self.assertEqual(self.report()["current_open_tabs"], 0)

    def test_waiter_empty_cancellation_reaches_manager_history_once(self):
        tab_id = self.open_tab()
        self.assertIn(tab_id, self.list_ids("active=true"))
        version = self.detail(tab_id)["version"]
        command = {
            "kind": "CANCEL_EMPTY",
            "expected_version": version,
            "idempotency_key": "cancel-empty-fixture",
            "reason": "Abertura duplicada no teste",
        }
        first = self.waiter.post(f"/tabs/{tab_id}/operations/", command, format="json")
        self.assertEqual(first.status_code, 200)
        replay = self.waiter.post(f"/tabs/{tab_id}/operations/", command, format="json")
        self.assertEqual(replay.status_code, 200)
        self.assertNotIn(tab_id, self.list_ids("active=true"))
        self.assertEqual(self.history()[tab_id]["state"], "CANCELLED")
        detail = self.detail(tab_id)
        self.assertEqual(detail["payments_cents"], 0)
        self.assertEqual(detail["exposure_cents"], 0)
        self.assertEqual(detail["orders"], [])
        event = AuditEvent.objects.get(event_type="tab.cancelled", entity_id=tab_id)
        self.assertEqual(event.actor_staff_id, self.waiter_record.id)
        self.assertFalse(Payment.objects.filter(tab_id=tab_id).exists())
        self.assertEqual(self.report()["paid_cents"], 0)
        self.assertEqual(self.report()["gross_cents"], 0)

    def test_nonempty_cancellation_and_unauthorized_payment_cannot_hide_open_tab(self):
        tab_id = self.open_tab()
        self.order(tab_id)
        response = self.cancel(tab_id)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "TAB_NOT_EMPTY")
        self.membership.capability_overrides = {}
        self.membership.save()
        self.assertEqual(self.payment(tab_id, 2000, "denied-fixture").status_code, 403)
        self.assertEqual(self.detail(tab_id)["state"], "OPEN")
        self.assertEqual(self.list_ids("active=true")[tab_id]["exposure_cents"], 2000)
        self.assertNotIn(tab_id, self.history())
        self.assertFalse(Payment.objects.filter(tab_id=tab_id).exists())
        self.assertFalse(
            AuditEvent.objects.filter(event_type="tab.cancelled", entity_id=tab_id).exists()
        )

    def test_fully_cancelled_consumption_can_close_without_inventing_payment(self):
        tab_id = self.open_tab()
        item_id = self.order(tab_id)
        response = self.waiter.post(
            f"/order-items/{item_id}/corrections/cancel/",
            {
                "kind": "WRONG_ITEM_ENTERED",
                "reason_code": "WRONG_ENTRY",
                "reason_text": "Lançamento duplicado no teste",
                "idempotency_key": "cancel-items-fixture",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        closed = self.waiter.post(f"/tabs/{tab_id}/close/", {}, format="json")
        self.assertEqual(closed.status_code, 200)
        self.assertNotIn(tab_id, self.list_ids("active=true"))
        self.assertEqual(self.history()[tab_id]["state"], "CLOSED")
        detail = self.detail(tab_id)
        self.assertEqual(detail["payable_cents"], 0)
        self.assertEqual(detail["payments_cents"], 0)
        self.assertEqual(detail["orders"][0]["items"][0]["state"], "CANCELLED")
        self.assertFalse(Payment.objects.filter(tab_id=tab_id).exists())
        self.assertEqual(self.report()["paid_cents"], 0)
        self.assertEqual(self.report()["net_sales_cents"], 0)

    def test_pending_payment_stays_open_and_is_not_received_in_manager_report(self):
        tab_id = self.open_tab()
        self.order(tab_id)
        Payment.objects.create(
            tab_id=tab_id,
            amount_cents=2000,
            method="CARD",
            status="PENDING",
            idempotency_key="provider-pending-fixture",
            received_by=self.waiter_record,
        )
        self.assertEqual(self.detail(tab_id)["state"], "OPEN")
        self.assertEqual(self.detail(tab_id)["payments_cents"], 0)
        self.assertIn(tab_id, self.list_ids("active=true"))
        self.assertNotIn(tab_id, self.history())
        self.assertEqual(self.report()["paid_cents"], 0)
        self.assertEqual(self.report()["current_open_exposure_cents"], 2000)

    def test_another_venue_manager_cannot_read_waiter_history(self):
        tab_id = self.open_tab()
        self.assertEqual(self.cancel(tab_id).status_code, 200)
        other = Venue.objects.create(name="Other lifecycle fixture", slug="other-lifecycle")
        client, _, _ = self.login("other-manager-fixture", StaffRole.MANAGER, "WEB", venue=other)
        self.assertEqual(client.get(f"/tabs/{tab_id}/").status_code, 404)
        self.assertEqual(client.get("/tabs/?history_day=current").json()["results"], [])
