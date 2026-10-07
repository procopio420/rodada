from django.test import TestCase
from django.utils import timezone

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
