from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from dispatch.models import DeliveryRun, DispatchEvent, DispatchTask
from pos.models import OrderItem


def publish_venue_event(venue_id, kind, payload=None):
    """Best-effort realtime signal; HTTP snapshots remain the source of truth."""
    message = {"kind": kind, "payload": payload or {}}
    transaction.on_commit(lambda: async_to_sync(get_channel_layer().group_send)(
        f"dispatch.venue.{venue_id}", {"type": "dispatch.event", "event": message}
    ))


def emit(task, kind, payload=None):
    event = DispatchEvent.objects.create(venue=task.venue, task=task, kind=kind, payload=payload or {})
    message = {
        "id": event.id,
        "task_id": task.id,
        "kind": kind,
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
    }
    transaction.on_commit(lambda: async_to_sync(get_channel_layer().group_send)(
        f"dispatch.venue.{task.venue_id}", {"type": "dispatch.event", "event": message}
    ))
    return event


@transaction.atomic
def ensure_delivery_task(item_id):
    item = OrderItem.objects.select_for_update().select_related("order__tab__venue", "order__tab__service_point__zone").get(pk=item_id)
    if item.state != OrderItem.State.READY:
        raise ValidationError("Only ready items produce delivery tasks.")
    point = item.order.tab.service_point
    task, created = DispatchTask.objects.get_or_create(order_item=item, defaults={"venue": item.order.tab.venue, "tab": item.order.tab,
        "service_point": point, "zone": point.zone if point else None, "type": DispatchTask.Type.DELIVERY})
    if created:
        emit(task, "task.created", {"state": task.state})
    return task


@transaction.atomic
def claim_task(task_id, actor):
    task = DispatchTask.objects.select_for_update().get(pk=task_id)
    if actor.venue_id != task.venue_id:
        raise PermissionDenied("Staff member does not belong to this venue.")
    if task.state != DispatchTask.State.OPEN:
        raise ValidationError("Task is no longer available.")
    task.state, task.claimed_by, task.claimed_at = DispatchTask.State.CLAIMED, actor, timezone.now()
    task.save(update_fields=["state", "claimed_by", "claimed_at"]); emit(task, "task.claimed", {"staff_id": actor.id})
    return task


@transaction.atomic
def complete_task(task_id, actor):
    task = DispatchTask.objects.select_for_update().select_related("order_item").get(pk=task_id)
    if actor.venue_id != task.venue_id:
        raise PermissionDenied("Staff member does not belong to this venue.")
    if task.state != DispatchTask.State.CLAIMED or task.claimed_by_id != actor.id:
        raise ValidationError("Only the staff member who claimed this task can complete it.")
    now = timezone.now()
    if task.order_item_id and task.order_item.state in {OrderItem.State.READY, OrderItem.State.PICKED_UP}:
        task.order_item.state, task.order_item.delivered_at = OrderItem.State.DELIVERED, now
        if task.order_item.picked_up_at is None: task.order_item.picked_up_at = now
        task.order_item.save(update_fields=["state", "picked_up_at", "delivered_at"])
    task.state, task.done_at = DispatchTask.State.DONE, now
    task.save(update_fields=["state", "done_at"]); emit(task, "task.done", {"staff_id": actor.id})
    return task


@transaction.atomic
def create_run(venue, zone, actor, task_ids):
    tasks = list(DispatchTask.objects.select_for_update().filter(id__in=task_ids, venue=venue, zone=zone, type=DispatchTask.Type.DELIVERY).exclude(state__in=[DispatchTask.State.DONE, DispatchTask.State.CANCELLED]))
    if len(tasks) != len(set(task_ids)): raise ValidationError("All tasks must be active deliveries in the selected zone.")
    run = DeliveryRun.objects.create(venue=venue, zone=zone, created_by=actor); run.tasks.add(*tasks)
    return run
