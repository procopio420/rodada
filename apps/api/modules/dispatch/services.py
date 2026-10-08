from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.dispatch.models import (
    DeliveryCompletionSource,
    DispatchTask,
    DispatchTaskState,
    DispatchTaskType,
)
from modules.hospitality.models import TabOccupancyAssignment
from modules.ordering.models import OrderItem, OrderItemState


@dataclass(frozen=True)
class DispatchServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


def _active_destination_for_tab(*, tab_id):
    """Resolve physical context without treating a Table as the account owner."""
    assignment = (
        TabOccupancyAssignment.objects.select_related("occupancy__table")
        .filter(
            tab_id=tab_id,
            released_at__isnull=True,
            occupancy__released_at__isnull=True,
        )
        .first()
    )
    if assignment is None:
        from modules.ordering.models import Tab
        tab = Tab.objects.select_related("service_point").get(pk=tab_id)
        return None, None, tab.service_point.label if tab.service_point_id else ""

    table = assignment.occupancy.table
    return table, assignment.occupancy, f"Mesa {table.label}"


@transaction.atomic
def ensure_delivery_task_for_ready_order_item(*, item_id, actor: ActorContext | None = None) -> DispatchTask:
    """Create delivery work exactly once after an OrderItem becomes READY.

    Call this immediately after persisting a successful READY transition. It is
    intentionally safe to call again after a command retry, event replay, or a
    timeout after commit. The task is tied to the individual item, which keeps
    BAR and KITCHEN readiness independent within the same Order.
    """
    item = (
        OrderItem.objects.select_for_update()
        .select_related("order__tab")
        .filter(pk=item_id)
        .first()
    )
    if item is None:
        raise DispatchServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)
    if actor is not None and actor.venue_id != item.order.tab.venue_id:
        raise DispatchServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)

    existing = DispatchTask.objects.filter(
        order_item_id=item.id,
        task_type=DispatchTaskType.DELIVERY,
    ).first()
    if existing is not None:
        existing._dispatch_replay = True
        return existing

    if item.state != OrderItemState.READY:
        raise DispatchServiceError(
            "ORDER_ITEM_NOT_READY",
            "A entrega só pode ser criada para item pronto.",
            409,
            {"state": item.state},
        )

    table, occupancy, destination_label = _active_destination_for_tab(tab_id=item.order.tab_id)
    try:
        # Keep the uniqueness-race recovery inside a savepoint. Catching an
        # IntegrityError directly in this outer transaction would leave it
        # unusable for the subsequent read on PostgreSQL.
        with transaction.atomic():
            task = DispatchTask.objects.create(
                venue_id=item.order.tab.venue_id,
                task_type=DispatchTaskType.DELIVERY,
                order_item=item,
                destination_table=table,
                destination_occupancy=occupancy,
                destination_label=destination_label,
                ready_at=item.ready_at or timezone.now(),
            )
    except IntegrityError:
        # The one-to-one relation is the final idempotency barrier if a ready
        # event is delivered concurrently by separate workers.
        task = DispatchTask.objects.get(
            order_item_id=item.id,
            task_type=DispatchTaskType.DELIVERY,
        )
        task._dispatch_replay = True
        return task

    task._dispatch_replay = False
    if actor is not None:
        record_audit_event(
            actor=actor,
            event_type="dispatch.delivery_created",
            entity_type="DispatchTask",
            entity_id=str(task.id),
            metadata={
                "order_item_id": str(item.id),
                "tab_id": str(item.order.tab_id),
                "destination_label": task.destination_label,
            },
        )
    return task


@transaction.atomic
def complete_delivery_task(*, task_id, actor: ActorContext) -> DispatchTask:
    """Complete delivery and its canonical OrderItem transition in one transaction."""
    task_reference = (
        DispatchTask.objects.filter(
            pk=task_id,
            venue_id=actor.venue_id,
            task_type=DispatchTaskType.DELIVERY,
        )
        .values("id", "order_item_id")
        .first()
    )
    if task_reference is None:
        raise DispatchServiceError("DELIVERY_TASK_NOT_FOUND", "Entrega não encontrada.", 404)

    # Lock order item before task; this matches READY -> task creation and
    # avoids an inverse lock order between the two command paths.
    item = (
        OrderItem.objects.select_for_update()
        .select_related("order__tab")
        .filter(pk=task_reference["order_item_id"], order__tab__venue_id=actor.venue_id)
        .first()
    )
    task = DispatchTask.objects.select_for_update().get(pk=task_reference["id"])
    if task.state == DispatchTaskState.DONE:
        task._completion_replay = True
        return task
    if task.state == DispatchTaskState.CANCELLED:
        raise DispatchServiceError("DELIVERY_TASK_CANCELLED", "Entrega cancelada.", 409)
    if item is None:
        raise DispatchServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)
    if item.state not in (
        OrderItemState.READY,
        OrderItemState.PICKED_UP,
        OrderItemState.DELIVERED,
    ):
        raise DispatchServiceError(
            "ORDER_ITEM_NOT_DELIVERABLE",
            "Item não está pronto para entrega.",
            409,
            {"state": item.state},
        )

    now = timezone.now()
    if item.state != OrderItemState.DELIVERED:
        item.state = OrderItemState.DELIVERED
        item.delivered_at = now
        item.save(update_fields=["state", "delivered_at"])
        record_audit_event(
            actor=actor,
            event_type="order_item.transitioned",
            entity_type="OrderItem",
            entity_id=str(item.id),
            metadata={"state": OrderItemState.DELIVERED, "via": "dispatch"},
        )

    task.state = DispatchTaskState.DONE
    task.completed_at = now
    task.completed_by_id = actor.staff_id
    task.completion_source = DeliveryCompletionSource.MANUAL
    task.save(
        update_fields=[
            "state",
            "completed_at",
            "completed_by",
            "completion_source",
            "updated_at",
        ]
    )
    task._completion_replay = False
    record_audit_event(
        actor=actor,
        event_type="dispatch.delivery_completed",
        entity_type="DispatchTask",
        entity_id=str(task.id),
        metadata={"order_item_id": str(item.id), "tab_id": str(item.order.tab_id)},
    )
    return task


def refresh_tab_destination(tab, actor):
    from modules.dispatch.models import DispatchTask
    from modules.hospitality.models import TabOccupancyAssignment
    assignment = TabOccupancyAssignment.objects.filter(tab=tab, released_at__isnull=True).select_related("occupancy__table").first()
    table = assignment.occupancy.table if assignment else None
    occupancy = assignment.occupancy if assignment else None
    label = table.label if table else (tab.service_point.label if tab.service_point_id else tab.display_label)
    for task in DispatchTask.objects.select_for_update(of=("self",)).filter(order_item__order__tab=tab, state__in=("OPEN", "CLAIMED")):
        before = {"table_id": str(task.destination_table_id) if task.destination_table_id else None, "label": task.destination_label}
        task.destination_table, task.destination_occupancy, task.destination_label = table, occupancy, label
        task.save(update_fields=["destination_table", "destination_occupancy", "destination_label", "updated_at"])
        record_audit_event(actor=actor, event_type="dispatch.destination_changed", entity_type="DispatchTask", entity_id=str(task.id), metadata={"tab_id": str(tab.id), "before": before, "label": label})

