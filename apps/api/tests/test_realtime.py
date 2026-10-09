"""Spec 014: durable delivery, recovery and authorization of realtime facts."""

import asyncio
import json
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.models import StaffMember, StaffRole, VenueStaffMembership
from modules.catalog.models import FulfillmentStation, Product
from modules.guest_access.services import create_or_get_guest_tab, resolve_table_qr
from modules.hospitality.models import GuestOrderingMode, Table
from modules.ordering.models import OrderSource, Tab
from modules.ordering.services import confirm_order
from modules.realtime.models import OutboxEvent
from modules.realtime.services import dispatch_pending, emit_event
from modules.venue.models import Venue


def frames(response):
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/event-stream")
    body = b"".join(response.streaming_content).decode()
    result = []
    for block in body.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                fields[key] = value
        if "data" in fields:
            fields["data"] = json.loads(fields["data"])
            result.append(fields)
    return result


class RealtimeTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Realtime", slug="realtime-tests")
        self.other = Venue.objects.create(name="Other", slug="realtime-other")
        self.tab = Tab.objects.create(venue=self.venue)
        self.product = Product.objects.create(
            venue=self.venue,
            name="Beer",
            price_cents=1200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        self.client = APIClient()
        staff = StaffMember.objects.create(display_name="Ana", login_identifier="realtime-ana")
        staff.set_pin("1234")
        staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=staff, role=StaffRole.MANAGER
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": staff.login_identifier,
                "pin": "1234",
                "installation_id": "realtime-tests",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])

    def emit(self, *, venue=None, tab=None):
        with transaction.atomic():
            return emit_event(
                venue_id=(venue or self.venue).id,
                event_type="order.confirmed",
                aggregate_type="Order",
                aggregate_id=self.tab.id,
                tab_id=(tab or self.tab).id,
            )

    def stream(self, cursor):
        dispatch_pending()
        return frames(
            self.client.get(
                "/realtime/stream/",
                {"once": "1"},
                HTTP_LAST_EVENT_ID=str(cursor),
                HTTP_ACCEPT="text/event-stream",
            )
        )

    def test_domain_mutation_and_outbox_rollback_together(self):
        initial = OutboxEvent.objects.count()
        with self.assertRaises(RuntimeError), transaction.atomic():
            confirm_order(
                tab_id=self.tab.id,
                source=OrderSource.STAFF,
                lines=[{"product_id": self.product.id, "quantity": 1}],
                actor=None,
                idempotency_key="rolled-back",
            )
            assert OutboxEvent.objects.count() > initial
            raise RuntimeError("failure after domain write")
        assert self.tab.orders.count() == 0
        assert self.tab.charges.count() == 0
        assert OutboxEvent.objects.count() == initial

    def test_customization_invalidates_shared_products_without_audit_payload(self):
        from modules.audit.models import AuditEvent
        from modules.catalog.models import ModifierGroup, ModifierOption, ProductModifierGroup
        from modules.realtime.views import visible
        from types import SimpleNamespace

        group = ModifierGroup.objects.create(venue=self.venue, name="Extras", selection_mode="MULTI")
        option = ModifierOption.objects.create(group=group, name="Extra")
        second = Product.objects.create(venue=self.venue, name="Second", price_cents=1200, fulfillment_station=FulfillmentStation.BAR)
        for product in (self.product, second):
            ProductModifierGroup.objects.create(product=product, group=group)
        for event_type, entity in (("catalog.option_availability_changed", option), ("catalog.customization_configured", group)):
            with transaction.atomic():
                AuditEvent.objects.create(venue=self.venue, event_type=event_type, entity_type=entity.__class__.__name__, entity_id=str(entity.pk), metadata={"product_id": str(self.product.id), "private": "audit-only"})
            events = OutboxEvent.objects.filter(event_type=event_type)
            assert set(events.values_list("aggregate_id", flat=True)) == {str(self.product.id), str(second.id)}
            assert all(event.aggregate_type == "Product" and event.payload == {} and event.tab_id is None for event in events)
            assert all(visible(event, SimpleNamespace(tab_id=None), True) for event in events)
            assert all(visible(event, SimpleNamespace(membership=self.membership), False) for event in events)

    def test_idempotent_http_command_emits_one_fact(self):
        payload = {
            "idempotency_key": "duplicate-command",
            "lines": [{"product_id": str(self.product.id), "quantity": 1}],
        }
        first = self.client.post(f"/tabs/{self.tab.id}/orders/confirm/", payload, format="json")
        count = OutboxEvent.objects.count()
        replay = self.client.post(f"/tabs/{self.tab.id}/orders/confirm/", payload, format="json")
        assert first.status_code == 201, first.json()
        assert replay.status_code == 200, replay.json()
        assert first.json()["id"] == replay.json()["id"]
        assert OutboxEvent.objects.count() == count
        assert self.tab.orders.count() == self.tab.charges.count() == 1

    def test_unauthenticated_stream_and_snapshot_rejected(self):
        client = APIClient()
        for endpoint in ("/realtime/stream/?once=1", "/realtime/snapshot/"):
            assert client.get(endpoint).status_code == 401

    def test_unknown_cursor_requires_snapshot(self):
        self.emit()
        result = self.stream("999999999")
        assert any(frame.get("event") == "reset" for frame in result)
        assert not any(frame.get("event") == "change" for frame in result)

    def guest(self, label):
        table = Table.objects.create(
            venue=self.venue, label=label, guest_ordering_mode=GuestOrderingMode.DIRECT
        )
        resolved = resolve_table_qr(public_token=table.public_token)
        tab = create_or_get_guest_tab(session_token=resolved.token)
        client = APIClient()
        client.credentials(HTTP_X_GUEST_SESSION=resolved.token)
        return client, resolved, tab

    def test_revoked_guest_cannot_read_snapshot_or_subscribe(self):
        client, resolved, _ = self.guest("1")
        resolved.session.revoked_at = timezone.now()
        resolved.session.save(update_fields=["revoked_at"])
        for endpoint in ("/guest/realtime/snapshot/", "/guest/realtime/stream/?once=1"):
            assert client.get(endpoint).status_code in (401, 403)

    def test_resume_replays_missed_facts_and_not_already_accepted_cursor(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.emit()
        self.emit()
        changes = [frame for frame in self.stream(baseline) if frame.get("event") == "change"]
        assert len(changes) == 2
        assert changes[0]["id"] != changes[1]["id"]
        resumed = [
            frame for frame in self.stream(changes[0]["id"]) if frame.get("event") == "change"
        ]
        assert [frame["id"] for frame in resumed] == [changes[1]["id"]]
        assert not any(frame.get("event") == "change" for frame in self.stream(changes[-1]["id"]))

    def test_staff_scope_cannot_be_overridden_with_venue_query(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.emit(venue=self.other)
        dispatch_pending()
        response = self.client.get(
            "/realtime/stream/",
            {"once": "1", "venue_id": str(self.other.id)},
            HTTP_LAST_EVENT_ID=baseline,
        )
        assert not any(frame.get("event") == "change" for frame in frames(response))

    def test_guest_scope_ignores_other_tab_and_venue_selection(self):
        client, _, tab = self.guest("2")
        baseline = client.get("/guest/realtime/snapshot/").json()["cursor"]
        secret = Tab.objects.create(venue=self.venue, display_label="PRIVATE TAB")
        self.emit(tab=secret)
        self.emit(venue=self.other)
        dispatch_pending()
        response = client.get(
            "/guest/realtime/stream/",
            {"once": "1", "tab_id": str(secret.id), "venue_id": str(self.other.id)},
            HTTP_LAST_EVENT_ID=baseline,
        )
        result = frames(response)
        assert not any(frame.get("event") == "change" for frame in result)
        snapshot = client.get("/guest/realtime/snapshot/", {"tab_id": str(secret.id)})
        assert snapshot.status_code == 200
        assert str(secret.id) not in json.dumps(snapshot.json())
        assert "PRIVATE TAB" not in json.dumps(snapshot.json())
        confirm_order(
            tab_id=tab.id,
            source=OrderSource.GUEST,
            lines=[{"product_id": self.product.id, "quantity": 1}],
            actor=None,
            idempotency_key="guest-visible",
        )
        dispatch_pending()
        result = frames(
            client.get("/guest/realtime/stream/", {"once": "1"}, HTTP_LAST_EVENT_ID=baseline)
        )
        assert any(frame.get("event") == "change" for frame in result)

    def test_guest_order_history_survives_reload_with_canonical_balance(self):
        client, _, tab = self.guest("3")
        order = confirm_order(
            tab_id=tab.id,
            source=OrderSource.GUEST,
            lines=[{"product_id": self.product.id, "quantity": 2}],
            actor=None,
            idempotency_key="guest-reload",
        )
        response = client.get("/guest/realtime/snapshot/")
        assert response.status_code == 200
        encoded = json.dumps(response.json())
        assert str(order.id) in encoded
        assert "2400" in encoded
        assert "NEW" in encoded

    def test_database_replay_survives_cache_restart_and_dispatch_retry(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.emit()
        cache.clear()
        dispatch_pending()
        dispatch_pending()
        changes = [frame for frame in self.stream(baseline) if frame.get("event") == "change"]
        assert len(changes) == 1
        assert OutboxEvent.objects.filter(venue=self.venue).count() == 1
        assert self.tab.charges.count() == 0

    def test_missing_history_forces_reset_before_more_changes(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.emit()
        first = next(frame for frame in self.stream(baseline) if frame.get("event") == "change")
        self.emit()
        OutboxEvent.objects.filter(venue=self.venue).order_by("sequence").first().delete()
        result = self.stream(first["id"])
        assert any(frame.get("event") == "reset" for frame in result)
        assert not any(frame.get("event") == "change" for frame in result)

    def test_expired_replay_history_requires_canonical_snapshot(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.emit()
        OutboxEvent.objects.filter(venue=self.venue).update(
            occurred_at=timezone.now() - timedelta(days=2)
        )
        result = self.stream(baseline)
        assert any(frame.get("event") == "reset" for frame in result)
        assert not any(frame.get("event") == "change" for frame in result)
        snapshot = self.client.get("/realtime/snapshot/")
        assert snapshot.status_code == 200
        assert snapshot.json()["cursor"] != baseline

    def test_dispatch_retry_keeps_stable_event_identity(self):
        event = self.emit()
        cursor = event.cursor
        assert dispatch_pending() == 1
        event.refresh_from_db()
        published_at = event.published_at
        assert published_at is not None
        assert dispatch_pending() == 0
        event.refresh_from_db()
        assert event.cursor == cursor
        assert event.published_at == published_at

    def test_role_filtering_hides_financial_events(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        self.membership.capability_overrides = {"deny": ["payment.collect"]}
        self.membership.save(update_fields=["capability_overrides"])
        with transaction.atomic():
            emit_event(
                venue_id=self.venue.id,
                event_type="payment.confirmed",
                aggregate_type="Payment",
                aggregate_id=self.tab.id,
                tab_id=self.tab.id,
            )
        result = self.stream(baseline)
        assert not any(frame.get("event") == "change" for frame in result)

    def test_unpublished_commits_wait_for_dispatch_without_advancing_cursor(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        event = self.emit()
        before = frames(self.client.get("/realtime/stream/", {"once": "1", "cursor": baseline}))
        assert not any(frame.get("event") == "change" for frame in before)
        assert before[-1]["data"]["cursor"] == baseline
        changes = [frame for frame in self.stream(baseline) if frame.get("event") == "change"]
        assert [frame["id"] for frame in changes] == [event.cursor]

    def test_cash_changes_are_atomic_and_filtered_from_guest_and_staff(self):
        from modules.access.context import ActorContext
        from modules.access.services import session_for_access_token
        from modules.cash.models import CashPoint
        from modules.cash.services import create_cash_point

        client, _, _ = self.guest("cash-scope")
        baseline = client.get("/guest/realtime/snapshot/").json()["cursor"]
        token = self.client._credentials["HTTP_AUTHORIZATION"].split(" ", 1)[1]
        actor = ActorContext.from_session(session_for_access_token(token))
        with self.assertRaises(RuntimeError), transaction.atomic():
            create_cash_point(label="Rolled back", actor=actor)
            assert OutboxEvent.objects.filter(event_type="cash.point_created").exists()
            raise RuntimeError("command rollback")
        assert not CashPoint.objects.filter(label="Rolled back").exists()
        assert not OutboxEvent.objects.filter(event_type="cash.point_created").exists()
        create_cash_point(label="Authorized drawer", actor=actor)
        assert any(frame.get("event") == "change" for frame in self.stream(baseline))
        dispatch_pending()
        guest_frames = frames(
            client.get("/guest/realtime/stream/", {"once": "1", "cursor": baseline})
        )
        assert not any(frame.get("event") == "change" for frame in guest_frames)
        self.membership.role = StaffRole.STAFF
        self.membership.save(update_fields=["role"])
        assert not any(frame.get("event") == "change" for frame in self.stream(baseline))

    def test_unclassified_public_port_events_are_not_delivered(self):
        baseline = self.client.get("/realtime/snapshot/").json()["cursor"]
        with transaction.atomic():
            emit_event(
                venue_id=self.venue.id,
                event_type="future.private",
                aggregate_type="Future",
                aggregate_id="test",
            )
        assert not any(frame.get("event") == "change" for frame in self.stream(baseline))

    def test_expired_staff_access_rotates_credentials_without_revoking_session(self):
        from unittest.mock import patch

        from modules.access.services import AccessServiceError, session_for_access_token

        token = self.client._credentials["HTTP_AUTHORIZATION"].split(" ", 1)[1]
        session = session_for_access_token(token)
        cursor = self.client.get("/realtime/snapshot/").json()["cursor"]
        with patch(
            "modules.realtime.views.session_for_access_token",
            side_effect=[session, AccessServiceError("ACCESS_TOKEN_EXPIRED", "Expired", 401)],
        ):
            result = frames(self.client.get("/realtime/stream/", {"once": "1", "cursor": cursor}))
        assert [frame["event"] for frame in result] == ["reauthenticate"]
        session.refresh_from_db()
        assert session.revoked_at is None


class ActiveStreamRevocationTests(TransactionTestCase):
    def test_connected_guest_session_is_reauthorized_before_delivery(self):
        venue = Venue.objects.create(name="Active guest", slug="active-stream-guest")
        table = Table.objects.create(
            venue=venue, label="1", guest_ordering_mode=GuestOrderingMode.DIRECT
        )
        resolution = resolve_table_qr(public_token=table.public_token)
        create_or_get_guest_tab(session_token=resolution.token)
        client = APIClient()
        client.credentials(HTTP_X_GUEST_SESSION=resolution.token)
        cursor = client.get("/guest/realtime/snapshot/").json()["cursor"]
        response = client.get("/guest/realtime/stream/", {"cursor": cursor})
        assert response.status_code == 200
        assert response.is_async
        resolution.session.revoked_at = timezone.now()
        resolution.session.save(update_fields=["revoked_at"])

        async def consume():
            iterator = response.streaming_content.__aiter__()
            first = await asyncio.wait_for(iterator.__anext__(), timeout=3)
            await iterator.aclose()
            return first

        assert b"event: revoked" in asyncio.run(consume())
