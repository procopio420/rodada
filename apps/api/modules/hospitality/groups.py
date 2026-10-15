"""Transactional Spec 004 TABLE-011 grouping of physical tables only.

Locks are acquired in deterministic Table UUID order, then group/member rows.
There is no TableOccupancy, Tab, GuestSession, Order, payment or ledger write.
"""
import hashlib
import json

from django.db import transaction
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.hospitality.models import (
    Table, TableGroup, TableGroupMembership, TableStatus,
)
from modules.hospitality.services import HospitalityServiceError


def _fingerprint(*, label, ids):
    return hashlib.sha256(json.dumps(
        {"label": label, "table_ids": ids}, sort_keys=True,
        separators=(",", ":"),
    ).encode()).hexdigest()


def group_payload(group):
    members = list(
        group.memberships.select_related("table")
        .order_by("table__label", "table_id")
    )
    return {
        "id": str(group.pk),
        "label": group.label,
        "created_at": group.created_at,
        "dissolved_at": group.dissolved_at,
        "active": group.dissolved_at is None,
        "tables": [
            {"id": str(m.table_id), "label": m.table.label,
             "active": m.removed_at is None}
            for m in members
        ],
    }


@transaction.atomic
def create_table_group(*, actor, table_ids, label, request_key):
    ids = sorted(str(table_id) for table_id in table_ids)
    if len(ids) != len(set(ids)) or not 2 <= len(ids) <= 20:
        raise HospitalityServiceError(
            "INVALID_GROUP_MEMBERS", "Selecione entre duas e vinte mesas distintas.", 400
        )
    label = label.strip()
    digest = _fingerprint(label=label, ids=ids)
    key = {"venue_id": actor.venue_id, "created_by_id": actor.staff_id,
           "request_key": request_key}
    existing = TableGroup.objects.filter(**key).first()
    if existing:
        if existing.fingerprint != digest:
            raise HospitalityServiceError(
                "IDEMPOTENCY_CONFLICT", "Esta intenção já tem outro conteúdo.", 409
            )
        return existing, True

    tables = list(
        Table.objects.select_for_update().filter(
            venue_id=actor.venue_id, id__in=ids
        ).order_by("id")
    )
    if len(tables) != len(ids):
        raise HospitalityServiceError("TABLE_NOT_FOUND", "Mesa não encontrada.", 404)

    group, created = TableGroup.objects.get_or_create(
        **key, defaults={"label": label, "fingerprint": digest},
    )
    group = TableGroup.objects.select_for_update().get(pk=group.pk)
    if not created:
        if group.fingerprint != digest:
            raise HospitalityServiceError(
                "IDEMPOTENCY_CONFLICT", "Esta intenção já tem outro conteúdo.", 409
            )
        return group, True

    if any(table.status == TableStatus.OUT_OF_SERVICE for table in tables):
        raise HospitalityServiceError(
            "TABLE_OUT_OF_SERVICE", "Mesa fora de uso não pode ser agrupada.", 409
        )
    if TableGroupMembership.objects.filter(
        table_id__in=ids, removed_at__isnull=True
    ).exists():
        raise HospitalityServiceError(
            "TABLE_ALREADY_GROUPED", "Uma das mesas já pertence a outro grupo ativo.", 409
        )

    TableGroupMembership.objects.bulk_create([
        TableGroupMembership(group=group, table=table) for table in tables
    ])
    record_audit_event(
        actor=actor, event_type="table_group.created", entity_type="TableGroup",
        entity_id=str(group.id),
        metadata={"label": label, "table_ids": ids,
                  "request_key": str(request_key)},
    )
    return group, False


@transaction.atomic
def dissolve_table_group(*, actor, group_id):
    group = TableGroup.objects.filter(pk=group_id, venue_id=actor.venue_id).first()
    if group is None:
        raise HospitalityServiceError("TABLE_GROUP_NOT_FOUND", "Grupo não encontrado.", 404)

    ids = list(
        TableGroupMembership.objects.filter(group=group, removed_at__isnull=True)
        .order_by("table_id").values_list("table_id", flat=True)
    )
    list(Table.objects.select_for_update().filter(pk__in=ids).order_by("id"))
    group = TableGroup.objects.select_for_update().get(pk=group_id)
    if group.dissolved_at is not None:
        return group, True

    now = timezone.now()
    TableGroupMembership.objects.filter(
        group=group, removed_at__isnull=True
    ).update(removed_at=now)
    group.dissolved_at = now
    group.dissolved_by_id = actor.staff_id
    group.save(update_fields=["dissolved_at", "dissolved_by"])
    record_audit_event(
        actor=actor, event_type="table_group.dissolved", entity_type="TableGroup",
        entity_id=str(group.id),
        metadata={"table_ids": [str(table_id) for table_id in ids]},
    )
    return group, False
