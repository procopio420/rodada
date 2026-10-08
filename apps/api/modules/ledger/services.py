from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.ledger.models import (
    AdjustmentKind,
    Charge,
    LedgerAdjustment,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from modules.ordering.models import OrderItem, Tab, TabState


class LedgerServiceError(Exception):
    def __init__(self, code, message, status_code=400):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


def exposure_cents(tab: Tab) -> int:
    return totals(tab)["exposure_cents"]


def totals(tab: Tab) -> dict:
    charges = tab.charges.aggregate(total=Sum("amount_cents"))["total"] or 0
    adjustments = tab.ledger_adjustments.aggregate(total=Sum("amount_cents"))["total"] or 0
    payments = tab.payments.filter(status__in=PaymentStatus.confirmed_money_values()).aggregate(
        total=Sum("amount_cents")
    )["total"] or 0
    refunds = Refund.objects.filter(
        payment__tab=tab,
        status=RefundStatus.CONFIRMED,
    ).aggregate(total=Sum("amount_cents"))["total"] or 0
    return {
        "charges_cents": charges,
        "adjustments_cents": adjustments,
        "payments_cents": payments,
        "refunds_cents": refunds,
        "exposure_cents": charges + adjustments - payments + refunds,
    }


@transaction.atomic
def create_charges_for_order(order, actor):
    for item in OrderItem.objects.select_for_update().filter(order=order):
        Charge.objects.get_or_create(tab=order.tab, order_item=item, defaults={"amount_cents": item.line_total_cents})
    if actor is not None:
        record_audit_event(actor=actor, event_type="order.charged", entity_type="Order", entity_id=str(order.id), metadata={"tab_id": str(order.tab_id)})


def reverse_open_responsibility(correction, item: OrderItem, actor) -> LedgerAdjustment:
    """Append the financial counterpart of an unpaid item cancellation.

    Payments are intentionally not touched here. Callers must first establish
    that the Tab has no confirmed money that would need a separate refund.
    """
    charge = (
        Charge.objects.select_for_update()
        .filter(order_item=item, tab=item.order.tab)
        .first()
    )
    if charge is None:
        raise LedgerServiceError(
            "CHARGE_NOT_FOUND",
            "O item confirmado não possui cobrança para reverter.",
            409,
        )

    key = f"correction:{correction.id}"
    adjustment, created = LedgerAdjustment.objects.get_or_create(
        tab=charge.tab,
        idempotency_key=key,
        defaults={
            "order_item": item,
            "kind": AdjustmentKind.ORDER_ITEM_CANCELLATION,
            "amount_cents": -charge.amount_cents,
            "reason_code": correction.reason_code,
            "created_by_id": actor.staff_id,
        },
    )
    expected = (
        adjustment.order_item_id == item.id
        and adjustment.kind == AdjustmentKind.ORDER_ITEM_CANCELLATION
        and adjustment.amount_cents == -charge.amount_cents
    )
    if not expected:
        raise LedgerServiceError(
            "ADJUSTMENT_IDEMPOTENCY_CONFLICT",
            "A reversão financeira existente não corresponde à correção.",
            409,
        )
    if created:
        record_audit_event(
            actor=actor,
            event_type="charge.reversed",
            entity_type="LedgerAdjustment",
            entity_id=str(adjustment.id),
            reason=correction.reason_code,
            metadata={
                "correction_id": str(correction.id),
                "charge_id": str(charge.id),
                "order_item_id": str(item.id),
                "amount_cents": adjustment.amount_cents,
            },
        )
    return adjustment


def courtesy_replacement(correction, item: OrderItem, actor) -> LedgerAdjustment:
    """Comp the newly produced remake without inventing a zero-price item."""
    charge = (
        Charge.objects.select_for_update()
        .filter(order_item=item, tab=item.order.tab)
        .first()
    )
    if charge is None:
        raise LedgerServiceError(
            "CHARGE_NOT_FOUND",
            "O item de reposição não possui cobrança canônica.",
            409,
        )
    adjustment, created = LedgerAdjustment.objects.get_or_create(
        tab=charge.tab,
        idempotency_key=f"courtesy-replacement:{correction.id}",
        defaults={
            "order_item": item,
            "kind": AdjustmentKind.COURTESY_REPLACEMENT,
            "amount_cents": -charge.amount_cents,
            "reason_code": correction.reason_code,
            "created_by_id": actor.staff_id,
        },
    )
    if (
        adjustment.order_item_id != item.id
        or adjustment.kind != AdjustmentKind.COURTESY_REPLACEMENT
        or adjustment.amount_cents != -charge.amount_cents
    ):
        raise LedgerServiceError(
            "ADJUSTMENT_IDEMPOTENCY_CONFLICT",
            "A cortesia existente não corresponde à correção.",
            409,
        )
    if created:
        record_audit_event(
            actor=actor,
            event_type="replacement.courtesy_applied",
            entity_type="LedgerAdjustment",
            entity_id=str(adjustment.id),
            reason=correction.reason_code,
            metadata={
                "correction_id": str(correction.id),
                "order_item_id": str(item.id),
                "charge_id": str(charge.id),
                "amount_cents": adjustment.amount_cents,
            },
        )
    return adjustment


@transaction.atomic
def collect_payment(
    *,
    tab_id,
    amount_cents,
    method,
    idempotency_key,
    actor,
    cash_point_id=None,
    amount_tendered_cents=None,
):
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if not tab:
        raise LedgerServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state == TabState.CLOSED:
        raise LedgerServiceError("TAB_CLOSED", "Comanda fechada não recebe pagamento.", 409)
    if amount_cents <= 0 or method not in PaymentMethod.values or not idempotency_key:
        raise LedgerServiceError("INVALID_PAYMENT", "Pagamento inválido.")
    if method in (PaymentMethod.TAP_TO_PAY, PaymentMethod.CARD_ONLINE):
        raise LedgerServiceError(
            "PAYMENT_METHOD_UNAVAILABLE",
            "Este método exige confirmação por um provedor configurado.",
            409,
        )
    existing = Payment.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
    if existing:
        if existing.amount_cents != amount_cents or existing.method != method:
            raise LedgerServiceError("IDEMPOTENCY_CONFLICT", "Chave já usada com outro pagamento.", 409)
        return existing, totals(tab)
    if amount_cents > exposure_cents(tab):
        raise LedgerServiceError("PAYMENT_EXCEEDS_EXPOSURE", "Pagamento excede o saldo em aberto.", 409)
    amount_due_cents = exposure_cents(tab)
    if method == PaymentMethod.CASH and not cash_point_id:
        raise LedgerServiceError(
            "CASH_POINT_REQUIRED",
            "Selecione um caixa aberto para registrar dinheiro.",
            409,
        )
    confirmed_at = timezone.now()
    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                tab=tab,
                amount_cents=amount_cents,
                method=method,
                idempotency_key=idempotency_key,
                status=PaymentStatus.CONFIRMED,
                confirmed_at=confirmed_at,
                received_by_id=actor.staff_id,
            )
    except IntegrityError:
        payment = Payment.objects.get(tab=tab, idempotency_key=idempotency_key)
    if method == PaymentMethod.CASH:
        from modules.cash.services import CashServiceError, record_cash_payment_movement

        try:
            record_cash_payment_movement(
                payment_id=payment.id,
                cash_point_id=cash_point_id,
                amount_due_cents=amount_due_cents,
                amount_tendered_cents=amount_tendered_cents,
                idempotency_key=f"payment:{idempotency_key}",
                actor=actor,
            )
        except CashServiceError as error:
            raise LedgerServiceError(error.code, error.message, error.status_code) from error
    result = totals(tab)
    record_audit_event(
        actor=actor,
        event_type="payment.collected",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={**result, "method": method, "status": payment.status},
    )
    return payment, result


def _confirmed_refunds_cents(payment: Payment) -> int:
    return payment.refunds.filter(status=RefundStatus.CONFIRMED).aggregate(total=Sum("amount_cents"))["total"] or 0


@transaction.atomic
def create_refund(*, payment_id, amount_cents, idempotency_key, reason, actor, cash_point_id=None):
    payment = (
        Payment.objects.select_for_update()
        .select_related("tab")
        .filter(pk=payment_id, tab__venue_id=actor.venue_id)
        .first()
    )
    if not payment:
        raise LedgerServiceError("PAYMENT_NOT_FOUND", "Pagamento não encontrado.", 404)
    if payment.tab.state == TabState.CLOSED:
        raise LedgerServiceError(
            "TAB_CLOSED",
            "Reabra a comanda antes de registrar um estorno.",
            409,
        )
    if amount_cents <= 0 or not idempotency_key:
        raise LedgerServiceError("INVALID_REFUND", "Estorno inválido.")
    existing = Refund.objects.filter(payment=payment, idempotency_key=idempotency_key).first()
    if existing:
        if existing.amount_cents != amount_cents or existing.reason != reason:
            raise LedgerServiceError("IDEMPOTENCY_CONFLICT", "Chave já usada com outro estorno.", 409)
        existing._idempotency_replay = True
        return existing, totals(payment.tab)
    if payment.status not in PaymentStatus.confirmed_money_values():
        raise LedgerServiceError("PAYMENT_NOT_CONFIRMED", "Só é possível estornar pagamento confirmado.", 409)
    refunded_cents = _confirmed_refunds_cents(payment)
    if amount_cents > payment.amount_cents - refunded_cents:
        raise LedgerServiceError("REFUND_EXCEEDS_PAYMENT", "Estorno excede o valor ainda reembolsável.", 409)

    confirmed_at = timezone.now()
    try:
        with transaction.atomic():
            refund = Refund.objects.create(
                payment=payment,
                amount_cents=amount_cents,
                idempotency_key=idempotency_key,
                reason=reason,
                status=RefundStatus.CONFIRMED,
                confirmed_at=confirmed_at,
                created_by_id=actor.staff_id,
            )
    except IntegrityError:
        refund = Refund.objects.get(payment=payment, idempotency_key=idempotency_key)
        refund._idempotency_replay = True

    if payment.method == PaymentMethod.CASH:
        if not cash_point_id:
            raise LedgerServiceError(
                "CASH_POINT_REQUIRED",
                "Selecione o caixa que pagará o estorno em dinheiro.",
                409,
            )
        from modules.cash.services import CashServiceError, record_cash_refund_movement

        try:
            record_cash_refund_movement(
                refund_id=refund.id,
                cash_point_id=cash_point_id,
                idempotency_key=f"refund:{idempotency_key}",
                actor=actor,
            )
        except CashServiceError as error:
            raise LedgerServiceError(error.code, error.message, error.status_code) from error

    total_refunded = _confirmed_refunds_cents(payment)
    payment.status = (
        PaymentStatus.REFUNDED
        if total_refunded == payment.amount_cents
        else PaymentStatus.PARTIALLY_REFUNDED
    )
    payment.save(update_fields=["status"])
    result = totals(payment.tab)
    record_audit_event(
        actor=actor,
        event_type="payment.refunded",
        entity_type="Refund",
        entity_id=str(refund.id),
        reason=reason,
        metadata={
            **result,
            "payment_id": str(payment.id),
            "amount_cents": amount_cents,
            "payment_status": payment.status,
        },
    )
    if not hasattr(refund, "_idempotency_replay"):
        refund._idempotency_replay = False
    return refund, result


@transaction.atomic
def close_tab(*, tab_id, actor):
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if not tab:
        raise LedgerServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state == TabState.CLOSED:
        return tab
    if exposure_cents(tab) != 0:
        raise LedgerServiceError("TAB_HAS_OPEN_EXPOSURE", "Comanda só fecha com saldo zero.", 409)
    tab.state, tab.closed_at, tab.version = TabState.CLOSED, timezone.now(), tab.version + 1
    tab.save(update_fields=["state", "closed_at", "version"])
    record_audit_event(actor=actor, event_type="tab.closed", entity_type="Tab", entity_id=str(tab.id), metadata={"exposure_cents": 0})
    return tab
