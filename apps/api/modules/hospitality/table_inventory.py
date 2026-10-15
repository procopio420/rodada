"""Venue-scoped inventory, preserving table and occupancy history."""

from django.db import transaction

from modules.audit.services import record_audit_event
from modules.hospitality.models import GuestOrderingMode, Table, TableGroupMembership, TableStatus
from modules.hospitality.services import HospitalityServiceError, create_table
from modules.venue.models import Venue


def _set_enabled(table, enabled, actor):
    desired = TableStatus.AVAILABLE if enabled else TableStatus.OUT_OF_SERVICE
    if table.status == desired:
        return
    required = TableStatus.OUT_OF_SERVICE if enabled else TableStatus.AVAILABLE
    if table.status != required or table.occupancies.filter(released_at__isnull=True).exists():
        raise HospitalityServiceError(
            "TABLE_IN_USE", "A mesa precisa estar disponível e sem ocupação para sair de uso.", 409
        )
    if not enabled and TableGroupMembership.objects.filter(
        table=table, removed_at__isnull=True
    ).exists():
        raise HospitalityServiceError(
            "TABLE_GROUP_ACTIVE", "Desfaça o agrupamento antes de retirar a mesa de uso.", 409
        )
    previous = table.status
    table.status = desired
    table.access_generation += 1
    table.save(update_fields=["status", "access_generation", "updated_at"])
    record_audit_event(
        actor=actor,
        event_type="table.inventory_changed",
        entity_type="Table",
        entity_id=str(table.id),
        metadata={"previous_status": previous, "status": desired},
    )


@transaction.atomic
def set_table_enabled(*, table_id, enabled, expected_status, actor):
    Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
    table = Table.objects.select_for_update().filter(pk=table_id, venue_id=actor.venue_id).first()
    if table is None:
        raise HospitalityServiceError("TABLE_NOT_FOUND", "Mesa não encontrada.", 404)
    desired = TableStatus.AVAILABLE if enabled else TableStatus.OUT_OF_SERVICE
    if table.status != desired and table.status != expected_status:
        raise HospitalityServiceError(
            "TABLE_CHANGED", "A mesa mudou. Atualize antes de tentar novamente.", 409
        )
    _set_enabled(table, enabled, actor)
    return table


@transaction.atomic
def set_working_table_count(*, target_count, expected_count, retire_ids, actor):
    Venue.objects.select_for_update(no_key=True).get(pk=actor.venue_id)
    tables = list(Table.objects.select_for_update().filter(venue_id=actor.venue_id).order_by("id"))
    active = [t for t in tables if t.status != TableStatus.OUT_OF_SERVICE]
    if len(active) == target_count:
        return
    if len(active) != expected_count:
        raise HospitalityServiceError(
            "TABLE_COUNT_CHANGED", "A quantidade mudou. Atualize e revise as mesas.", 409
        )
    if target_count < len(active):
        selected = {str(value) for value in retire_ids}
        candidates = [t for t in active if str(t.id) in selected]
        if len(selected) != len(active) - target_count or len(candidates) != len(selected):
            raise HospitalityServiceError(
                "TABLE_SELECTION_REQUIRED",
                "Selecione exatamente as mesas que serão retiradas.",
                409,
            )
        for table in candidates:
            _set_enabled(table, False, actor)
        return
    remaining = target_count - len(active)
    for table in sorted(
        (t for t in tables if t.status == TableStatus.OUT_OF_SERVICE),
        key=lambda t: (t.label, str(t.id)),
    ):
        _set_enabled(table, True, actor)
        remaining -= 1
        if not remaining:
            return
    labels = {t.label for t in tables}
    number = 1
    while remaining:
        label = f"Mesa {number:02d}"
        number += 1
        if label in labels:
            continue
        create_table(label=label, guest_ordering_mode=GuestOrderingMode.DISABLED, actor=actor)
        labels.add(label)
        remaining -= 1
