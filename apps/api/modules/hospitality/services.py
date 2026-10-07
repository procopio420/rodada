from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.hospitality.models import (
    Table,
    TableOccupancy,
    TableStatus,
    TabOccupancyAssignment,
)
from modules.ordering.models import Tab


@dataclass(frozen=True)
class HospitalityServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


def _table_for_actor(table_id, actor: ActorContext) -> Table:
    table = Table.objects.select_for_update().filter(pk=table_id, venue_id=actor.venue_id).first()
    if table is None:
        raise HospitalityServiceError("TABLE_NOT_FOUND", "Mesa não encontrada.", 404)
    return table


@transaction.atomic
def create_table(*, label: str, guest_ordering_mode: str, actor: ActorContext) -> Table:
    table = Table.objects.create(
        venue_id=actor.venue_id,
        label=label.strip(),
        guest_ordering_mode=guest_ordering_mode,
    )
    record_audit_event(
        actor=actor,
        event_type="table.created",
        entity_type="Table",
        entity_id=str(table.id),
        metadata={"label": table.label, "guest_ordering_mode": table.guest_ordering_mode},
    )
    return table


def _active_occupancy(table: Table) -> TableOccupancy:
    occupancy = (
        TableOccupancy.objects.select_for_update()
        .filter(table=table, released_at__isnull=True)
        .first()
    )
    if occupancy is None:
        raise HospitalityServiceError(
            "ACTIVE_OCCUPANCY_NOT_FOUND", "Ocupação ativa não encontrada.", 409
        )
    return occupancy


@transaction.atomic
def occupy_table(*, table_id, actor: ActorContext, tab_id=None) -> TableOccupancy:
    table = _table_for_actor(table_id, actor)
    if table.status != TableStatus.AVAILABLE:
        raise HospitalityServiceError(
            "TABLE_NOT_AVAILABLE", "Mesa não está disponível.", 409, {"status": table.status}
        )
    occupancy = TableOccupancy.objects.create(table=table, generation=table.access_generation)
    table.status = TableStatus.OCCUPIED
    table.save(update_fields=["status", "updated_at"])
    if tab_id is not None:
        _assign_tab(occupancy=occupancy, tab_id=tab_id, actor=actor)
    record_audit_event(
        actor=actor,
        event_type="table.occupied",
        entity_type="TableOccupancy",
        entity_id=str(occupancy.id),
        metadata={"table_id": str(table.id), "generation": occupancy.generation},
    )
    return occupancy


def _assign_tab(
    *, occupancy: TableOccupancy, tab_id, actor: ActorContext
) -> TabOccupancyAssignment:
    # Locking the Tab serializes assignment attempts from two tables.
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if tab is None:
        raise HospitalityServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if occupancy.table.venue_id != actor.venue_id:
        raise HospitalityServiceError("OCCUPANCY_NOT_FOUND", "Ocupação não encontrada.", 404)
    if occupancy.released_at is not None or occupancy.table.status != TableStatus.OCCUPIED:
        raise HospitalityServiceError("OCCUPANCY_NOT_ACTIVE", "Ocupação não aceita comandas.", 409)
    previous = (
        TabOccupancyAssignment.objects.select_for_update()
        .filter(tab=tab, released_at__isnull=True)
        .first()
    )
    if previous is not None:
        if previous.occupancy_id == occupancy.id:
            return previous
        raise HospitalityServiceError(
            "TAB_ALREADY_OCCUPIED",
            "Comanda já está associada a outra ocupação ativa.",
            409,
            {"occupancy_id": str(previous.occupancy_id)},
        )
    assignment = TabOccupancyAssignment.objects.create(
        occupancy=occupancy,
        tab=tab,
        assigned_by_id=actor.staff_id,
    )
    record_audit_event(
        actor=actor,
        event_type="table_occupancy.tab_assigned",
        entity_type="TabOccupancyAssignment",
        entity_id=str(assignment.id),
        metadata={"occupancy_id": str(occupancy.id), "tab_id": str(tab.id)},
    )
    return assignment


@transaction.atomic
def assign_tab(*, occupancy_id, tab_id, actor: ActorContext) -> TabOccupancyAssignment:
    occupancy = (
        TableOccupancy.objects.select_for_update()
        .select_related("table")
        .filter(pk=occupancy_id, table__venue_id=actor.venue_id)
        .first()
    )
    if occupancy is None:
        raise HospitalityServiceError("OCCUPANCY_NOT_FOUND", "Ocupação não encontrada.", 404)
    return _assign_tab(occupancy=occupancy, tab_id=tab_id, actor=actor)


@transaction.atomic
def release_table(*, table_id, actor: ActorContext) -> TableOccupancy:
    table = _table_for_actor(table_id, actor)
    if table.status != TableStatus.OCCUPIED:
        raise HospitalityServiceError(
            "INVALID_TABLE_TRANSITION",
            "Apenas mesa ocupada pode ser liberada.",
            409,
            {"status": table.status},
        )
    occupancy = _active_occupancy(table)
    now = timezone.now()
    occupancy.released_at = now
    occupancy.released_by_id = actor.staff_id
    occupancy.save(update_fields=["released_at", "released_by"])
    TabOccupancyAssignment.objects.filter(occupancy=occupancy, released_at__isnull=True).update(
        released_at=now
    )
    table.status = TableStatus.DIRTY
    table.save(update_fields=["status", "updated_at"])
    record_audit_event(
        actor=actor,
        event_type="table.released",
        entity_type="TableOccupancy",
        entity_id=str(occupancy.id),
        metadata={"table_id": str(table.id)},
    )
    return occupancy


@transaction.atomic
def start_cleaning(*, table_id, actor: ActorContext) -> TableOccupancy:
    table = _table_for_actor(table_id, actor)
    if table.status != TableStatus.DIRTY:
        raise HospitalityServiceError(
            "INVALID_TABLE_TRANSITION",
            "Apenas mesa suja pode iniciar limpeza.",
            409,
            {"status": table.status},
        )
    occupancy = TableOccupancy.objects.select_for_update().filter(table=table).first()
    if occupancy is None or occupancy.released_at is None:
        raise HospitalityServiceError(
            "RELEASED_OCCUPANCY_NOT_FOUND", "Ocupação liberada não encontrada.", 409
        )
    now = timezone.now()
    occupancy.cleaning_started_at = now
    occupancy.cleaning_started_by_id = actor.staff_id
    occupancy.save(update_fields=["cleaning_started_at", "cleaning_started_by"])
    table.status = TableStatus.CLEANING
    table.save(update_fields=["status", "updated_at"])
    record_audit_event(
        actor=actor,
        event_type="table.cleaning_started",
        entity_type="TableOccupancy",
        entity_id=str(occupancy.id),
        metadata={"table_id": str(table.id)},
    )
    return occupancy


@transaction.atomic
def complete_cleaning(*, table_id, actor: ActorContext) -> TableOccupancy:
    table = _table_for_actor(table_id, actor)
    if table.status != TableStatus.CLEANING:
        raise HospitalityServiceError(
            "INVALID_TABLE_TRANSITION",
            "Apenas mesa em limpeza pode ficar disponível.",
            409,
            {"status": table.status},
        )
    occupancy = TableOccupancy.objects.select_for_update().filter(table=table).first()
    if occupancy is None or occupancy.cleaning_started_at is None or occupancy.ready_at is not None:
        raise HospitalityServiceError(
            "CLEANING_OCCUPANCY_NOT_FOUND", "Limpeza ativa não encontrada.", 409
        )
    occupancy.ready_at = timezone.now()
    occupancy.ready_by_id = actor.staff_id
    occupancy.save(update_fields=["ready_at", "ready_by"])
    table.status = TableStatus.AVAILABLE
    table.access_generation += 1
    table.save(update_fields=["status", "access_generation", "updated_at"])
    record_audit_event(
        actor=actor,
        event_type="table.cleaning_completed",
        entity_type="TableOccupancy",
        entity_id=str(occupancy.id),
        metadata={"table_id": str(table.id), "access_generation": table.access_generation},
    )
    return occupancy
