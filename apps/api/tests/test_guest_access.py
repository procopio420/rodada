from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import AvailabilityState, FulfillmentStation, Product
from modules.guest_access.models import GuestSession
from modules.guest_access.services import (
    GuestAccessError,
    confirm_guest_order,
    create_or_get_guest_tab,
    guest_catalog,
    guest_session_context,
    resolve_table_qr,
)
from modules.hospitality.models import GuestOrderingMode, Table, TableOccupancy, TableStatus
from modules.ordering.models import OrderSource
from modules.venue.models import Venue


class GuestAccessServiceTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Guest Bar", slug="guest-bar")
        self.table = Table.objects.create(
            venue=self.venue,
            label="27",
            guest_ordering_mode=GuestOrderingMode.DIRECT,
        )
        self.product = Product.objects.create(
            venue=self.venue,
            name="Cerveja",
            price_cents=1400,
            fulfillment_station=FulfillmentStation.BAR,
        )

    def resolve(self, *, existing_session_token=""):
        return resolve_table_qr(
            public_token=self.table.public_token,
            existing_session_token=existing_session_token,
        )

    def test_qr_is_opaque_and_direct_scan_only_claims_table_when_tab_is_created(self):
        resolution = self.resolve()

        assert resolution.session.table_id == self.table.id
        assert resolution.session.occupancy_id is None
        assert resolution.session.tab_id is None
        assert resolution.token != str(self.table.id)
        assert GuestSession.objects.get(pk=resolution.session.id).token_digest != resolution.token
        assert not TableOccupancy.objects.filter(table=self.table).exists()

        tab = create_or_get_guest_tab(session_token=resolution.token, display_label="Ana")
        assignment = tab.occupancy_assignments.get(released_at__isnull=True)
        self.table.refresh_from_db()
        resolution.session.refresh_from_db()

        assert tab.venue_id == self.venue.id
        assert assignment.assigned_by_id is None
        assert self.table.status == TableStatus.OCCUPIED
        assert resolution.session.occupancy_id == assignment.occupancy_id
        assert resolution.session.tab_id == tab.id
        assert AuditEvent.objects.filter(
            venue=self.venue,
            event_type="guest_tab.created",
            entity_id=str(tab.id),
            actor_staff__isnull=True,
        ).exists()

    def test_join_active_requires_existing_occupancy_and_disabled_never_issues_session(self):
        self.table.guest_ordering_mode = GuestOrderingMode.JOIN_ACTIVE
        self.table.save(update_fields=["guest_ordering_mode"])
        with self.assertRaises(GuestAccessError) as captured:
            self.resolve()
        assert captured.exception.code == "ACTIVE_OCCUPANCY_REQUIRED"

        self.table.guest_ordering_mode = GuestOrderingMode.DISABLED
        self.table.save(update_fields=["guest_ordering_mode"])
        with self.assertRaises(GuestAccessError) as captured:
            self.resolve()
        assert captured.exception.code == "GUEST_ORDERING_DISABLED"
        assert GuestSession.objects.count() == 0

    def test_guest_order_uses_canonical_pipeline_and_revalidates_stale_availability(self):
        resolution = self.resolve()
        tab = create_or_get_guest_tab(session_token=resolution.token)

        order = confirm_guest_order(
            session_token=resolution.token,
            lines=[{"product_id": self.product.id, "quantity": 2}],
            idempotency_key="guest-order-1",
        )
        order.refresh_from_db()
        assert order.tab_id == tab.id
        assert order.source == OrderSource.GUEST
        assert order.items.get().unit_price_cents == 1400
        assert tab.charges.get(order_item=order.items.get()).amount_cents == 2800

        self.product.availability.state = AvailabilityState.UNAVAILABLE
        self.product.availability.version += 1
        self.product.availability.save(update_fields=["state", "version", "changed_at"])
        with self.assertRaises(GuestAccessError) as captured:
            confirm_guest_order(
                session_token=resolution.token,
                lines=[{"product_id": self.product.id, "quantity": 1}],
                idempotency_key="stale-guest-cart",
            )
        assert captured.exception.code == "PRODUCTS_NOT_CONFIRMABLE"
        assert (
            guest_catalog(session_token=resolution.token).get(pk=self.product.id).availability.state
            == "UNAVAILABLE"
        )

    def test_guest_order_replays_safely_but_rejects_same_key_with_new_intent(self):
        resolution = self.resolve()
        create_or_get_guest_tab(session_token=resolution.token)
        lines = [{"product_id": self.product.id, "quantity": 1}]
        first = confirm_guest_order(
            session_token=resolution.token, lines=lines, idempotency_key="same-command"
        )
        replay = confirm_guest_order(
            session_token=resolution.token, lines=lines, idempotency_key="same-command"
        )
        assert first.id == replay.id
        assert getattr(replay, "_idempotency_replay", False)
        with self.assertRaises(GuestAccessError) as captured:
            confirm_guest_order(
                session_token=resolution.token,
                lines=[{"product_id": self.product.id, "quantity": 2}],
                idempotency_key="same-command",
            )
        assert captured.exception.code == "IDEMPOTENCY_CONFLICT"

    def test_old_session_cannot_order_after_release_and_new_visit_is_distinct(self):
        old = self.resolve()
        create_or_get_guest_tab(session_token=old.token)
        occupancy = TableOccupancy.objects.get(table=self.table, released_at__isnull=True)
        occupancy.released_at = timezone.now()
        occupancy.save(update_fields=["released_at"])
        self.table.status = TableStatus.DIRTY
        self.table.save(update_fields=["status"])

        with self.assertRaises(GuestAccessError) as captured:
            confirm_guest_order(
                session_token=old.token,
                lines=[{"product_id": self.product.id, "quantity": 1}],
                idempotency_key="after-release",
            )
        assert captured.exception.code == "GUEST_SESSION_REVOKED"

        self.table.status = TableStatus.AVAILABLE
        self.table.access_generation += 1
        self.table.save(update_fields=["status", "access_generation"])
        fresh = self.resolve()
        new_tab = create_or_get_guest_tab(session_token=fresh.token)
        assert fresh.session.id != old.session.id
        assert new_tab.id != old.session.tab_id

    def test_operational_block_rejects_guest_mutation_without_changing_tab_or_history(self):
        resolution = self.resolve()
        tab = create_or_get_guest_tab(session_token=resolution.token)
        self.table.guest_ordering_blocked = True
        self.table.save(update_fields=["guest_ordering_blocked"])

        with self.assertRaises(GuestAccessError) as captured:
            confirm_guest_order(
                session_token=resolution.token,
                lines=[{"product_id": self.product.id, "quantity": 1}],
                idempotency_key="blocked-order",
            )
        assert captured.exception.code == "GUEST_ORDERING_BLOCKED"
        assert not tab.orders.exists()
        assert guest_session_context(session_token=resolution.token).tab_id == tab.id


class GuestAccessApiTests(TestCase):
    def setUp(self):
        self.guest_client = APIClient()
        self.staff_client = APIClient()
        self.venue = Venue.objects.create(name="Guest API Bar", slug="guest-api-bar")
        self.table = Table.objects.create(
            venue=self.venue,
            label="9",
            guest_ordering_mode=GuestOrderingMode.DIRECT,
        )
        self.product = Product.objects.create(
            venue=self.venue,
            name="Caipirinha",
            price_cents=2200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        staff = StaffMember.objects.create(display_name="Bia", login_identifier="guest-api-bia")
        staff.set_pin("1234")
        staff.save(update_fields=["pin_hash"])
        VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=staff, role=StaffRole.STAFF
        )
        login = self.staff_client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "1234",
                "installation_id": "guest-api-test-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.staff_client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])

    def test_guest_http_flow_uses_only_guest_endpoints_and_feeds_production(self):
        resolved = self.guest_client.post(
            "/guest/qr/resolve/", {"token": self.table.public_token}, format="json"
        )
        assert resolved.status_code == 201, resolved.json()
        session_token = resolved.json()["guest_session_token"]
        self.guest_client.credentials(HTTP_X_GUEST_SESSION=session_token)

        assert self.guest_client.get("/guest/catalog/").status_code == 200
        tab = self.guest_client.post("/guest/tabs/", {"display_label": "Ana"}, format="json")
        assert tab.status_code == 201, tab.json()
        order = self.guest_client.post(
            "/guest/orders/confirm/",
            {
                "idempotency_key": "guest-http-order",
                "lines": [{"product_id": str(self.product.id), "quantity": 1}],
            },
            format="json",
        )
        assert order.status_code == 201, order.json()
        assert order.json()["source"] == OrderSource.GUEST

        # A guest bearer is not accepted by staff-authenticated surfaces.
        assert self.guest_client.get(f"/tabs/{tab.json()['id']}/").status_code == 401
        queue = self.staff_client.get("/production/BAR/")
        assert queue.status_code == 200, queue.json()
        assert [item["id"] for item in queue.json()["results"]] == [order.json()["items"][0]["id"]]
