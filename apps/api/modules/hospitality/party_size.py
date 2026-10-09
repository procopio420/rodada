"""Canonical covers commands: target locks serialize explicit observations."""

from django.db import transaction
from django.utils import timezone

from modules.access.capabilities import Capability, has_capability
from modules.access.models import StaffRole, VenueStaffMembership
from modules.audit.models import AuditEvent
from modules.hospitality.models import (
    PartySizeObservation,
    Table,
    TableOccupancy,
    TabOccupancyAssignment,
)
from modules.hospitality.services import HospitalityServiceError
from modules.ordering.models import Tab
from modules.realtime.services import emit_event


def observation_payload(row):
    if row is None:
        return {"covers_count": None, "version": 0, "source": None, "observation_id": None}
    return {
        "covers_count": row.covers_count,
        "version": row.version,
        "source": row.source,
        "observation_id": str(row.id),
        "supersedes_id": str(row.supersedes_id) if row.supersedes_id else None,
        "staff_member_id": str(row.staff_member_id) if row.staff_member_id else None,
        "guest_session_id": str(row.guest_session_id) if row.guest_session_id else None,
        "reason": row.reason,
        "observed_at": row.observed_at,
        "recorded_at": row.recorded_at,
    }


def current_party_size(*, occupancy_id=None, tab_id=None):
    if (occupancy_id is None) == (tab_id is None):
        raise ValueError("Exactly one party-size target is required")
    if tab_id is not None:
        assignment = TabOccupancyAssignment.objects.filter(
            tab_id=tab_id, released_at__isnull=True
        ).first()
        if assignment:
            occupancy_id, tab_id = assignment.occupancy_id, None
    return PartySizeObservation.objects.filter(occupancy_id=occupancy_id, tab_id=tab_id).first()


@transaction.atomic
def record_party_size(
    *,
    covers_count,
    expected_version,
    idempotency_key,
    actor=None,
    session_token=None,
    occupancy_id=None,
    tab_id=None,
    reason="",
):
    guest = None
    if actor is None:
        from modules.guest_access.services import _locked_authorized_session

        guest = _locked_authorized_session(token=session_token, require_tab=True)
        # Public guest command takes no target ID: context is server-resolved.
        if occupancy_id is not None and occupancy_id != guest.occupancy_id or tab_id is not None:
            raise HospitalityServiceError("GUEST_NOT_AUTHORIZED", "Ocupação não autorizada.", 403)
        occupancy_id = guest.occupancy_id
        venue_id = guest.table.venue_id
    else:
        venue_id = actor.venue_id
        membership = (
            VenueStaffMembership.objects.select_related("staff_member")
            .filter(venue_id=venue_id, staff_member_id=actor.staff_id)
            .first()
        )
        if membership is None or not has_capability(membership, Capability.TABLE_MANAGE):
            raise HospitalityServiceError(
                "GUEST_NOT_AUTHORIZED", "Sem permissão para registrar pessoas.", 403
            )
    if type(covers_count) is not int or covers_count <= 0 or covers_count > 2147483647:
        raise HospitalityServiceError(
            "INVALID_COVER_COUNT", "Informe quantidade positiva de pessoas."
        )
    if type(expected_version) is not int or expected_version < 0:
        raise HospitalityServiceError("STALE_PARTY_SIZE", "Versão inválida.", 409)
    if (
        not isinstance(idempotency_key, str)
        or not idempotency_key.strip()
        or len(idempotency_key) > 128
    ):
        raise HospitalityServiceError(
            "INVALID_IDEMPOTENCY_KEY", "Identificador de solicitação obrigatório."
        )
    if (occupancy_id is None) == (tab_id is None):
        raise HospitalityServiceError("INVALID_TARGET", "Selecione uma ocupação ou comanda.")
    if occupancy_id is not None:
        # Same table -> occupancy order as release, so correction/release cannot race.
        reference = (
            TableOccupancy.objects.filter(pk=occupancy_id, table__venue_id=venue_id)
            .values("table_id")
            .first()
        )
        if reference is None:
            raise HospitalityServiceError("OCCUPANCY_NOT_FOUND", "Ocupação não encontrada.", 404)
        Table.objects.select_for_update().get(pk=reference["table_id"])
        target = TableOccupancy.objects.select_for_update().get(pk=occupancy_id)
        if target.released_at:
            if guest:
                raise HospitalityServiceError("TARGET_RELEASED", "Ocupação encerrada.", 409)
            if membership.role not in (StaffRole.MANAGER, StaffRole.OWNER):
                raise HospitalityServiceError(
                    "MANAGER_REQUIRED", "Correção histórica exige gerente.", 403
                )
            if not reason.strip():
                raise HospitalityServiceError(
                    "REASON_REQUIRED", "Informe motivo da correção histórica."
                )
    else:
        target = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=venue_id).first()
        if target is None:
            raise HospitalityServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
        if target.occupancy_assignments.exists():
            raise HospitalityServiceError(
                "OCCUPANCY_TARGET_REQUIRED", "Registre pessoas na ocupação desta comanda.", 409
            )
    current = current_party_size(occupancy_id=occupancy_id, tab_id=tab_id)
    replay = PartySizeObservation.objects.filter(
        venue_id=venue_id, idempotency_key=idempotency_key
    ).first()
    if replay:
        if (
            replay.occupancy_id != occupancy_id
            or replay.tab_id != tab_id
            or replay.covers_count != covers_count
            or replay.reason != reason.strip()
            or replay.staff_member_id != (actor.staff_id if actor else None)
            or replay.guest_session_id != (guest.id if guest else None)
        ):
            raise HospitalityServiceError(
                "IDEMPOTENCY_CONFLICT", "Solicitação já usada com outros dados.", 409
            )
        return replay
    if expected_version != (current.version if current else 0):
        raise HospitalityServiceError(
            "STALE_PARTY_SIZE",
            "Quantidade atualizada; confira o valor atual.",
            409,
            {"current": observation_payload(current)},
        )
    row = PartySizeObservation.objects.create(
        venue_id=venue_id,
        occupancy_id=occupancy_id,
        tab_id=tab_id,
        covers_count=covers_count,
        version=expected_version + 1,
        source="GUEST" if guest else "STAFF",
        supersedes=current,
        staff_member_id=actor.staff_id if actor else None,
        guest_session=guest,
        reason=reason.strip(),
        idempotency_key=idempotency_key,
        observed_at=timezone.now(),
    )
    event_type = "party_size.corrected" if current else "party_size.recorded"
    AuditEvent.objects.create(
        venue_id=venue_id,
        actor_staff_id=actor.staff_id if actor else None,
        actor_session_id=actor.session_id if actor else None,
        device_id=actor.device_id if actor else None,
        event_type=event_type,
        entity_type="PartySizeObservation",
        entity_id=str(row.id),
        metadata={
            "previous_count": current.covers_count if current else None,
            "covers_count": row.covers_count,
            "source": row.source,
            "reason": row.reason,
            "occupancy_id": str(occupancy_id) if occupancy_id else None,
            "tab_id": str(tab_id) if tab_id else None,
            "guest_session_id": str(guest.id) if guest else None,
        },
    )
    emit_event(
        venue_id=venue_id,
        event_type=event_type,
        aggregate_type="TableOccupancy" if occupancy_id else "Tab",
        aggregate_id=occupancy_id or tab_id,
        tab_id=tab_id,
        payload={"version": row.version},
    )
    return row


def occupancy_cover_metrics(*, occupancies, eligible_revenue_cents):
    """Ratio-of-sums inputs require a caller's canonical, unambiguous attribution.

    Missing revenue attribution is excluded, never guessed from a Tab's present
    location. Covers count once per physical visit, independently of Tab count.
    The numerator/denominator remain integers so callers choose display precision.
    """
    known_visits = unknown_visits = excluded_visits = known_covers = numerator = 0
    seen = set()
    for occupancy in occupancies:
        if occupancy.id in seen:
            continue
        seen.add(occupancy.id)
        row = current_party_size(occupancy_id=occupancy.id)
        if row is None:
            unknown_visits += 1
            continue
        known_visits += 1
        if occupancy.id not in eligible_revenue_cents:
            excluded_visits += 1
            continue
        cents = eligible_revenue_cents[occupancy.id]
        if type(cents) is not int:
            raise ValueError("Eligible revenue must be canonical integer cents")
        known_covers += row.covers_count
        numerator += cents
    total = known_visits + unknown_visits
    return {
        "known_visits": known_visits,
        "unknown_visits": unknown_visits,
        "excluded_visits": excluded_visits,
        "coverage_basis_points": known_visits * 10000 // total if total else None,
        "eligible_revenue_cents": numerator,
        "eligible_known_covers": known_covers,
        "revenue_per_cover": {"numerator_cents": numerator, "denominator_covers": known_covers}
        if known_covers
        else None,
    }
