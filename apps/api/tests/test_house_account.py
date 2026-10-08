"""Spec 002 acceptance: real persisted ledger, authorization and order pipeline."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.house_account.models import (
    Customer,
    LimitOverride,
    Relationship,
    VenueRelationshipPolicy,
)
from modules.ledger.models import Charge, Payment
from modules.ledger.services import exposure_cents
from modules.ordering.models import OrderItem, Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import Venue


class HouseFixture:
    def setUp(self):
        super().setUp()
        self.venue = Venue.objects.create(name="House proof", slug="house-proof")
        self.product = Product.objects.create(
            venue=self.venue, name="Água", price_cents=1000, fulfillment_station="BAR"
        )
        self.manager = self.login("manager", "MANAGER")
        self.staff = self.login("staff", "STAFF")
        self.cashier = self.login("cashier", "CASHIER")

    def login(self, name, role):
        staff = StaffMember.objects.create(display_name=name, login_identifier="house-" + name)
        staff.set_pin("0420")
        staff.save()
        VenueStaffMembership.objects.create(venue=self.venue, staff_member=staff, role=role)
        client = APIClient()
        response = client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "0420",
                "platform": "WEB",
                "installation_id": "house-" + name,
            },
            format="json",
        )
        assert response.status_code == 200, response.json()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + response.json()["access_token"])
        return client

    def post(self, client, path, body=None, status=200):
        response = client.post(path, body or {}, format="json")
        assert response.status_code == status, response.json()
        return response.json()

    def tab(self, customer=None):
        body = {"customer_id": str(customer.id)} if customer else {}
        return self.post(self.staff, "/tabs/", body, status=201)["id"]

    def order(self, tab_id, quantity=1, key="order", client=None, status=201, extra=None):
        return self.post(
            client or self.staff,
            f"/tabs/{tab_id}/orders/confirm/",
            {
                "idempotency_key": key,
                "lines": [{"product_id": str(self.product.id), "quantity": quantity}],
                **(extra or {}),
            },
            status=status,
        )

    def detail(self, tab_id):
        response = self.staff.get(f"/tabs/{tab_id}/")
        assert response.status_code == 200
        return response.json()

    def payment(self, tab_id, amount=1000, key="payment"):
        return self.post(
            self.cashier,
            f"/tabs/{tab_id}/payments/",
            {"amount_cents": amount, "method": "EXTERNAL_TERMINAL", "idempotency_key": key},
            status=201,
        )

    def reauth(self):
        self.post(self.manager, "/auth/reauthenticate/", {"pin": "0420"})

    def override(self, tab_id, limit=5000, **extra):
        return {
            "limit_cents": limit,
            "reason": "Aprovado durante esta visita",
            "expires_at": (timezone.now() + timedelta(hours=1)).isoformat(),
            "idempotency_key": "approval",
            **extra,
        }


class HouseAccountTests(HouseFixture, TestCase):
    def test_active_tab_pagination_does_not_hide_old_attention_tabs(self):
        Tab.objects.bulk_create([Tab(venue=self.venue, display_label=str(i)) for i in range(201)])
        first = self.staff.get("/tabs/", {"active": "true"}).json()
        assert len(first["results"]) == 200
        assert first["next_offset"] == 200
        second = self.staff.get("/tabs/", {"active": "true", "offset": 200}).json()
        assert len(second["results"]) == 1
        assert second["next_offset"] is None
        assert set(t["id"] for t in first["results"]).isdisjoint(t["id"] for t in second["results"])

    def test_staff_customer_search_is_venue_scoped(self):
        customer = self.post(
            self.manager,
            "/customers/",
            {"display_name": "João da Oficina", "kind": "REGULAR", "phone": "5551234"},
            status=201,
        )
        for query in ("oficina", "5551234"):
            response = self.staff.get("/customers/", {"q": query})
            assert response.status_code == 200
            assert response.json()["results"][0]["id"] == customer["id"]
        denied = self.staff.patch(f"/customers/{customer['id']}/", {"kind": "HOUSE"}, format="json")
        assert denied.status_code == 403

    def test_spending_limit_is_source_agnostic(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=3)
        for source in ("STAFF", "CASHIER", "GUEST"):
            with self.assertRaises(OrderingServiceError) as caught:
                confirm_order(
                    tab_id=tab_id,
                    source=source,
                    lines=[{"product_id": self.product.id, "quantity": 1}],
                    idempotency_key=source,
                )
            assert caught.exception.code == "SPENDING_LIMIT_EXCEEDED"
        assert Charge.objects.count() == 1

    def test_policy_update_preserves_existing_order(self):
        tab_id = self.tab()
        original = self.order(tab_id)
        self.reauth()
        response = self.manager.put(
            "/house-account/policies/", {"kind": "VISITOR", "limit_cents": 0}, format="json"
        )
        assert response.status_code == 200
        assert self.order(tab_id, status=200) == original
        assert self.detail(tab_id)["operating_limit_cents"] == 3000

    def test_direct_override_service_cannot_trust_a_waiter_actor(self):
        from modules.access.context import ActorContext
        from modules.access.errors import AccessPermissionDenied
        from modules.access.models import StaffSession
        from modules.house_account.services import approve_override

        tab_id = self.tab()
        session = StaffSession.objects.get(staff_member__login_identifier="house-staff")
        with self.assertRaises(AccessPermissionDenied):
            approve_override(
                tab_id=tab_id,
                limit_cents=5000,
                reason="Payload alterado",
                expires_at=timezone.now() + timedelta(hours=1),
                idempotency_key="illegal",
                actor=ActorContext.from_session(session),
            )
        assert not LimitOverride.objects.exists()

    def test_anonymous_uses_venue_visitor_policy_and_snapshots_updates(self):
        policy = VenueRelationshipPolicy.objects.create(
            venue=self.venue, kind="VISITOR", limit_cents=4000
        )
        tab_id = self.tab()
        detail = self.detail(tab_id)
        assert detail["customer_id"] is None
        assert detail["relationship_snapshot"] == "VISITOR"
        assert detail["operating_limit_cents"] == 4000
        self.reauth()
        response = self.manager.put(
            "/house-account/policies/", {"kind": "VISITOR", "limit_cents": 1000}, format="json"
        )
        assert response.status_code == 200, response.json()
        policy.refresh_from_db()
        assert policy.version == 2
        assert self.detail(tab_id)["operating_limit_cents"] == 4000
        assert self.detail(self.tab())["operating_limit_cents"] == 1000

    def test_house_and_restricted_snapshots(self):
        for kind, limit in [("HOUSE", 50000), ("RESTRICTED", 0)]:
            customer = Customer.objects.create(display_name=kind)
            Relationship.objects.create(venue=self.venue, customer=customer, kind=kind)
            tab_id = self.tab(customer)
            detail = self.detail(tab_id)
            assert detail["relationship_snapshot"] == kind
            assert detail["effective_limit_cents"] == limit
            if kind == "RESTRICTED":
                assert detail["state"] == "REQUIRES_ACTION"
                assert detail["percentage_used"] is None
                assert self.order(tab_id, status=409)["code"] == "SPENDING_LIMIT_EXCEEDED"

    def test_orders_below_limit_and_at_limit_then_no_effect_on_rejection(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=2)
        detail = self.detail(tab_id)
        assert detail["remaining_capacity_cents"] == 1000
        assert detail["percentage_used"] == 66
        self.order(tab_id, key="at-limit")
        detail = self.detail(tab_id)
        assert detail["state"] == "REQUIRES_ACTION"
        assert detail["consumption_blocked"]
        counts = (Charge.objects.count(), OrderItem.objects.count())
        self.order(tab_id, key="blocked", status=409)
        assert counts == (Charge.objects.count(), OrderItem.objects.count())
        assert Tab.objects.get(pk=tab_id).state == "REQUIRES_ACTION"

    def test_idempotent_replay_after_limit_policy_change_and_close(self):
        tab_id = self.tab()
        first = self.order(tab_id, quantity=3)
        assert self.order(tab_id, quantity=3, status=200)["id"] == first["id"]
        self.payment(tab_id, amount=3000)
        self.post(self.cashier, f"/tabs/{tab_id}/close/")
        assert self.order(tab_id, quantity=3, status=200)["id"] == first["id"]
        assert Charge.objects.count() == 1
        assert self.order(tab_id, quantity=2, status=409)["code"] == "IDEMPOTENCY_CONFLICT"

    def test_partial_payment_restores_capacity_and_refund_increases_exposure(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=3)
        payment = self.payment(tab_id)
        assert self.detail(tab_id)["remaining_capacity_cents"] == 1000
        assert self.detail(tab_id)["state"] == "OPEN"
        self.reauth()
        self.post(
            self.manager,
            f"/payments/{payment['id']}/refunds/",
            {"amount_cents": 1000, "idempotency_key": "refund", "reason": "Devolução confirmada"},
            status=201,
        )
        assert self.detail(tab_id)["exposure_cents"] == 3000
        assert self.detail(tab_id)["state"] == "REQUIRES_ACTION"
        assert (
            self.order(tab_id, key="after-refund", status=409)["code"] == "SPENDING_LIMIT_EXCEEDED"
        )

    def test_unauthorized_override_payload_and_recent_reauth(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=3)
        body = self.override(tab_id)
        self.post(self.staff, f"/tabs/{tab_id}/limit-override/", body, status=403)
        self.post(self.cashier, f"/tabs/{tab_id}/limit-override/", body, status=403)
        assert (
            self.post(self.manager, f"/tabs/{tab_id}/limit-override/", body, status=403)["code"]
            == "REAUTH_REQUIRED"
        )
        self.order(
            tab_id,
            key="tampered",
            status=409,
            extra={"limit_cents": 999999, "manager_approved": True},
        )
        assert LimitOverride.objects.count() == 0

    def test_override_idempotency_expiration_and_no_fake_money(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=3)
        self.reauth()
        body = self.override(tab_id)
        self.post(self.manager, f"/tabs/{tab_id}/limit-override/", body)
        self.post(self.manager, f"/tabs/{tab_id}/limit-override/", body)
        assert LimitOverride.objects.count() == 1
        assert Payment.objects.count() == 0
        assert AuditEvent.objects.filter(event_type="tab.limit_overridden").count() == 1
        history = self.manager.get(f"/tabs/{tab_id}/house-history/").json()["results"]
        event = next(row for row in history if row["event_type"] == "tab.limit_overridden")
        assert event["actor_name"] == "manager"
        assert event["actor"] is not None
        assert event["reason"] == body["reason"]
        assert event["metadata"]["previous_limit_cents"] == 3000
        assert event["metadata"]["limit_cents"] == 5000
        assert self.staff.get(f"/tabs/{tab_id}/house-history/").status_code == 403
        self.order(tab_id, key="approved")
        LimitOverride.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        assert self.detail(tab_id)["effective_limit_cents"] == 3000
        assert self.detail(tab_id)["consumption_blocked"]
        self.order(tab_id, key="expired", status=409)
        assert self.order(tab_id, key="approved", status=200)

    def test_override_cannot_clear_another_unresolved_reason(self):
        tab_id = self.tab()
        self.order(tab_id, quantity=3)
        Tab.objects.filter(pk=tab_id).update(action_reasons=["SPENDING_LIMIT", "MANUAL_REVIEW"])
        self.payment(tab_id)
        assert self.detail(tab_id)["state"] == "REQUIRES_ACTION"
        self.reauth()
        self.post(self.manager, f"/tabs/{tab_id}/limit-override/", self.override(tab_id))
        assert self.detail(tab_id)["action_reasons"] == ["MANUAL_REVIEW"]

    def test_customer_association_relationship_change_explicit_reassessment_preserves_history(self):
        tab_id = self.tab()
        order = self.order(tab_id)
        payment = self.payment(tab_id, amount=500)
        customer = self.post(
            self.manager, "/customers/", {"display_name": "João", "kind": "REGULAR"}, status=201
        )
        self.post(self.staff, f"/tabs/{tab_id}/customer/", {"customer_id": customer["id"]})
        assert self.detail(tab_id)["operating_limit_cents"] == 3000
        self.reauth()
        changed = self.manager.patch(
            f"/customers/{customer['id']}/", {"kind": "HOUSE"}, format="json"
        )
        assert changed.status_code == 200
        assert self.detail(tab_id)["relationship_snapshot"] == "VISITOR"
        self.post(
            self.manager, f"/tabs/{tab_id}/reassess-policy/", {"reason": "Cliente reconhecido"}
        )
        assert self.detail(tab_id)["operating_limit_cents"] == 50000
        assert self.order(tab_id, status=200) == order
        assert Payment.objects.get(pk=payment["id"]).amount_cents == 500
        assert self.manager.get(f"/customers/{customer['id']}/").json()["tabs"][0]["id"] == tab_id
        assert AuditEvent.objects.filter(event_type="tab.policy_reassessed").exists()

    def test_guest_and_staff_share_same_tab_enforcement(self):
        table = self.post(
            self.manager,
            "/hospitality/tables/",
            {"label": "24", "guest_ordering_mode": "DIRECT"},
            status=201,
        )
        guest = APIClient()
        context = self.post(
            guest, "/guest/qr/resolve/", {"token": table["public_token"]}, status=201
        )
        guest.credentials(HTTP_X_GUEST_SESSION=context["guest_session_token"])
        tab_id = self.post(guest, "/guest/tabs/", status=201)["id"]
        self.order(tab_id, quantity=3)
        body = {
            "idempotency_key": "guest-block",
            "lines": [{"product_id": str(self.product.id), "quantity": 1}],
            "limit_cents": 99999,
        }
        assert (
            self.post(guest, "/guest/orders/confirm/", body, status=409)["code"]
            == "SPENDING_LIMIT_EXCEEDED"
        )
        self.order(tab_id, key="staff-block", status=409)
        assert guest.get("/guest/context/").json()["tab"]["consumption_blocked"]
        self.post(guest, f"/tabs/{tab_id}/limit-override/", self.override(tab_id), status=401)

    def test_request_approval_is_audited_without_granting_capacity(self):
        tab_id = self.tab()
        self.post(
            self.staff,
            f"/tabs/{tab_id}/approval-request/",
            {"reason": "Cliente pediu mais", "idempotency_key": "ask"},
        )
        self.post(
            self.staff,
            f"/tabs/{tab_id}/approval-request/",
            {"reason": "Cliente pediu mais", "idempotency_key": "ask"},
        )
        assert AuditEvent.objects.filter(event_type="tab.limit_approval_requested").count() == 1
        assert self.detail(tab_id)["effective_limit_cents"] == 3000

    def test_cross_venue_customer_cannot_be_associated(self):
        other = Venue.objects.create(name="Other", slug="house-other")
        customer = Customer.objects.create(display_name="Outro cliente")
        Relationship.objects.create(venue=other, customer=customer)
        tab_id = self.tab()
        self.post(
            self.staff, f"/tabs/{tab_id}/customer/", {"customer_id": str(customer.id)}, status=404
        )

    def test_warning_at_eighty_percent(self):
        self.product.price_cents = 2400
        self.product.save()
        tab_id = self.tab()
        self.order(tab_id)
        assert self.detail(tab_id)["limit_warning"]
        assert self.detail(tab_id)["percentage_used"] == 80


@skipUnless(connection.vendor == "postgresql", "Row-lock concurrency proof requires PostgreSQL")
class HouseConcurrencyTests(HouseFixture, TransactionTestCase):
    def test_concurrent_orders_cannot_overspend(self):
        tab_id = self.tab()
        gate = Barrier(2)

        def worker(key):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                try:
                    confirm_order(
                        tab_id=tab_id,
                        source="STAFF",
                        actor=None,
                        lines=[{"product_id": self.product.id, "quantity": 2}],
                        idempotency_key=key,
                    )
                    return "CONFIRMED"
                except OrderingServiceError as error:
                    return error.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, ["first", "second"]))
        assert sorted(results) == ["CONFIRMED", "SPENDING_LIMIT_EXCEEDED"]
        assert exposure_cents(Tab.objects.get(pk=tab_id)) == 2000
        assert Charge.objects.count() == 1

    def test_concurrent_replay_creates_one_order(self):
        tab_id = self.tab()
        gate = Barrier(2)

        def worker(_):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                return confirm_order(
                    tab_id=tab_id,
                    source="STAFF",
                    actor=None,
                    lines=[{"product_id": self.product.id, "quantity": 3}],
                    idempotency_key="same",
                ).id
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, range(2)))
        assert results[0] == results[1]
        assert Charge.objects.count() == 1
