"""013-003 safe routing, preview revalidation and PostgreSQL races."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import Product
from modules.ordering.models import OrderItem, Tab
from modules.ordering.services import OrderingServiceError, confirm_order
from modules.venue.models import StationConfiguration, Venue
from modules.venue.stations import StationChangeError, apply_station_change, preview_station_change, station_snapshot


class StationFixtures:
    def setup_station(self):
        self.venue = Venue.objects.create(name="Station", slug="station")
        self.other = Venue.objects.create(name="Other", slug="station-other")
        self.staff = StaffMember.objects.create(display_name="Manager", login_identifier="station-manager")
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.MANAGER)
        self.client = APIClient()
        login = self.client.post("/auth/login/", {
            "venue_slug": self.venue.slug, "login_identifier": self.staff.login_identifier,
            "pin": "1234", "installation_id": "station-test", "platform": "WEB",
        }, format="json")
        assert login.status_code == 200, login.content
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        assert self.client.post("/auth/reauthenticate/", {"pin": "1234"}, format="json").status_code == 200
        self.session = StaffSession.objects.get(pk=login.json()["session_id"])
        self.actor = ActorContext.from_session(self.session)
        self.product = Product.objects.create(venue=self.venue, name="Food", price_cents=100,
                                              fulfillment_station="KITCHEN")
        self.tab = Tab.objects.create(venue=self.venue)

    def order(self, key="station-order"):
        return confirm_order(tab_id=self.tab.id, source="STAFF", actor=self.actor,
                             idempotency_key=key, lines=[{"product_id": self.product.id, "quantity": 1}])

    def apply(self, enabled=False, label="Kitchen", version=1):
        return apply_station_change(actor=self.actor, station="KITCHEN", enabled=enabled,
                                    label=label, expected_version=version, reason="Maintenance")


class StationConfigurationTests(StationFixtures, TestCase):
    def setUp(self):
        self.setup_station()

    def test_active_queue_blocks_apply_without_orphan_or_financial_mutation(self):
        order = self.order()
        original = list(order.items.values("id", "fulfillment_station_snapshot", "product_name_snapshot",
                                           "quantity", "unit_price_cents", "customization_snapshot"))
        preview = preview_station_change(venue_id=self.venue.id, station="KITCHEN", enabled=False,
                                         label="Kitchen", expected_version=1)
        assert preview["blockers"]["order_items"][0]["id"] == str(order.items.get().id)
        with self.assertRaises(StationChangeError) as error:
            self.apply()
        assert error.exception.code == "STATION_HAS_ACTIVE_WORK"
        assert station_snapshot(self.venue.id, "KITCHEN")["enabled"]
        assert order.items.get().state == "NEW"
        assert list(order.items.values("id", "fulfillment_station_snapshot", "product_name_snapshot",
                                       "quantity", "unit_price_cents", "customization_snapshot")) == original
        assert self.tab.charges.count() == 1
        assert not AuditEvent.objects.filter(entity_type="StationConfiguration").exists()

    def test_apply_rechecks_work_created_after_safe_preview(self):
        preview = preview_station_change(venue_id=self.venue.id, station="KITCHEN", enabled=False,
                                         label="", expected_version=1)
        assert preview["can_apply"]
        self.order()
        with self.assertRaises(StationChangeError):
            self.apply()

    def test_disabled_station_rejects_whole_mixed_order(self):
        self.apply()
        bar = Product.objects.create(venue=self.venue, name="Drink", price_cents=100, fulfillment_station="BAR")
        with self.assertRaises(OrderingServiceError) as error:
            confirm_order(tab_id=self.tab.id, source="GUEST", lines=[
                {"product_id": self.product.id, "quantity": 1}, {"product_id": bar.id, "quantity": 1}])
        assert error.exception.code == "STATION_DISABLED"
        assert self.tab.orders.count() == self.tab.charges.count() == 0

    def test_idempotent_replay_of_delivered_order_survives_station_disable(self):
        order = self.order()
        OrderItem.objects.filter(order=order).update(state="DELIVERED")
        self.apply()
        assert self.order().id == order.id
        assert self.tab.orders.count() == self.tab.charges.count() == 1

    def test_stale_version_preserves_winner_and_audit_provenance(self):
        self.apply(enabled=True, label="Winner")
        with self.assertRaises(StationChangeError) as error:
            self.apply(label="Loser")
        assert error.exception.code == "STALE_VERSION"
        assert error.exception.details["current"]["label"] == "Winner"
        event = AuditEvent.objects.get(entity_type="StationConfiguration")
        assert event.actor_session_id == self.session.id
        assert event.device_id == self.session.device_id
        assert event.metadata["before"]["version"] == 1
        assert event.metadata["after"]["version"] == 2
        assert event.reason == "Maintenance"

    def test_cross_venue_policy_and_work_not_exposed_or_mutated(self):
        StationConfiguration.objects.create(venue=self.other, station="KITCHEN", enabled=False, label="Private")
        self.apply(enabled=True)
        assert station_snapshot(self.venue.id, "KITCHEN")["label"] == "Kitchen"
        assert station_snapshot(self.other.id, "KITCHEN")["label"] == "Private"

    def test_revoked_permission_revalidated_inside_command(self):
        VenueStaffMembership.objects.filter(pk=self.membership.pk).update(role=StaffRole.STAFF)
        from modules.access.services import AccessServiceError
        with self.assertRaises(AccessServiceError):
            self.apply()
        assert not StationConfiguration.objects.exists()

    def test_online_api_strict_fields_and_reauthentication(self):
        assert self.client.get("/management/stations/").status_code == 200
        response = self.client.post("/management/stations/KITCHEN/preview/", {
            "expected_version": 1, "enabled": False, "arbitrary_setting": True}, format="json")
        assert response.status_code == 400
        StaffSession.objects.filter(pk=self.session.pk).update(recently_reauthenticated_at=None)
        response = self.client.post("/management/stations/KITCHEN/apply/", {
            "expected_version": 1, "enabled": False}, format="json")
        assert response.status_code == 403
        assert response.json()["code"] == "REAUTH_REQUIRED"

    def test_api_stale_version_returns_current_configuration(self):
        self.apply(enabled=True, label="Winner")
        response = self.client.post("/management/stations/KITCHEN/apply/", {
            "expected_version": 1, "enabled": False, "label": "Loser"}, format="json")
        assert response.status_code == 409
        assert response.json()["code"] == "STALE_VERSION"
        assert response.json()["current"]["version"] == 2
        assert response.json()["current"]["label"] == "Winner"
        assert StationConfiguration.objects.get().enabled


class StationConcurrencyTests(StationFixtures, TransactionTestCase):
    def setUp(self):
        self.setup_station()

    def run_race(self, commands):
        assert connection.vendor == "postgresql", "PostgreSQL required for row-lock evidence"
        barrier = Barrier(2)
        def run(command):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    command()
                    return "OK"
                except (StationChangeError, OrderingServiceError) as exc:
                    return exc.code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, commands))

    def test_two_editors_one_winner_one_conflict(self):
        result = self.run_race([lambda: self.apply(enabled=True, label="A"),
                                lambda: self.apply(enabled=True, label="B")])
        assert sorted(result) == ["OK", "STALE_VERSION"]
        assert StationConfiguration.objects.get().version == 2
        assert AuditEvent.objects.filter(entity_type="StationConfiguration").count() == 1

    def test_order_and_disable_cannot_commit_orphan(self):
        result = self.run_race([self.order, self.apply])
        assert "OK" in result
        if self.tab.orders.exists():
            assert "STATION_HAS_ACTIVE_WORK" in result
            assert station_snapshot(self.venue.id, "KITCHEN")["enabled"]
        else:
            assert "STATION_DISABLED" in result
            assert not station_snapshot(self.venue.id, "KITCHEN")["enabled"]
