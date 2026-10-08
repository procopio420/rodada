import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.access.models import StaffRole, VenueStaffMembership
from modules.audit.services import record_audit_event
from modules.corrections.models import (
    CorrectionKind,
    CorrectionStatus,
    FinancialDisposition,
    OrderCorrection,
)
from modules.ordering.models import Order, OrderItem, OrderItemState, OrderSource, TabState


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
_POST_PRODUCTION_STATES = frozenset(
    (OrderItemState.PREPARING, OrderItemState.READY, OrderItemState.PICKED_UP, OrderItemState.DELIVERED)
)


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


def _manager_approval_required(actor: ActorContext) -> None:
    if not VenueStaffMembership.objects.filter(
        venue_id=actor.venue_id,
        staff_member_id=actor.staff_id,
        role__in=(StaffRole.MANAGER, StaffRole.OWNER),
    ).exists():
        raise CorrectionServiceError(
            "MANAGER_APPROVAL_REQUIRED",
            "Correções após o início da produção exigem gerente.",
            403,
        )


def _cancel_active_delivery(*, item: OrderItem, actor: ActorContext, correction: OrderCorrection) -> None:
    """Resolve active delivery work as an exception without erasing its history."""
    from modules.dispatch.models import DispatchTask, DispatchTaskState

    task = DispatchTask.objects.select_for_update().filter(order_item=item).first()
    if task is None or task.state in (DispatchTaskState.DONE, DispatchTaskState.CANCELLED):
        return
    task.state = DispatchTaskState.CANCELLED
    task.save(update_fields=["state", "updated_at"])
    record_audit_event(
        actor=actor,
        event_type="dispatch.delivery_cancelled_for_correction",
        entity_type="DispatchTask",
        entity_id=str(task.id),
        reason=correction.reason_code,
        metadata={"correction_id": str(correction.id), "order_item_id": str(item.id)},
    )


def _cancel_item_operationally(*, item: OrderItem, actor: ActorContext, correction: OrderCorrection) -> None:
    if item.state != OrderItemState.CANCELLED:
        item.state = OrderItemState.CANCELLED
        item.cancelled_at = timezone.now()
        item.save(update_fields=["state", "cancelled_at"])
    _cancel_active_delivery(item=item, actor=actor, correction=correction)


def _replacement_fingerprint(*, kind: str, reason_code: str, reason_text: str, product_id) -> str:
    payload = {
        "kind": kind,
        "reason_code": reason_code.strip(),
        "reason_text": reason_text.strip(),
        "product_id": str(product_id or ""),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


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
    if item.order.tab.state == TabState.CLOSED:
        raise CorrectionServiceError(
            "TAB_CLOSED",
            "Reabra a comanda antes de registrar uma correção.",
            409,
        )

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


@transaction.atomic
def create_post_production_correction(
    *,
    item_id,
    kind: str,
    reason_code: str,
    reason_text: str,
    idempotency_key: str,
    actor: ActorContext,
    replacement_product_id=None,
) -> OrderCorrection:
    """Apply a manager-authorized remake or replacement without rewriting history.

    A remake retains the original customer responsibility and adds a matching
    courtesy adjustment for its new charge.  A replacement reverses the
    original responsibility and adds the replacement's normal charge, making
    equal/cheaper/more-expensive outcomes deterministic from the ledger.
    """
    if kind not in (CorrectionKind.REMAKE, CorrectionKind.REPLACEMENT):
        raise CorrectionServiceError("INVALID_CORRECTION_KIND", "Tipo de correção inválido.")
    reason_code, reason_text, idempotency_key = (
        reason_code.strip(),
        reason_text.strip(),
        idempotency_key.strip(),
    )
    if not reason_code or not idempotency_key:
        raise CorrectionServiceError(
            "INVALID_CORRECTION_REQUEST", "Motivo e chave de idempotência são obrigatórios."
        )
    item = (
        OrderItem.objects.select_for_update()
        .select_related("order__tab", "product")
        .filter(pk=item_id, order__tab__venue_id=actor.venue_id)
        .first()
    )
    if item is None:
        raise CorrectionServiceError("ORDER_ITEM_NOT_FOUND", "Item não encontrado.", 404)
    if item.order.tab.state == TabState.CLOSED:
        raise CorrectionServiceError("TAB_CLOSED", "Reabra a comanda antes de registrar uma correção.", 409)
    fingerprint = _replacement_fingerprint(
        kind=kind,
        reason_code=reason_code,
        reason_text=reason_text,
        product_id=replacement_product_id,
    )
    existing = OrderCorrection.objects.filter(
        original_order_item=item, idempotency_key=idempotency_key
    ).first()
    if existing is not None:
        if existing.request_fingerprint != fingerprint:
            raise CorrectionServiceError("IDEMPOTENCY_CONFLICT", "A chave já foi usada para outra correção.", 409)
        existing._idempotency_replay = True
        return existing
    if item.state not in _POST_PRODUCTION_STATES:
        raise CorrectionServiceError(
            "CORRECTION_STAGE_REQUIRES_PRODUCTION", "Remake ou substituição exige item em produção ou concluído.", 409,
            {"state": item.state},
        )
    _manager_approval_required(actor)
    active = OrderCorrection.objects.filter(
        original_order_item=item,
        status__in=(CorrectionStatus.REQUESTED, CorrectionStatus.APPLIED),
    ).first()
    if active is not None:
        raise CorrectionServiceError(
            "ITEM_ALREADY_CORRECTED", "Este item já possui uma correção em andamento ou aplicada.", 409,
            {"correction_id": str(active.id)},
        )

    from modules.catalog.models import Product
    from modules.ledger.services import courtesy_replacement, create_charges_for_order, reverse_open_responsibility, totals

    if kind == CorrectionKind.REMAKE:
        product = item.product
        unit_price_cents = item.unit_price_cents
        quantity = item.quantity
    else:
        if not replacement_product_id:
            raise CorrectionServiceError("REPLACEMENT_PRODUCT_REQUIRED", "Escolha o item de substituição.")
        product = Product.objects.select_for_update().filter(
            pk=replacement_product_id, venue_id=actor.venue_id, active=True
        ).first()
        if product is None:
            raise CorrectionServiceError("REPLACEMENT_PRODUCT_NOT_AVAILABLE", "Item de substituição indisponível.", 409)
        unit_price_cents = product.price_cents
        quantity = item.quantity

    correction = OrderCorrection.objects.create(
        venue_id=item.order.tab.venue_id,
        original_order_item=item,
        kind=kind,
        stage_at_request=item.state,
        reason_code=reason_code,
        reason_text=reason_text,
        financial_disposition=(
            FinancialDisposition.COURTESY_REPLACEMENT
            if kind == CorrectionKind.REMAKE
            else FinancialDisposition.REVERSE_OPEN_RESPONSIBILITY
        ),
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        requested_by_id=actor.staff_id,
        approved_by_id=actor.staff_id,
    )
    replacement_order = Order.objects.create(
        tab=item.order.tab,
        source=OrderSource.STAFF,
        confirmed_by_id=actor.staff_id,
        idempotency_key=f"correction:{correction.id}",
        request_fingerprint=fingerprint,
    )
    replacement = OrderItem.objects.create(
        order=replacement_order,
        product=product,
        product_name_snapshot=product.name if kind == CorrectionKind.REPLACEMENT else item.product_name_snapshot,
        unit_price_cents=unit_price_cents,
        quantity=quantity,
    )
    create_charges_for_order(replacement_order, actor)
    item.order.tab.version += 1
    item.order.tab.save(update_fields=["version"])
    correction.replacement_order_item = replacement

    if kind == CorrectionKind.REMAKE:
        correction.financial_adjustment = courtesy_replacement(correction, replacement, actor)
        correction.status = CorrectionStatus.APPLIED
    else:
        correction.financial_adjustment = reverse_open_responsibility(correction, item, actor)
        resulting_exposure = totals(item.order.tab)["exposure_cents"]
        if resulting_exposure < 0:
            correction.financial_disposition = FinancialDisposition.REFUND_REQUIRED
            correction.refund_required_cents = -resulting_exposure
        else:
            correction.status = CorrectionStatus.APPLIED

    _cancel_item_operationally(item=item, actor=actor, correction=correction)
    if correction.status == CorrectionStatus.APPLIED:
        correction.applied_at = timezone.now()
    correction.save(
        update_fields=[
            "replacement_order_item", "financial_adjustment", "financial_disposition",
            "refund_required_cents", "status", "applied_at",
        ]
    )
    correction._idempotency_replay = False
    event_type = "order_item.remake_created" if kind == CorrectionKind.REMAKE else "order_item.replacement_created"
    record_audit_event(
        actor=actor,
        event_type=event_type,
        entity_type="OrderCorrection",
        entity_id=str(correction.id),
        reason=reason_code,
        metadata={
            "order_item_id": str(item.id),
            "replacement_order_item_id": str(replacement.id),
            "stage_at_request": correction.stage_at_request,
            "financial_disposition": correction.financial_disposition,
            "refund_required_cents": correction.refund_required_cents,
            **totals(item.order.tab),
        },
    )
    return correction


@transaction.atomic
def settle_refund_required_cancellation(
    *,
    correction_id,
    payment_id,
    amount_cents: int,
    refund_idempotency_key: str,
    cash_point_id,
    actor: ActorContext,
):
    """Settle a paid cancellation through an explicit refund plus reversal.

    A confirmed payment is never rewritten. The result is three independent,
    inspectable facts: the original Charge, a negative LedgerAdjustment and a
    Refund against the manager-selected confirmed Payment.
    """
    correction = (
        OrderCorrection.objects.select_for_update()
        # `refund` and `financial_adjustment` are nullable.  PostgreSQL cannot
        # lock the nullable side of the outer joins select_related would add,
        # so lock the correction/original path only and lazy-load optional
        # append-only links when needed below.
        .select_related("original_order_item__order__tab")
        .filter(pk=correction_id, venue_id=actor.venue_id)
        .first()
    )
    if correction is None:
        raise CorrectionServiceError("CORRECTION_NOT_FOUND", "Correção não encontrada.", 404)

    item = correction.original_order_item
    if correction.status == CorrectionStatus.APPLIED:
        if (
            correction.refund_id
            and str(correction.refund.payment_id) == str(payment_id)
            and correction.refund.idempotency_key == refund_idempotency_key
        ):
            correction._idempotency_replay = True
            from modules.ledger.services import totals

            return correction, correction.refund, totals(item.order.tab)
        raise CorrectionServiceError(
            "CORRECTION_ALREADY_SETTLED",
            "Esta correção já foi concluída.",
            409,
        )
    if (
        correction.status != CorrectionStatus.REQUESTED
        or correction.financial_disposition != FinancialDisposition.REFUND_REQUIRED
    ):
        raise CorrectionServiceError(
            "CORRECTION_NOT_REFUND_REQUIRED",
            "Esta correção não aguarda estorno.",
            409,
        )
    if item.state not in (*_CANCELLABLE_STATES, OrderItemState.CANCELLED):
        raise CorrectionServiceError(
            "CORRECTION_STAGE_REQUIRES_APPROVAL",
            "O item mudou de estágio e exige tratamento operacional específico.",
            409,
            {"state": item.state},
        )
    if item.order.tab.state == TabState.CLOSED:
        raise CorrectionServiceError("TAB_CLOSED", "Comanda fechada não aceita estorno de correção.", 409)
    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool) or amount_cents <= 0:
        raise CorrectionServiceError("INVALID_REFUND", "Valor de estorno inválido.")
    if correction.refund_required_cents and amount_cents != correction.refund_required_cents:
        raise CorrectionServiceError(
            "REFUND_AMOUNT_MISMATCH",
            "O estorno precisa cobrir exatamente o saldo de correção pendente.",
            409,
            {"refund_required_cents": correction.refund_required_cents},
        )

    from modules.ledger.models import Charge, Payment
    from modules.ledger.services import LedgerServiceError, create_refund, reverse_open_responsibility, totals

    charge = Charge.objects.select_for_update().filter(order_item=item, tab=item.order.tab).first()
    if charge is None:
        raise CorrectionServiceError("CHARGE_NOT_FOUND", "Item sem cobrança canônica.", 409)
    if amount_cents > charge.amount_cents:
        raise CorrectionServiceError(
            "REFUND_EXCEEDS_ITEM_VALUE",
            "Estorno excede o valor original do item.",
            409,
        )
    if not Payment.objects.filter(pk=payment_id, tab=item.order.tab).exists():
        raise CorrectionServiceError("PAYMENT_NOT_FOUND", "Pagamento não pertence à comanda.", 404)

    try:
        refund, _ = create_refund(
            payment_id=payment_id,
            amount_cents=amount_cents,
            idempotency_key=refund_idempotency_key,
            reason=f"correction:{correction.reason_code}",
            actor=actor,
            cash_point_id=cash_point_id,
        )
        adjustment = reverse_open_responsibility(correction, item, actor)
    except LedgerServiceError as error:
        raise CorrectionServiceError(error.code, error.message, error.status_code) from error

    now = timezone.now()
    _cancel_item_operationally(item=item, actor=actor, correction=correction)
    correction.refund = refund
    correction.financial_adjustment = adjustment
    correction.status = CorrectionStatus.APPLIED
    correction.approved_by_id = actor.staff_id
    correction.applied_at = now
    correction.save(
        update_fields=[
            "refund",
            "financial_adjustment",
            "status",
            "approved_by",
            "applied_at",
        ]
    )
    correction._idempotency_replay = False
    result = totals(item.order.tab)
    record_audit_event(
        actor=actor,
        event_type="order_item.cancelled_after_refund",
        entity_type="OrderCorrection",
        entity_id=str(correction.id),
        reason=correction.reason_code,
        metadata={
            "order_item_id": str(item.id),
            "refund_id": str(refund.id),
            "financial_adjustment_id": str(adjustment.id),
            "refund_amount_cents": amount_cents,
            **result,
        },
    )
    return correction, refund, result
