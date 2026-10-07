from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from modules.access.context import ActorContext
from modules.access.models import StaffMember, StaffRole, StaffSession, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.catalog.models import FulfillmentStation, Product
from modules.dispatch.models import DispatchTask, DispatchTaskState
from modules.dispatch.services import (
    DispatchServiceError,
    complete_delivery_task,
    ensure_delivery_task_for_ready_order_item,
)
from modules.hospitality.models import Table, TableOccupancy, TabOccupancyAssignment
from modules.ordering.models import Order, OrderItem, OrderItemState, OrderSource, Tab
from modules.ordering.services import transition_order_item
from modules.venue.models import Venue


class DispatchFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.venue = Venue.objects.create(name="Dispatch Bar", slug="dispatch-bar")
        self.other_venue = Venue.objects.create(name="Outro", slug="dispatch-other")
        self.staff = StaffMember.objects.create(
            display_name="Garçom", login_identifier="dispatch-garcom"
        )
        self.staff.set_pin("1234")
        self.staff.save(update_fields=["pin_hash"])
        self.membership = VenueStaffMembership.objects.create(
            venue=self.venue, staff_member=self.staff, role=StaffRole.STAFF
        )
        login = self.client.post(
            "/auth/login/",
            {
                "venue_slug": self.venue.slug,
                "login_identifier": self.staff.login_identifier,
                "pin": "1234",
                "installation_id": "dispatch-device",
                "platform": "WEB",
            },
            format="json",
        )
        assert login.status_code == 200, login.json()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
        self.actor = ActorContext.from_session(StaffSession.objects.get(venue=self.venue))

    def ready_item(self, *, venue=None, tab=None, name="Cerveja"):
        venue = venue or self.venue
        tab = tab or Tab.objects.create(venue=venue, display_label="Ana")
        product = Product.objects.create(
            venue=venue,
            name=name,
            price_cents=1200,
            fulfillment_station=FulfillmentStation.BAR,
        )
        order = Order.objects.create(tab=tab, source=OrderSource.STAFF)
        return OrderItem.objects.create(
            order=order,
            product=product,
            product_name_snapshot=product.name,
            unit_price_cents=product.price_cents,
            quantity=1,
            state=OrderItemState.READY,
            ready_at=timezone.now(),
        )

    def assign_to_active_table(self, tab):
        table = Table.objects.create(venue=self.venue, label="24")
        occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
        TabOccupancyAssignment.objects.create(
            occupancy=occupancy,
            tab=tab,
            assigned_by=self.staff,
        )
        return table, occupancy

    def test_ready_item_creates_one_delivery_task_with_table_destination_snapshot(self):
        tab = Tab.objects.create(venue=self.venue, display_label="Ana")
        table, occupancy = self.assign_to_active_table(tab)
        item = self.ready_item(tab=tab)

        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)

        assert task.order_item_id == item.id
        assert task.venue_id == self.venue.id
        assert task.state == DispatchTaskState.OPEN
        assert task.destination_table_id == table.id
        assert task.destination_occupancy_id == occupancy.id
        assert task.destination_label == "Mesa 24"
        assert task.ready_at == item.ready_at
        assert AuditEvent.objects.filter(
            event_type="dispatch.delivery_created", entity_id=str(task.id)
        ).exists()

    def test_ready_event_replay_is_idempotent_and_items_have_independent_delivery_work(self):
        tab = Tab.objects.create(venue=self.venue)
        first_item = self.ready_item(tab=tab, name="Cerveja")
        second_item = self.ready_item(tab=tab, name="Porção")

        first = ensure_delivery_task_for_ready_order_item(item_id=first_item.id, actor=self.actor)
        replay = ensure_delivery_task_for_ready_order_item(item_id=first_item.id, actor=self.actor)
        second = ensure_delivery_task_for_ready_order_item(item_id=second_item.id, actor=self.actor)

        assert replay.id == first.id
        assert getattr(replay, "_dispatch_replay") is True
        assert second.id != first.id
        assert DispatchTask.objects.filter(venue=self.venue).count() == 2
        assert AuditEvent.objects.filter(event_type="dispatch.delivery_created").count() == 2

    def test_ready_item_without_occupancy_has_safe_empty_destination(self):
        item = self.ready_item()

        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)

        assert task.destination_table_id is None
        assert task.destination_occupancy_id is None
        assert task.destination_label == ""

    def test_task_cannot_be_created_before_item_is_ready(self):
        item = self.ready_item()
        item.state = OrderItemState.PREPARING
        item.save(update_fields=["state"])

        with self.assertRaises(DispatchServiceError) as captured:
            ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)

        assert captured.exception.code == "ORDER_ITEM_NOT_READY"
        assert DispatchTask.objects.count() == 0

    def test_ordering_ready_transition_creates_delivery_work_through_canonical_hook(self):
        item = self.ready_item()
        item.state = OrderItemState.ACCEPTED
        item.ready_at = None
        item.accepted_at = timezone.now()
        item.save(update_fields=["state", "ready_at", "accepted_at"])

        transitioned = transition_order_item(
            item_id=item.id,
            target_state=OrderItemState.READY,
            actor=self.actor,
        )

        assert transitioned.state == OrderItemState.READY
        task = DispatchTask.objects.get(order_item_id=item.id)
        assert task.state == DispatchTaskState.OPEN
        assert task.ready_at == transitioned.ready_at

    def test_delivery_completion_is_retry_safe_and_transitions_canonical_item(self):
        item = self.ready_item()
        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)

        completed = complete_delivery_task(task_id=task.id, actor=self.actor)
        replay = complete_delivery_task(task_id=task.id, actor=self.actor)
        item.refresh_from_db()

        assert completed.state == DispatchTaskState.DONE
        assert completed.completed_at is not None
        assert completed.completed_by_id == self.staff.id
        assert replay.id == task.id
        assert getattr(replay, "_completion_replay") is True
        assert item.state == OrderItemState.DELIVERED
        assert item.delivered_at is not None
        assert AuditEvent.objects.filter(
            event_type="dispatch.delivery_completed", entity_id=str(task.id)
        ).count() == 1

    def test_delivery_queue_and_completion_http_api_use_persisted_state(self):
        item = self.ready_item()
        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)

        queue = self.client.get("/dispatch/delivery/")
        assert queue.status_code == 200, queue.json()
        assert queue.json()["results"] == [
            {
                "id": str(task.id),
                "state": DispatchTaskState.OPEN,
                "priority": 0,
                "destination_label": "",
                "destination_table_id": None,
                "order_item_id": str(item.id),
                "ready_at": task.ready_at.isoformat().replace("+00:00", "Z"),
                "created_at": task.created_at.isoformat().replace("+00:00", "Z"),
                "completed_at": None,
                "completed_by_id": None,
                "completion_source": "",
                "age_seconds": queue.json()["results"][0]["age_seconds"],
            }
        ]

        first = self.client.post(f"/dispatch/delivery/{task.id}/complete/", {}, format="json")
        replay = self.client.post(f"/dispatch/delivery/{task.id}/complete/", {}, format="json")
        assert first.status_code == 200, first.json()
        assert replay.status_code == 200, replay.json()
        assert first.json()["state"] == DispatchTaskState.DONE
        assert replay.json()["completed_at"] == first.json()["completed_at"]

    def test_other_venue_cannot_complete_delivery(self):
        item = self.ready_item()
        task = ensure_delivery_task_for_ready_order_item(item_id=item.id, actor=self.actor)
        other_staff = StaffMember.objects.create(
            display_name="Outro", login_identifier="dispatch-outro"
        )
        other_membership = VenueStaffMembership.objects.create(
            venue=self.other_venue, staff_member=other_staff, role=StaffRole.STAFF
        )
        other_session = StaffSession.objects.create(
            venue=self.other_venue,
            staff_member=other_staff,
            membership=other_membership,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        with self.assertRaises(DispatchServiceError) as captured:
            complete_delivery_task(task_id=task.id, actor=ActorContext.from_session(other_session))

        assert captured.exception.code == "DELIVERY_TASK_NOT_FOUND"
        task.refresh_from_db()
        assert task.state == DispatchTaskState.OPEN
