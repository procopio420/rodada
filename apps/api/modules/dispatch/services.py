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



@transaction.atomic
def create_service_request(*, request_id, task_type, actor=None, table_id=None, session_token=None):
    """Persist a structured call; identity makes retries safe after completion."""
    from modules.hospitality.models import Table, TableOccupancy
    from modules.guest_access.services import _locked_authorized_session, _record_guest_audit

    if task_type not in (DispatchTaskType.SERVICE_REQUEST, DispatchTaskType.BILL_REQUEST):
        raise DispatchServiceError("INVALID_REQUEST_TYPE", "Tipo de solicitação inválido.")
    if session_token is not None:
        session = _locked_authorized_session(token=session_token, require_ordering_enabled=False)
        table = session.table
        occupancy = session.occupancy
    else:
        session = None
        table = Table.objects.select_for_update().filter(pk=table_id, venue_id=actor.venue_id).first()
        if table is None:
            raise DispatchServiceError("TABLE_NOT_FOUND", "Mesa não encontrada.", 404)
        occupancy = TableOccupancy.objects.filter(table=table, released_at__isnull=True).first()
    if occupancy is None or occupancy.released_at is not None:
        raise DispatchServiceError("ACTIVE_OCCUPANCY_REQUIRED", "Atendimento ativo obrigatório.", 409)
    # All callers lock the destination table before this lookup/create, so
    # concurrent retries in a visit serialize without a second task.
    existing = DispatchTask.objects.filter(pk=request_id).first()
    if existing:
        if (existing.venue_id != table.venue_id or existing.destination_occupancy_id != occupancy.id
                or existing.task_type != task_type):
            raise DispatchServiceError("REQUEST_ID_CONFLICT", "Solicitação já utilizada.", 409)
        existing._request_replay = True
        return existing
    try:
        with transaction.atomic():
            task = DispatchTask.objects.create(
                id=request_id, venue_id=table.venue_id, task_type=task_type,
                destination_table=table, destination_occupancy=occupancy,
                destination_label=f"Mesa {table.label}",
            )
    except IntegrityError:
        # Different venues may concurrently submit the same externally chosen
        # UUID. A conflict never reveals or returns the other venue's task.
        raise DispatchServiceError("REQUEST_ID_CONFLICT", "Solicitação já utilizada.", 409)
    metadata = {"task_type": task_type, "occupancy_id": str(occupancy.id)}
    if session:
        _record_guest_audit(session=session, event_type="dispatch.service_requested",
                            entity_type="DispatchTask", entity_id=str(task.id), metadata=metadata)
    else:
        record_audit_event(actor=actor, event_type="dispatch.service_requested",
                           entity_type="DispatchTask", entity_id=str(task.id), metadata=metadata)
    task._request_replay = False
    return task


@transaction.atomic
def update_service_request(*, task_id, actor, complete=False):
    task = DispatchTask.objects.select_for_update().filter(
        pk=task_id, venue_id=actor.venue_id,
        task_type__in=(DispatchTaskType.SERVICE_REQUEST, DispatchTaskType.BILL_REQUEST),
    ).first()
    if task is None:
        raise DispatchServiceError("SERVICE_TASK_NOT_FOUND", "Solicitação não encontrada.", 404)
    if task.state == DispatchTaskState.CANCELLED:
        raise DispatchServiceError("SERVICE_TASK_CANCELLED", "Solicitação cancelada.", 409)
    if task.state == DispatchTaskState.DONE:
        return task
    if task.claimed_by_id and task.claimed_by_id != actor.staff_id:
        raise DispatchServiceError("SERVICE_TASK_ALREADY_CLAIMED", "Solicitação tem responsável.", 409)
    if not complete and task.state == DispatchTaskState.CLAIMED:
        return task
    now = timezone.now()
    if complete:
        task.state = DispatchTaskState.DONE
        task.completed_at = now
        task.completed_by_id = actor.staff_id
        task.completion_source = DeliveryCompletionSource.MANUAL
        event = "dispatch.service_completed"
    else:
        task.state = DispatchTaskState.CLAIMED
        task.claimed_by_id = actor.staff_id
        task.claimed_at = now
        event = "dispatch.service_claimed"
    task.save()
    record_audit_event(actor=actor, event_type=event, entity_type="DispatchTask",
                       entity_id=str(task.id), metadata={"task_type": task.task_type})
    return task
