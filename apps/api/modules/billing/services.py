from dataclasses import dataclass

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.billing.models import (
    Adjustment,
    Charge,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from modules.ordering.models import Order, Tab, TabState


@dataclass(frozen=True)
class BillingServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


RECEIVED_PAYMENT_STATES = (
    PaymentStatus.CONFIRMED,
    PaymentStatus.PARTIALLY_REFUNDED,
    PaymentStatus.REFUNDED,
)


def create_charges_for_order(order: Order) -> list[Charge]:
    charges = []
    for item in order.items.all():
        charge, _created = Charge.objects.get_or_create(
            order_item=item,
            defaults={
                "venue_id": order.tab.venue_id,
                "tab_id": order.tab_id,
                "amount_cents": item.line_total_cents,
            },
        )
        charges.append(charge)
    return charges


def exposure_cents(*, tab_id) -> int:
    charges = (
        Charge.objects.filter(tab_id=tab_id).aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    adjustments = (
        Adjustment.objects.filter(tab_id=tab_id).aggregate(total=Sum("effect_cents"))["total"]
        or 0
    )
    payments = (
        Payment.objects.filter(
            tab_id=tab_id,
            status__in=RECEIVED_PAYMENT_STATES,
        ).aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    return int(charges) + int(adjustments) - int(payments)


@transaction.atomic
def record_manual_payment(
    *,
    actor: ActorContext,
    tab_id,
    amount_cents: int,
    method: str,
    idempotency_key: str,
) -> Payment:
    if method not in PaymentMethod.values:
        raise BillingServiceError("INVALID_PAYMENT_METHOD", "Método de pagamento inválido.")
    if amount_cents <= 0:
        raise BillingServiceError("INVALID_PAYMENT_AMOUNT", "Valor do pagamento deve ser positivo.")
    if not idempotency_key.strip():
        raise BillingServiceError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency key é obrigatória.")

    existing = Payment.objects.filter(
        venue_id=actor.venue_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing:
        if (
            existing.tab_id != tab_id
            or existing.amount_cents != amount_cents
            or existing.method != method
        ):
            raise BillingServiceError(
                "IDEMPOTENCY_CONFLICT",
                "Esta idempotency key já foi usada com outro payload.",
                409,
            )
        return existing

    tab = (
        Tab.objects.select_for_update()
        .filter(pk=tab_id, venue_id=actor.venue_id)
        .first()
    )
    if not tab:
        raise BillingServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state not in (TabState.OPEN, TabState.REQUIRES_ACTION, TabState.SETTLING):
        raise BillingServiceError(
            "TAB_NOT_PAYABLE",
            "Esta comanda não aceita pagamento.",
            409,
        )

    current_exposure = exposure_cents(tab_id=tab.id)
    if current_exposure <= 0:
        raise BillingServiceError("NO_OPEN_EXPOSURE", "Comanda não possui saldo em aberto.", 409)
    if amount_cents > current_exposure:
        raise BillingServiceError(
            "PAYMENT_EXCEEDS_EXPOSURE",
            "Pagamento não pode exceder o saldo em aberto.",
            409,
            {"exposure_cents": current_exposure},
        )

    payment = Payment.objects.create(
        venue_id=actor.venue_id,
        tab=tab,
        amount_cents=amount_cents,
        method=method,
        status=PaymentStatus.CONFIRMED,
        idempotency_key=idempotency_key,
        created_by_id=actor.staff_id,
        confirmed_at=timezone.now(),
    )
    tab.version += 1
    tab.save(update_fields=["version"])

    record_audit_event(
        actor=actor,
        event_type="payment.confirmed_manual",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={
            "tab_id": str(tab.id),
            "amount_cents": amount_cents,
            "method": method,
            "exposure_after_cents": exposure_cents(tab_id=tab.id),
            "tab_version": tab.version,
        },
    )
    return payment
