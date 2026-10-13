"""Spec 027: real API contracts and durable domain invariants."""

from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.hospitality.models import ServiceCommand, Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Order, OrderItem, Tab
from modules.venue.models import Venue


class TableServiceTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Bar", slug="spec027", table_service_enabled=True)
        self.table = Table.objects.create(
            venue=self.venue, label="12", guest_ordering_mode="DIRECT"
        )
        self.staff, self.client = self.login("ana")
        self.other, self.other_client = self.login("bia")

    def login(self, name, venue=None):
        staff = StaffMember.objects.create(display_name=name, login_identifier=name)
        staff.set_pin("1234")
        staff.save()
        VenueStaffMembership.objects.create(
            venue=venue or self.venue, staff_member=staff, role=StaffRole.STAFF
        )
        client = APIClient()
        r = client.post(
            "/auth/login/",
            {
                "venue_slug": (venue or self.venue).slug,
                "login_identifier": name,
                "pin": "1234",
                "installation_id": name,
                "platform": "WEB",
            },
            format="json",
        )
        assert r.status_code == 200, r.json()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + r.json()["access_token"])
        return staff, client

    def start(self, client=None, key="start"):
        return (client or self.client).post(
            f"/hospitality/tables/{self.table.id}/service/start/",
            {"idempotency_key": key},
            format="json",
        )

    def open(self, occupancy, key="open", client=None, **extra):
        return (client or self.client).post(
            f"/hospitality/occupancies/{occupancy.id}/tabs/open/",
            {"idempotency_key": key, "expected_generation": occupancy.generation, **extra},
            format="json",
        )

    def claim(self, occupancy, client=None, key="claim", **extra):
        return (client or self.client).post(
            f"/hospitality/occupancies/{occupancy.id}/responsibility/claim/",
            {
                "idempotency_key": key,
                "expected_responsibility_version": occupancy.responsibility_version,
                "mode": "CLAIM_UNASSIGNED",
                **extra,
            },
            format="json",
        )

    def test_start_no_financial_side_effects_replay_and_conflicts(self):
        result = self.start()
        assert result.status_code == 201, result.json()
        occupancy = TableOccupancy.objects.get(table=self.table)
        assert occupancy.responsible_staff_id == self.staff.id
        assert not Tab.objects.exists() and not Order.objects.exists()
        assert not occupancy.party_size_observations.exists()
        replay = self.start()
        assert replay.status_code == 200 and replay.json()["replayed"]
        assert TableOccupancy.objects.count() == 1
        assert (
            AuditEvent.objects.filter(event_type="occupancy.responsibility_assigned").count() == 1
        )
        assert self.start(self.other_client, "other").json()["code"] == "OCCUPANCY_ALREADY_ACTIVE"
        other_table = Table.objects.create(venue=self.venue, label="13")
        mismatch = self.client.post(
            f"/hospitality/tables/{other_table.id}/service/start/",
            {"idempotency_key": "start"},
            format="json",
        )
        assert mismatch.status_code == 409 and mismatch.json()["code"] == "IDEMPOTENCY_CONFLICT"
        assert ServiceCommand.objects.count() == 1

    def test_open_atomic_replay_homonyms_and_release(self):
        self.start()
        occupancy = TableOccupancy.objects.get(table=self.table)
        first = self.open(occupancy, display_label="João")
        second = self.open(occupancy, key="second", display_label="João", client=self.other_client)
        assert first.status_code == second.status_code == 201
        assert first.json()["tab_id"] != second.json()["tab_id"]
        assert self.open(occupancy, display_label="João").json()["tab_id"] == first.json()["tab_id"]
        assert (
            self.open(occupancy, display_label="Different").json()["code"] == "IDEMPOTENCY_CONFLICT"
        )
        occupancy.refresh_from_db()
        assert occupancy.responsible_staff_id == self.staff.id
        listing = self.client.get("/hospitality/tables/").json()["results"][0]["active_occupancy"]
        assert len(listing["tabs"]) == 2
        assert len({t["display_reference"] for t in listing["tabs"]}) == 2
        self.client.post(f"/hospitality/tables/{self.table.id}/release/", {}, format="json")
        assert self.open(occupancy, key="after").json()["code"] == "OCCUPANCY_RELEASED"
        assert Tab.objects.count() == 2
        assert self.open(occupancy, display_label="João").status_code == 200

    def test_assignment_failure_rolls_back_tab_audit_and_intent(self):
        self.start()
        occupancy = TableOccupancy.objects.get(table=self.table)
        from modules.hospitality.services import HospitalityServiceError

        with patch(
            "modules.hospitality.table_service._assign_tab",
            side_effect=HospitalityServiceError("TEST", "Failure", 409),
        ):
            assert self.open(occupancy).status_code == 409
        assert not Tab.objects.exists()
        assert not AuditEvent.objects.filter(event_type="tab.opened").exists()
        assert not ServiceCommand.objects.filter(action="open").exists()

    def test_explicit_claim_cas_noop_takeover_and_guest_compatibility(self):
        from modules.access.context import ActorContext
        from modules.access.models import StaffSession
        from modules.hospitality.services import occupy_table

        actor = ActorContext.from_session(
            StaffSession.objects.filter(staff_member=self.staff).first()
        )
        occupancy = occupy_table(table_id=self.table.id, actor=actor)
        assert occupancy.responsible_staff_id is None
        result = self.claim(occupancy)
        assert result.status_code == 201
        assert (
            self.claim(occupancy, client=self.other_client).json()["code"]
            == "RESPONSIBILITY_CONFLICT"
        )
        occupancy.refresh_from_db()
        assert self.claim(occupancy, key="noop").json()["unchanged"]
        assert (
            AuditEvent.objects.filter(event_type="occupancy.responsibility_assigned").count() == 1
        )
        result = self.claim(occupancy, client=self.other_client, key="transfer", mode="TAKE_OVER")
        assert result.status_code == 201
        occupancy.refresh_from_db()
        assert (
            occupancy.responsibility_version == 2
            and occupancy.responsible_staff_id == self.other.id
        )
        assert (
            AuditEvent.objects.filter(event_type="occupancy.responsibility_transferred").count()
            == 1
        )

    def test_invalid_generation_customer_and_venue(self):
        self.start()
        occupancy = TableOccupancy.objects.get(table=self.table)
        assert (
            self.open(occupancy, expected_generation=999).json()["code"] == "STALE_TABLE_GENERATION"
        )
        import uuid

        assert (
            self.open(occupancy, customer_id=str(uuid.uuid4())).json()["code"]
            == "CUSTOMER_NOT_FOUND_OR_OTHER_VENUE"
        )
        other_venue = Venue.objects.create(name="Other", slug="other027")
        _, stranger = self.login("stranger", other_venue)
        assert self.open(occupancy, client=stranger).status_code == 404
        assert self.start(stranger).status_code == 404
        assert self.claim(occupancy, client=stranger).status_code == 404
        assert stranger.get("/hospitality/tables/").json()["results"] == []
        assert (
            APIClient()
            .post(f"/hospitality/tables/{self.table.id}/service/start/", {"idempotency_key": "x"})
            .status_code
            == 401
        )

    def test_unassigned_attention_canonical_aggregation_and_constant_queries(self):
        from modules.catalog.models import Product

        self.table.status = "OCCUPIED"
        self.table.save()
        occupancy = TableOccupancy.objects.create(table=self.table, generation=1)
        tab = Tab.objects.create(venue=self.venue)
        TabOccupancyAssignment.objects.create(occupancy=occupancy, tab=tab)
        listing = lambda: self.client.get("/hospitality/tables/").json()["results"][0][
            "active_occupancy"
        ]
        assert listing()["unassigned_service_attention"] == "UNASSIGNED_NO_ORDER"
        product = Product.objects.create(
            venue=self.venue, name="Beer", price_cents=100, fulfillment_station="BAR"
        )
        for _ in range(2):
            order = Order.objects.create(tab=tab, source="GUEST")
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name_snapshot="Beer",
                unit_price_cents=100,
                quantity=1,
                state="NEW",
            )
        projection = listing()
        assert projection["unassigned_service_attention"] == "UNASSIGNED_GUEST_ORDER"
        assert projection["unassigned_guest_order_count"] == 2
        item = OrderItem.objects.first()
        item.state = "READY"
        item.save()
        assert listing()["unassigned_service_attention"] == "UNASSIGNED_READY"
        with CaptureQueriesContext(connection) as small:
            self.client.get("/hospitality/tables/")
        for i in range(8):
            table = Table.objects.create(venue=self.venue, label=f"X{i}", status="OCCUPIED")
            TableOccupancy.objects.create(table=table, generation=1)
        with CaptureQueriesContext(connection) as large:
            self.client.get("/hospitality/tables/")
        assert len(large) == len(small), (len(small), len(large))
        assert self.claim(occupancy).status_code == 201
        assert listing()["unassigned_service_attention"] == "NONE"

    def test_real_direct_qr_replay_claim_preserves_guest_and_cycle_revokes(self):
        from modules.access.context import ActorContext
        from modules.access.models import StaffSession
        from modules.catalog.models import Product
        from modules.guest_access.services import (
            confirm_guest_order,
            create_or_get_guest_tab,
            guest_session_context,
            resolve_table_qr,
        )
        from modules.guest_access.views import _context_payload
        from modules.ordering.services import transition_order_item

        resolution = resolve_table_qr(public_token=self.table.public_token)
        assert not TableOccupancy.objects.exists()
        tab = create_or_get_guest_tab(session_token=resolution.token)
        occupancy = TableOccupancy.objects.get(table=self.table)
        assert occupancy.responsible_staff_id is None
        product = Product.objects.create(
            venue=self.venue, name="QR beer", price_cents=100, fulfillment_station="BAR"
        )
        command = {
            "session_token": resolution.token,
            "lines": [{"product_id": product.id, "quantity": 1}],
            "idempotency_key": "guest-intent",
        }
        order = confirm_guest_order(**command)
        assert confirm_guest_order(**command).id == order.id
        projection = self.client.get("/hospitality/tables/").json()["results"][0][
            "active_occupancy"
        ]
        assert projection["unassigned_guest_order_count"] == 1
        assert projection["unassigned_service_attention"] == "UNASSIGNED_GUEST_ORDER"
        actor = ActorContext.from_session(
            StaffSession.objects.filter(staff_member=self.staff).first()
        )
        item = order.items.get()
        for state in ("ACCEPTED", "PREPARING", "READY"):
            transition_order_item(item_id=item.id, target_state=state, actor=actor)
        projection = self.client.get("/hospitality/tables/").json()["results"][0][
            "active_occupancy"
        ]
        assert projection["unassigned_service_attention"] == "UNASSIGNED_READY"
        assert self.claim(occupancy).status_code == 201
        session = guest_session_context(session_token=resolution.token)
        assert session.tab_id == tab.id and session.occupancy_id == occupancy.id
        payload = _context_payload(session)
        assert "responsible" not in str(payload) and "unassigned" not in str(payload)
        assert (
            self.client.get("/hospitality/tables/").json()["results"][0]["active_occupancy"][
                "unassigned_service_attention"
            ]
            == "NONE"
        )
        self.client.post(f"/hospitality/tables/{self.table.id}/release/", {}, format="json")
        assert (
            self.client.get("/hospitality/tables/").json()["results"][0]["active_occupancy"] is None
        )
        from modules.guest_access.services import GuestAccessError

        with self.assertRaises(GuestAccessError):
            guest_session_context(session_token=resolution.token)
        self.client.post(f"/hospitality/tables/{self.table.id}/cleaning/start/", {}, format="json")
        self.client.post(
            f"/hospitality/tables/{self.table.id}/cleaning/complete/", {}, format="json"
        )
        assert self.start(key="next-visit").status_code == 201
        current = TableOccupancy.objects.get(table=self.table, released_at__isnull=True)
        assert current.id != occupancy.id and current.generation == 2
        assert current.responsible_staff_id == self.staff.id
        assert (
            self.client.get("/hospitality/tables/").json()["results"][0]["active_occupancy"][
                "unassigned_service_attention"
            ]
            == "NONE"
        )

    def test_helping_waiter_confirms_order_without_taking_responsibility(self):
        from modules.access.context import ActorContext
        from modules.access.models import StaffSession
        from modules.catalog.models import Product
        from modules.ordering.services import confirm_order

        self.start()
        occupancy = TableOccupancy.objects.get(table=self.table)
        opened = self.open(occupancy, client=self.other_client)
        product = Product.objects.create(
            venue=self.venue, name="Helper beer", price_cents=100, fulfillment_station="BAR"
        )
        actor = ActorContext.from_session(
            StaffSession.objects.filter(staff_member=self.other).first()
        )
        order = confirm_order(
            tab_id=opened.json()["tab_id"],
            source="STAFF",
            actor=actor,
            lines=[{"product_id": product.id, "quantity": 1}],
            idempotency_key="helper-order",
        )
        assert order.confirmed_by_id == self.other.id
        occupancy.refresh_from_db()
        assert occupancy.responsible_staff_id == self.staff.id
        assert occupancy.responsibility_version == 1
        assert not AuditEvent.objects.filter(
            event_type="occupancy.responsibility_transferred"
        ).exists()

    def test_disabled_rejects_new_but_replays_committed_intent(self):
        first = self.start()
        self.venue.table_service_enabled = False
        self.venue.save(update_fields=["table_service_enabled"])
        self.assertEqual(self.start(key="new").json()["code"], "TABLE_SERVICE_DISABLED")
        replay = self.start()
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["active_occupancy"], first.json()["active_occupancy"])
        occupancy = TableOccupancy.objects.get()
        self.assertEqual(self.open(occupancy).json()["code"], "TABLE_SERVICE_DISABLED")
        self.assertEqual(self.claim(occupancy).json()["code"], "TABLE_SERVICE_DISABLED")
        self.assertFalse(Tab.objects.exists())

    def test_rollout_authorization_cas_audit_and_replay(self):
        path = "/management/table-service-rollout/"
        body = {"enabled": False, "expected_version": 1, "idempotency_key": "rollback"}
        self.assertEqual(self.client.post(path, body, format="json").status_code, 403)
        membership = VenueStaffMembership.objects.get(staff_member=self.staff)
        membership.role = StaffRole.MANAGER
        membership.save()
        result = self.client.post(path, body, format="json")
        self.assertEqual(result.status_code, 200, result.json())
        self.assertEqual(result.json()["version"], 2)
        self.assertTrue(self.client.post(path, body, format="json").json()["replayed"])
        body["idempotency_key"] = "stale"
        self.assertEqual(self.client.post(path, body, format="json").status_code, 409)
        self.assertEqual(AuditEvent.objects.filter(event_type="table_service.rollout_changed").count(), 1)
        self.venue.refresh_from_db()
        self.assertFalse(self.venue.table_service_enabled)

    def test_two_tabs_qr_helper_and_move_preserve_identity_and_ownership(self):
        from modules.catalog.models import Product
        from modules.guest_access.services import (
            confirm_guest_order,
            create_or_get_guest_tab,
            resolve_table_qr,
        )
        from modules.ledger.models import Charge, Payment
        resolution = resolve_table_qr(public_token=self.table.public_token)
        guest_tab = create_or_get_guest_tab(session_token=resolution.token)
        occupancy = TableOccupancy.objects.get(table=self.table)
        self.assertEqual(self.claim(occupancy).status_code, 201)
        staff_tab_response = self.open(occupancy, display_label="João")
        self.assertEqual(staff_tab_response.status_code, 201)
        staff_tab = Tab.objects.get(pk=staff_tab_response.json()["tab_id"])
        product = Product.objects.create(venue=self.venue, name="Ensaio 027", price_cents=100, fulfillment_station="BAR")
        guest_order = confirm_guest_order(session_token=resolution.token,
            lines=[{"product_id": product.id, "quantity": 1}], idempotency_key="rehearsal-qr")
        helper = self.other_client.post(f"/tabs/{staff_tab.id}/orders/confirm/",
            {"lines": [{"product_id": str(product.id), "quantity": 1}], "idempotency_key": "rehearsal-helper"}, format="json")
        self.assertEqual(helper.status_code, 201, helper.json())
        helper_order = Order.objects.get(pk=helper.json()["id"])
        self.assertEqual(helper_order.confirmed_by_id, self.other.id)
        occupancy.refresh_from_db()
        self.assertEqual(occupancy.responsible_staff_id, self.staff.id)
        destination = Table.objects.create(venue=self.venue, label="13")
        started = self.client.post(f"/hospitality/tables/{destination.id}/service/start/", {"idempotency_key": "rehearsal-destination"}, format="json")
        self.assertEqual(started.status_code, 201)
        destination_visit = TableOccupancy.objects.get(table=destination)
        staff_tab.refresh_from_db()
        before = list(Charge.objects.filter(tab=staff_tab).values_list("id", "amount_cents"))
        command = {"kind": "MOVE_LOCATION", "expected_version": staff_tab.version,
                   "occupancy_id": str(destination_visit.id), "idempotency_key": "rehearsal-move"}
        path = f"/tabs/{staff_tab.id}/operations/"
        moved = self.other_client.post(path, command, format="json")
        self.assertEqual(moved.status_code, 200, moved.json())
        self.assertEqual(self.other_client.post(path, command, format="json").status_code, 200)
        self.assertEqual(list(Charge.objects.filter(tab=staff_tab).values_list("id", "amount_cents")), before)
        self.assertEqual(TabOccupancyAssignment.objects.get(tab=staff_tab, released_at__isnull=True).occupancy_id, destination_visit.id)
        self.assertEqual(TabOccupancyAssignment.objects.get(tab=guest_tab, released_at__isnull=True).occupancy_id, occupancy.id)
        self.assertEqual(guest_order.tab_id, guest_tab.id)
        occupancy.refresh_from_db()
        self.assertEqual(occupancy.responsible_staff_id, self.staff.id)
        self.assertFalse(Payment.objects.exists())
