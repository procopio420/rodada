from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from modules.access.capabilities import Capability
from modules.access.errors import AccessPermissionDenied
from modules.access.models import StaffSession
from modules.access.services import (
    AccessServiceError,
    authorize_replayed_command,
    recent_reauthentication_valid,
)
from modules.audit.services import record_audit_event
from modules.ledger.services import totals
from modules.ordering.models import Tab, TabState
from modules.ordering.services import OrderingServiceError

from .models import DEMO_LIMITS, LimitOverride, Relationship, VenueRelationshipPolicy


def authorize(actor, capability, *, privileged=False):
    try:
        canonical = authorize_replayed_command(
            session_id=actor.session_id, required_capability=capability
        )
    except AccessServiceError as error:
        raise AccessPermissionDenied(error.code, error.message) from error
    if canonical != actor:
        raise AccessPermissionDenied("ACTOR_MISMATCH", "Operador inválido.")
    if privileged and not recent_reauthentication_valid(
        StaffSession.objects.get(pk=actor.session_id)
    ):
        raise AccessPermissionDenied("REAUTH_REQUIRED", "Confirme seu PIN novamente.")


def policy(venue_id, kind):
    VenueRelationshipPolicy.objects.bulk_create(
        [
            VenueRelationshipPolicy(venue_id=venue_id, kind=name, limit_cents=limit)
            for name, limit in DEMO_LIMITS.items()
        ],
        ignore_conflicts=True,
    )
    return VenueRelationshipPolicy.objects.get(venue_id=venue_id, kind=kind)


def snapshot(venue_id, customer_id=None):
    kind = "VISITOR"
    if customer_id:
        relationship = Relationship.objects.filter(
            venue_id=venue_id, customer_id=customer_id
        ).first()
        if not relationship:
            raise OrderingServiceError(
                "CUSTOMER_NOT_FOUND", "Cliente não encontrado neste estabelecimento.", 404
            )
        kind = relationship.kind
    value = policy(venue_id, kind)
    return {
        "customer_id": customer_id,
        "relationship_snapshot": kind,
        "policy_version_snapshot": value.version,
        "operating_limit_cents": value.limit_cents,
    }


def financial_position(tab):
    ledger = totals(tab)
    latest = tab.limit_overrides.order_by("-created_at", "-id").first()
    active = latest if latest and latest.expires_at > timezone.now() else None
    limit = (
        max(tab.operating_limit_cents, active.limit_cents) if active else tab.operating_limit_cents
    )
    exposure = ledger["exposure_cents"]
    reasons = [r for r in tab.action_reasons if r != "SPENDING_LIMIT"]
    # Legacy/manual attention states must not be silently cleared by a payment.
    if tab.state == TabState.REQUIRES_ACTION and not tab.action_reasons:
        reasons.append("OTHER_ACTION_REQUIRED")
    from modules.corrections.models import OrderCorrection

    if OrderCorrection.objects.filter(
        original_order_item__order__tab=tab,
        status="REQUESTED",
        financial_disposition="REFUND_REQUIRED",
    ).exists():
        if "REFUND_REQUIRED" not in reasons:
            reasons.append("REFUND_REQUIRED")
    else:
        reasons = [r for r in reasons if r != "REFUND_REQUIRED"]
    if exposure >= limit:
        reasons.append("SPENDING_LIMIT")
    state = tab.state
    if state in (TabState.OPEN, TabState.REQUIRES_ACTION):
        state = TabState.REQUIRES_ACTION if reasons else TabState.OPEN
    from modules.audit.models import AuditEvent

    request = (
        AuditEvent.objects.filter(
            venue_id=tab.venue_id,
            entity_type="Tab",
            entity_id=str(tab.id),
            event_type="tab.limit_approval_requested",
        )
        .order_by("-occurred_at")
        .first()
    )
    approved = latest and request and latest.created_at >= request.occurred_at
    return {
        **ledger,
        "state": state,
        "action_reasons": reasons,
        "customer_id": str(tab.customer_id) if tab.customer_id else None,
        "relationship_snapshot": tab.relationship_snapshot,
        "policy_version_snapshot": tab.policy_version_snapshot,
        "operating_limit_cents": tab.operating_limit_cents,
        "effective_limit_cents": limit,
        "remaining_capacity_cents": max(0, limit - exposure),
        "percentage_used": max(0, exposure) * 100 // limit if limit else None,
        "limit_warning": limit > 0 and max(0, exposure) * 100 >= limit * 80,
        "consumption_blocked": exposure >= limit,
        "override_expires_at": active.expires_at if active else None,
        "approval_requested": bool(
            request and not approved and state in (TabState.OPEN, TabState.REQUIRES_ACTION)
        ),
    }


def sync_attention(tab, actor=None):
    """Caller holds the Tab lock; financial effects serialize on this aggregate."""
    position = financial_position(tab)
    if tab.state != position["state"] or tab.action_reasons != position["action_reasons"]:
        before = {"state": tab.state, "action_reasons": tab.action_reasons}
        tab.state = position["state"]
        tab.action_reasons = position["action_reasons"]
        tab.save(update_fields=["state", "action_reasons"])
        metadata = {
            "before": before,
            "state": tab.state,
            "action_reasons": tab.action_reasons,
            "exposure_cents": position["exposure_cents"],
            "effective_limit_cents": position["effective_limit_cents"],
            "source": "LEDGER_DERIVED",
        }
        if actor:
            record_audit_event(
                actor=actor,
                event_type="tab.attention_changed",
                entity_type="Tab",
                entity_id=str(tab.id),
                metadata=metadata,
            )
        else:
            from modules.audit.models import AuditEvent

            AuditEvent.objects.create(
                venue_id=tab.venue_id,
                event_type="tab.attention_changed",
                entity_type="Tab",
                entity_id=str(tab.id),
                metadata=metadata,
            )
    return position


def locked_tab(tab_id, actor):
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if not tab:
        raise OrderingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state not in (TabState.OPEN, TabState.REQUIRES_ACTION):
        raise OrderingServiceError("TAB_NOT_OPEN", "Comanda não está aberta.", 409)
    return tab


@transaction.atomic
def approve_override(*, tab_id, limit_cents, expires_at, reason, idempotency_key, actor):
    authorize(actor, Capability.LIMIT_OVERRIDE, privileged=True)
    tab = locked_tab(tab_id, actor)
    existing = tab.limit_overrides.filter(idempotency_key=idempotency_key).first()
    if existing:
        if (existing.limit_cents, existing.expires_at, existing.reason) != (
            limit_cents,
            expires_at,
            reason,
        ):
            raise OrderingServiceError(
                "IDEMPOTENCY_CONFLICT", "Chave usada em outra aprovação.", 409
            )
        return tab
    now = timezone.now()
    before = financial_position(tab)["effective_limit_cents"]
    if (
        not isinstance(limit_cents, int)
        or isinstance(limit_cents, bool)
        or not before < limit_cents <= 2147483647
    ):
        raise OrderingServiceError("INVALID_LIMIT", "Informe um limite total maior que o atual.")
    if (
        not reason.strip()
        or len(reason) > 240
        or not idempotency_key
        or len(idempotency_key) > 120
        or not now < expires_at <= now + timedelta(hours=24)
    ):
        raise OrderingServiceError(
            "INVALID_OVERRIDE", "Motivo e validade de até 24 horas são obrigatórios."
        )
    value = LimitOverride.objects.create(
        tab=tab,
        previous_limit_cents=before,
        limit_cents=limit_cents,
        expires_at=expires_at,
        reason=reason.strip(),
        actor_id=actor.staff_id,
        idempotency_key=idempotency_key,
    )
    tab.version += 1
    tab.save(update_fields=["version"])
    sync_attention(tab, actor)
    record_audit_event(
        actor=actor,
        event_type="tab.limit_overridden",
        entity_type="Tab",
        entity_id=str(tab.id),
        reason=value.reason,
        metadata={
            "override_id": str(value.id),
            "previous_limit_cents": before,
            "limit_cents": limit_cents,
            "expires_at": expires_at.isoformat(),
            "approval_type": "OPERATIONAL",
        },
    )
    return tab


@transaction.atomic
def associate_customer(*, tab_id, customer_id, actor):
    authorize(actor, Capability.TAB_OPEN)
    tab = locked_tab(tab_id, actor)
    if not Relationship.objects.filter(venue_id=actor.venue_id, customer_id=customer_id).exists():
        raise OrderingServiceError("CUSTOMER_NOT_FOUND", "Cliente não encontrado.", 404)
    before = str(tab.customer_id) if tab.customer_id else None
    tab.customer_id = customer_id
    tab.version += 1
    tab.save(update_fields=["customer", "version"])
    record_audit_event(
        actor=actor,
        event_type="tab.customer_associated",
        entity_type="Tab",
        entity_id=str(tab.id),
        metadata={"previous_customer_id": before, "customer_id": str(customer_id)},
    )
    return tab


@transaction.atomic
def reassess_tab(*, tab_id, reason, actor):
    authorize(actor, Capability.LIMIT_OVERRIDE, privileged=True)
    if not reason.strip():
        raise OrderingServiceError("REASON_REQUIRED", "Informe o motivo.")
    tab = locked_tab(tab_id, actor)
    before = {
        "kind": tab.relationship_snapshot,
        "limit_cents": tab.operating_limit_cents,
        "version": tab.policy_version_snapshot,
    }
    for key, value in snapshot(tab.venue_id, tab.customer_id).items():
        setattr(tab, key, value)
    tab.version += 1
    tab.save(
        update_fields=[
            "relationship_snapshot",
            "policy_version_snapshot",
            "operating_limit_cents",
            "version",
        ]
    )
    sync_attention(tab, actor)
    record_audit_event(
        actor=actor,
        event_type="tab.policy_reassessed",
        entity_type="Tab",
        entity_id=str(tab.id),
        reason=reason,
        metadata={
            "before": before,
            "after": {
                "kind": tab.relationship_snapshot,
                "limit_cents": tab.operating_limit_cents,
                "version": tab.policy_version_snapshot,
            },
        },
    )
    return tab
