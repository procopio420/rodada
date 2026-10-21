"""Venue policy over the existing ledger. No balance or relationship snapshot here."""

import logging

from django.db import transaction

from modules.access.capabilities import Capability
from modules.access.errors import AccessPermissionDenied
from modules.access.models import StaffSession
from modules.audit.services import record_audit_event
from modules.ordering.services import OrderingServiceError

from .models import SpendingLimitMode, SpendingLimitPolicyCommand, VenueSpendingLimitPolicy

logger = logging.getLogger(__name__)


def spending_policy(venue_id, *, lock=False):
    rows = VenueSpendingLimitPolicy.objects
    if lock:
        rows = rows.select_for_update()
    value = rows.filter(venue_id=venue_id).first()
    if value is None:
        logger.error("spending_limit_policy_missing", extra={"venue_id": str(venue_id)})
        return {
            "mode": SpendingLimitMode.ENFORCE,
            "version": None,
            "updated_at": None,
            "fallback": True,
        }
    return {
        "mode": value.mode,
        "version": value.version,
        "updated_at": value.updated_at.isoformat(),
        "fallback": False,
    }


def increment_exceeds_limit(position, increment_cents):
    return (
        position["spending_limit_mode"] == SpendingLimitMode.ENFORCE
        and increment_cents > 0
        and position["exposure_cents"] + increment_cents > position["effective_limit_cents"]
    )


def audit_excess(*, tab, position, increment_cents, entity_type, entity_id, actor=None):
    projected = position["exposure_cents"] + increment_cents
    if increment_cents <= 0 or projected <= position["effective_limit_cents"]:
        return
    metadata = {
        "tab_id": str(tab.id),
        "mode": position["spending_limit_mode"],
        "policy_version": position["spending_limit_policy_version"],
        "exposure_before_cents": position["exposure_cents"],
        "exposure_after_cents": projected,
        "effective_limit_cents": position["effective_limit_cents"],
    }
    if actor is not None:
        record_audit_event(
            actor=actor,
            event_type="spending_limit.exceeded",
            entity_type=entity_type,
            entity_id=str(entity_id),
            metadata=metadata,
        )
    else:
        from modules.audit.models import AuditEvent

        AuditEvent.objects.create(
            venue_id=tab.venue_id,
            event_type="spending_limit.exceeded",
            entity_type=entity_type,
            entity_id=str(entity_id),
            metadata=metadata,
        )


@transaction.atomic
def update_spending_policy(*, actor, mode, expected_version, reason, idempotency_key):
    from .services import authorize

    authorize(actor, Capability.VENUE_CONFIGURE, privileged=True)
    session = StaffSession.objects.select_related("membership").get(pk=actor.session_id)
    if session.membership.role not in ("MANAGER", "OWNER"):
        raise AccessPermissionDenied("MANAGER_REQUIRED", "A configuração exige gerência.")
    if (
        mode not in SpendingLimitMode.values
        or type(expected_version) is not int
        or expected_version < 1
        or not isinstance(reason, str)
        or not reason.strip()
        or len(reason) > 240
        or not isinstance(idempotency_key, str)
        or not idempotency_key.strip()
        or len(idempotency_key) > 120
    ):
        raise OrderingServiceError(
            "INVALID_POLICY", "Informe modo, versão, motivo e chave válidos."
        )
    # No Tab locks here: all consumption paths acquire their aggregate before policy.
    value = (
        VenueSpendingLimitPolicy.objects.select_for_update().filter(venue_id=actor.venue_id).first()
    )
    if value is None:
        raise OrderingServiceError("POLICY_MISSING", "Política ausente. Solicite manutenção.", 409)
    body = {"mode": mode, "expected_version": expected_version, "reason": reason.strip()}
    previous = SpendingLimitPolicyCommand.objects.filter(
        venue_id=actor.venue_id, idempotency_key=idempotency_key
    ).first()
    if previous:
        if previous.request != body:
            raise OrderingServiceError(
                "IDEMPOTENCY_CONFLICT", "Chave usada em outra configuração.", 409
            )
        return previous.response
    if value.version != expected_version:
        raise OrderingServiceError(
            "POLICY_VERSION_CONFLICT",
            "A política mudou. Atualize antes de salvar.",
            409,
            spending_policy(actor.venue_id),
        )
    before = spending_policy(actor.venue_id)
    changed = value.mode != mode
    if changed:
        value.mode = mode
        value.version += 1
        value.save(update_fields=["mode", "version", "updated_at"])
        record_audit_event(
            actor=actor,
            event_type="spending_limit_policy.updated",
            entity_type="VenueSpendingLimitPolicy",
            entity_id=str(actor.venue_id),
            reason=body["reason"],
            metadata={
                "before": before,
                "after": spending_policy(actor.venue_id),
                "idempotency_key": idempotency_key,
            },
        )
    response = spending_policy(actor.venue_id)
    SpendingLimitPolicyCommand.objects.create(
        venue_id=actor.venue_id, idempotency_key=idempotency_key, request=body, response=response
    )
    if changed:
        from modules.realtime.services import emit_event

        emit_event(
            venue_id=actor.venue_id,
            event_type="spending_limit_policy.updated",
            aggregate_type="Venue",
            aggregate_id=actor.venue_id,
        )
    return response
