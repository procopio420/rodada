import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.corrections.models import (
    CorrectionKind,
    CorrectionStatus,
    FinancialDisposition,
    OrderCorrection,
)
from modules.ordering.models import OrderItem, OrderItemState


@dataclass(frozen=True)
class CorrectionServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


# This boundary deliberately lives outside the correction domain. The ledger
# implementation must use it to append a real adjustment/reversal against the
# current financial owner before correction can become APPLIED.
OpenResponsibilityReversal = Callable[[OrderCorrection, OrderItem, ActorContext], None]


_CANCEL_KINDS = frozenset(
    (CorrectionKind.CANCEL_ITEM, CorrectionKind.CUSTOMER_CHANGED_MIND, CorrectionKind.WRONG_ITEM_ENTERED)
)
_CANCELLABLE_STATES = frozenset((OrderItemState.NEW, OrderItemState.ACCEPTED))


def _fingerprint(*, kind: str, reason_code: str, reason_text: str) -> str:
    payload = {
        "kind": kind,
        "reason_code": reason_code.strip(),
        "reason_text": reason_text.strip(),
        "financial_disposition": FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _has_confirmed_money(*, tab_id) -> bool:
    # There is not yet canonical allocation from payments to individual items.
    # Any confirmed money therefore takes this correction out of the simple
    # cancellation path and into the Refund/manager workflow.
    from modules.ledger.models import Payment, PaymentStatus

    return Payment.objects.filter(
        tab_id=tab_id,
        status__in=PaymentStatus.confirmed_money_values(),
    ).exists()


@transaction.atomic
def cancel_before_fulfillment(
    *,
    item_id,
    kind: str,
    reason_code: str,
    reason_text: str,
    idempotency_key: str,
    actor: ActorContext,
    financial_reversal_hook: OpenResponsibilityReversal | None,
    record_paid_request: bool = False,
) -> OrderCorrection:
    """Cancel a NEW/ACCEPTED item without erasing its snapshot or charge.

    `financial_reversal_hook` is mandatory because every confirmed item has a
    charge. It must append the ledger's true open-responsibility reversal in
    this same transaction, or raise. A correction never writes a fake payment,
    mutates the charge, or guesses how to allocate confirmed payments.
    """
    if kind not in _CANCEL_KINDS:
        raise CorrectionServiceError("INVALID_CORRECTION_KIND", "Tipo de correção inválido.")
    reason_code = reason_code.strip()
    reason_text = reason_text.strip()
    idempotency_key = idempotency_key.strip()
    if not reason_code or not idempotency_key:
        raise CorrectionServiceError(
            "INVALID_CORRECTION_REQUEST",
            "Motivo e chave de idempotência são obrigatórios.",
        )

    item = (
        OrderItem.objects.select_for_update()
        .select_related("order__tab")
        .filter(pk=item_id, order__tab__venue_id=actor.venue_id)
        .first()
    )
    if item is None:
        raise CorrectionServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)

    fingerprint = _fingerprint(kind=kind, reason_code=reason_code, reason_text=reason_text)
    existing = OrderCorrection.objects.filter(
        original_order_item=item,
        idempotency_key=idempotency_key,
    ).first()
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise CorrectionServiceError(
                "IDEMPOTENCY_CONFLICT",
                "A chave já foi usada para outra correção.",
                409,
            )
        existing._idempotency_replay = True
        return existing

    if item.state not in _CANCELLABLE_STATES:
        existing_terminal = (
            OrderCorrection.objects.filter(
                original_order_item=item,
                status=CorrectionStatus.APPLIED,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        if existing_terminal is not None:
            raise CorrectionServiceError(
                "ITEM_ALREADY_CORRECTED",
                "Este item já possui uma correção aplicada.",
                409,
                {"correction_id": str(existing_terminal.id), "state": item.state},
            )
        raise CorrectionServiceError(
            "CORRECTION_STAGE_REQUIRES_APPROVAL",
            "Este estágio exige fluxo de correção autorizado.",
            409,
            {"state": item.state},
        )

    if _has_confirmed_money(tab_id=item.order.tab_id):
        if record_paid_request:
            correction = OrderCorrection.objects.create(
                venue_id=item.order.tab.venue_id,
                original_order_item=item,
                kind=kind,
                stage_at_request=item.state,
                reason_code=reason_code,
                reason_text=reason_text,
                financial_disposition=FinancialDisposition.REFUND_REQUIRED,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                requested_by_id=actor.staff_id,
            )
            correction._idempotency_replay = False
            record_audit_event(
                actor=actor,
                event_type="order_item.refund_required",
                entity_type="OrderCorrection",
                entity_id=str(correction.id),
                reason=reason_code,
                metadata={
                    "order_item_id": str(item.id),
                    "tab_id": str(item.order.tab_id),
                    "financial_disposition": correction.financial_disposition,
                },
            )
            return correction
        raise CorrectionServiceError(
            "PAID_CORRECTION_REQUIRES_REFUND",
            "Item com dinheiro confirmado exige fluxo de estorno/cortesia.",
            409,
        )
    if financial_reversal_hook is None:
        raise CorrectionServiceError(
            "FINANCIAL_REVERSAL_INTEGRATION_REQUIRED",
            "O cancelamento exige reversão financeira canônica.",
            409,
        )

    try:
        with transaction.atomic():
            correction = OrderCorrection.objects.create(
                venue_id=item.order.tab.venue_id,
                original_order_item=item,
                kind=kind,
                stage_at_request=item.state,
                reason_code=reason_code,
                reason_text=reason_text,
                financial_disposition=FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                requested_by_id=actor.staff_id,
            )
    except IntegrityError:
        correction = OrderCorrection.objects.get(
            original_order_item=item,
            idempotency_key=idempotency_key,
        )
        if correction.request_fingerprint != fingerprint:
            raise CorrectionServiceError(
                "IDEMPOTENCY_CONFLICT",
                "A chave já foi usada para outra correção.",
                409,
            )
        correction._idempotency_replay = True
        return correction

    # This handler is intentionally invoked before operational mutation. Its
    # exception aborts the correction and preserves the item as actionable.
    adjustment = financial_reversal_hook(correction, item, actor)
    if adjustment is not None:
        correction.financial_adjustment = adjustment
        correction.save(update_fields=["financial_adjustment"])

    now = timezone.now()
    item.state = OrderItemState.CANCELLED
    item.cancelled_at = now
    item.save(update_fields=["state", "cancelled_at"])
    correction.status = CorrectionStatus.APPLIED
    correction.approved_by_id = actor.staff_id
    correction.applied_at = now
    correction.save(update_fields=["status", "approved_by", "applied_at"])
    correction._idempotency_replay = False
    record_audit_event(
        actor=actor,
        event_type="order_item.cancelled",
        entity_type="OrderCorrection",
        entity_id=str(correction.id),
        reason=reason_code,
        metadata={
            "order_item_id": str(item.id),
            "tab_id": str(item.order.tab_id),
            "kind": kind,
            "stage_at_request": correction.stage_at_request,
            "financial_disposition": correction.financial_disposition,
        },
    )
    return correction
