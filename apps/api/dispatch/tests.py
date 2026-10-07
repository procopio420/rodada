from django.test import TestCase
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from catalog.models import Product
from dispatch.models import DispatchEvent, DispatchTask
from dispatch.services import claim_task, complete_task, create_run, emit, ensure_delivery_task
from pos.models import Order, OrderItem, ServicePoint, StaffMember, Tab, Venue, Zone
from pos.services import confirm_order, transition_order_item


class DispatchTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Dispatch bar")
        self.zone = Zone.objects.create(venue=self.venue, name="Rua")
        self.point = ServicePoint.objects.create(venue=self.venue, zone=self.zone, code="P37")
        self.staff = StaffMember.objects.create(venue=self.venue, display_name="Bia")
        self.other = StaffMember.objects.create(venue=self.venue, display_name="Caio")
        product = Product.objects.create(venue=self.venue, name="Beer", current_price_cents=1000)
        tab = Tab.objects.create(venue=self.venue, service_point=self.point, operating_limit_cents=10000, opened_by=self.staff)
        order = Order.objects.create(tab=tab, created_by=self.staff)
        self.item = OrderItem.objects.create(order=order, product=product, quantity=1)
        confirm_order(order.id, self.staff)
        transition_order_item(self.item.id, OrderItem.State.ACCEPTED, self.staff)
        transition_order_item(self.item.id, OrderItem.State.READY, self.staff)

    def test_ready_creates_delivery_exactly_once_and_persists_event(self):
        first = self.item.delivery_task
        second = ensure_delivery_task(self.item.id)
        self.assertEqual(first.id, second.id)
        self.assertEqual(DispatchTask.objects.filter(order_item=self.item).count(), 1)
        self.assertTrue(DispatchEvent.objects.filter(task=first, kind="task.created").exists())

    def test_only_one_staff_member_can_claim_and_owner_completes(self):
        task = self.item.delivery_task
        claim_task(task.id, self.staff)
        with self.assertRaises(Exception): claim_task(task.id, self.other)
        complete_task(task.id, self.staff)
        task.refresh_from_db(); self.item.refresh_from_db()
        self.assertEqual(task.state, DispatchTask.State.DONE)
        self.assertEqual(self.item.state, OrderItem.State.DELIVERED)
        self.assertIsNotNone(self.item.picked_up_at); self.assertIsNotNone(self.item.delivered_at)

    def test_run_keeps_task_item_and_tab_associations(self):
        task = self.item.delivery_task
        run = create_run(self.venue, self.zone, self.staff, [task.id])
        linked = run.tasks.get()
        self.assertEqual(linked.order_item_id, self.item.id)
        self.assertEqual(linked.tab_id, self.item.order.tab_id)

    def test_persisted_event_is_broadcast_after_commit(self):
        task = self.item.delivery_task
        layer = get_channel_layer()
        channel = async_to_sync(layer.new_channel)()
        async_to_sync(layer.group_add)(f"dispatch.venue.{self.venue.id}", channel)

        with self.captureOnCommitCallbacks(execute=True):
            event = emit(task, "task.tested", {"ok": True})

        message = async_to_sync(layer.receive)(channel)
        self.assertEqual(message["type"], "dispatch.event")
        self.assertEqual(message["event"]["id"], event.id)
        self.assertEqual(message["event"]["payload"], {"ok": True})
