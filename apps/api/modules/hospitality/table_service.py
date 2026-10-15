"""Spec 027 commands. Lock order: intent -> Table -> Occupancy -> Tab.

Intent locks serialize only the same actor/action/key, including different targets.
All effects and the immutable replay result commit in one transaction.
"""

import hashlib
import json

from django.db import transaction
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.hospitality.models import ServiceCommand, TableOccupancy, TableStatus
from modules.hospitality.services import (
    HospitalityServiceError,
    _assign_tab,
    _table_for_actor,
    occupy_table,
)
from modules.ordering.services import open_tab


def _intent(actor, action, key, payload):
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    row, _ = ServiceCommand.objects.get_or_create(
        venue_id=actor.venue_id,
        actor_id=actor.staff_id,
        action=action,
        key=key,
        defaults={"fingerprint": fingerprint},
    )
    row = ServiceCommand.objects.select_for_update().get(pk=row.pk)
    if row.fingerprint != fingerprint:
        raise HospitalityServiceError(
            "IDEMPOTENCY_CONFLICT", "Esta intenção já tem outro destino ou conteúdo.", 409
        )
    return row


def _require_rollout(actor):
    from modules.venue.models import Venue
    if not Venue.objects.filter(pk=actor.venue_id, table_service_enabled=True).exists():
        raise HospitalityServiceError("TABLE_SERVICE_DISABLED", "Atendimento contextual desativado neste estabelecimento.", 409)


def _finish(row, result):
    row.result = result
    row.save(update_fields=["result"])
    return {**result, "replayed": False}


def _snapshot(occupancy):
    return {
        "id": str(occupancy.id),
        "generation": occupancy.generation,
        "responsible_staff_id": str(occupancy.responsible_staff_id)
        if occupancy.responsible_staff_id
        else None,
        "responsibility_version": occupancy.responsibility_version,
    }


def _locked_occupancy(occupancy_id, actor):
    table_id = (
        TableOccupancy.objects.filter(pk=occupancy_id, table__venue_id=actor.venue_id)
        .values_list("table_id", flat=True)
        .first()
    )
    if table_id is None:
        raise HospitalityServiceError("OCCUPANCY_NOT_FOUND", "Ocupação não encontrada.", 404)
    table = _table_for_actor(table_id, actor)
    occupancy = TableOccupancy.objects.select_for_update().get(pk=occupancy_id)
    occupancy.table = table
    if occupancy.released_at or table.status != TableStatus.OCCUPIED:
        raise HospitalityServiceError(
            "OCCUPANCY_RELEASED", "Esta ocupação foi encerrada. Atualize a mesa.", 409
        )
    return occupancy


@transaction.atomic
def start_table_service(*, table_id, idempotency_key, actor):
    row = _intent(actor, "start", idempotency_key, {"table_id": str(table_id)})
    if row.result:
        return {**row.result, "replayed": True}
    table = _table_for_actor(table_id, actor)
    _require_rollout(actor)
    if table.status == TableStatus.OCCUPIED:
        occupancy = TableOccupancy.objects.get(table=table, released_at__isnull=True)
        raise HospitalityServiceError(
            "OCCUPANCY_ALREADY_ACTIVE",
            "Mesa já em uso. Você pode atender sem assumir.",
            409,
            {"active_occupancy": _snapshot(occupancy), "occupancy_id": str(occupancy.id)},
        )
    occupancy = occupy_table(table_id=table_id, actor=actor)
    occupancy.responsible_staff_id = actor.staff_id
    occupancy.responsible_since = timezone.now()
    occupancy.responsibility_version = 1
    occupancy.save(
        update_fields=["responsible_staff", "responsible_since", "responsibility_version"]
    )
    _audit(occupancy, actor, "assigned", None, idempotency_key)
    return _finish(
        row,
        {
            "table_id": str(table_id),
            "table_status": "OCCUPIED",
            "active_occupancy": {**_snapshot(occupancy), "tab_count": 0},
        },
    )


@transaction.atomic
def start_table_service_and_open_tab(*, table_id, display_label, idempotency_key, actor):
    """Start a new visit and its first named Tab as one recoverable command."""
    row = _intent(
        actor,
        "start_open",
        idempotency_key,
        {"table_id": str(table_id), "display_label": display_label},
    )
    if row.result:
        return {**row.result, "replayed": True}
    table = _table_for_actor(table_id, actor)
    _require_rollout(actor)
    if table.status == TableStatus.OCCUPIED:
        occupancy = TableOccupancy.objects.get(table=table, released_at__isnull=True)
        raise HospitalityServiceError(
            "OCCUPANCY_ALREADY_ACTIVE",
            "Mesa já em uso. Escolha uma mesa disponível.",
            409,
            {"active_occupancy": _snapshot(occupancy), "occupancy_id": str(occupancy.id)},
        )
    if table.status != TableStatus.AVAILABLE:
        raise HospitalityServiceError(
            "TABLE_NOT_AVAILABLE",
            "Mesa não está disponível.",
            409,
            {"status": table.status},
        )
    occupancy = occupy_table(table_id=table_id, actor=actor)
    occupancy.responsible_staff_id = actor.staff_id
    occupancy.responsible_since = timezone.now()
    occupancy.responsibility_version = 1
    occupancy.save(
        update_fields=["responsible_staff", "responsible_since", "responsibility_version"]
    )
    _audit(occupancy, actor, "assigned", None, idempotency_key)
    tab = open_tab(actor=actor, display_label=display_label)
    _assign_tab(occupancy=occupancy, tab_id=tab.id, actor=actor)
    return _finish(
        row,
        {
            "tab_id": str(tab.id),
            "occupancy_id": str(occupancy.id),
            "table_id": str(table.id),
            "table_label": table.label,
            "display_label": tab.display_label,
            "state": tab.state,
        },
    )


def _audit(occupancy, actor, kind, previous, key):
    record_audit_event(
        actor=actor,
        event_type="occupancy.responsibility_" + kind,
        entity_type="TableOccupancy",
        entity_id=str(occupancy.id),
        metadata={
            "table_id": str(occupancy.table_id),
            "generation": occupancy.generation,
            "previous_staff_id": str(previous) if previous else None,
            "responsible_staff_id": str(actor.staff_id),
            "responsibility_version": occupancy.responsibility_version,
            "idempotency_key": key,
            "source": "STAFF",
        },
    )


@transaction.atomic
def open_tab_in_occupancy(
    *, occupancy_id, expected_generation, idempotency_key, actor, display_label="", customer_id=None
):
    row = _intent(
        actor,
        "open",
        idempotency_key,
        {
            "occupancy_id": str(occupancy_id),
            "expected_generation": expected_generation,
            "display_label": display_label,
            "customer_id": customer_id,
        },
    )
    if row.result:
        return {**row.result, "replayed": True}
    if not display_label.strip():
        raise HospitalityServiceError("DISPLAY_LABEL_REQUIRED", "Nome ou apelido é obrigatório.", 400)
    occupancy = _locked_occupancy(occupancy_id, actor)
    _require_rollout(actor)
    if (
        expected_generation != occupancy.generation
        or expected_generation != occupancy.table.access_generation
    ):
        raise HospitalityServiceError(
            "STALE_TABLE_GENERATION",
            "Esta mesa iniciou outra visita. Atualize antes de abrir a comanda.",
            409,
        )
    if customer_id:
        from modules.house_account.models import Relationship

        if not Relationship.objects.filter(
            customer_id=customer_id, venue_id=actor.venue_id
        ).exists():
            raise HospitalityServiceError(
                "CUSTOMER_NOT_FOUND_OR_OTHER_VENUE",
                "Cliente não encontrado neste estabelecimento.",
                404,
            )
    tab = open_tab(actor=actor, display_label=display_label, customer_id=customer_id)
    _assign_tab(occupancy=occupancy, tab_id=tab.id, actor=actor)
    return _finish(
        row,
        {
            "tab_id": str(tab.id),
            "occupancy_id": str(occupancy.id),
            "table_id": str(occupancy.table_id),
            "table_label": occupancy.table.label,
            "display_label": tab.display_label,
            "state": tab.state,
        },
    )


@transaction.atomic
def claim_occupancy_responsibility(
    *, occupancy_id, expected_responsibility_version, mode, idempotency_key, actor
):
    row = _intent(
        actor,
        "claim",
        idempotency_key,
        {
            "occupancy_id": str(occupancy_id),
            "expected_responsibility_version": expected_responsibility_version,
            "mode": mode,
        },
    )
    if row.result:
        return {**row.result, "replayed": True}
    occupancy = _locked_occupancy(occupancy_id, actor)
    _require_rollout(actor)
    if occupancy.responsible_staff_id == actor.staff_id:
        return _finish(row, {"active_occupancy": _snapshot(occupancy), "unchanged": True})
    if occupancy.responsibility_version != expected_responsibility_version or (
        occupancy.responsible_staff_id and mode != "TAKE_OVER"
    ):
        raise HospitalityServiceError(
            "RESPONSIBILITY_CONFLICT",
            "O atendimento mudou. Atualize antes de assumir.",
            409,
            {"active_occupancy": _snapshot(occupancy)},
        )
    previous = occupancy.responsible_staff_id
    occupancy.responsible_staff_id = actor.staff_id
    occupancy.responsible_since = timezone.now()
    occupancy.responsibility_version += 1
    occupancy.save(
        update_fields=["responsible_staff", "responsible_since", "responsibility_version"]
    )
    _audit(occupancy, actor, "transferred" if previous else "assigned", previous, idempotency_key)
    return _finish(row, {"active_occupancy": _snapshot(occupancy), "unchanged": False})
