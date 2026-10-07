from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.ledger.models import Charge, Payment, PaymentMethod
from modules.ordering.models import OrderItem, Tab, TabState


class LedgerServiceError(Exception):
    def __init__(self, code, message, status_code=400):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


def exposure_cents(tab: Tab) -> int:
    charges = tab.charges.aggregate(total=Sum("amount_cents"))["total"] or 0
    payments = tab.payments.aggregate(total=Sum("amount_cents"))["total"] or 0
    return charges - payments


def totals(tab: Tab) -> dict:
    charges = tab.charges.aggregate(total=Sum("amount_cents"))["total"] or 0
    payments = tab.payments.aggregate(total=Sum("amount_cents"))["total"] or 0
    return {"charges_cents": charges, "payments_cents": payments, "exposure_cents": charges - payments}


@transaction.atomic
def create_charges_for_order(order, actor):
    for item in OrderItem.objects.select_for_update().filter(order=order):
        Charge.objects.get_or_create(tab=order.tab, order_item=item, defaults={"amount_cents": item.line_total_cents})
    if actor is not None:
        record_audit_event(actor=actor, event_type="order.charged", entity_type="Order", entity_id=str(order.id), metadata={"tab_id": str(order.tab_id)})


@transaction.atomic
def collect_payment(*, tab_id, amount_cents, method, idempotency_key, actor):
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if not tab:
        raise LedgerServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    if tab.state == TabState.CLOSED:
        raise LedgerServiceError("TAB_CLOSED", "Comanda fechada não recebe pagamento.", 409)
    if amount_cents <= 0 or method not in PaymentMethod.values or not idempotency_key:
        raise LedgerServiceError("INVALID_PAYMENT", "Pagamento inválido.")
    existing = Payment.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
    if existing:
        if existing.amount_cents != amount_cents or existing.method != method:
            raise LedgerServiceError("IDEMPOTENCY_CONFLICT", "Chave já usada com outro pagamento.", 409)
        return existing, totals(tab)
    if amount_cents > exposure_cents(tab):
        raise LedgerServiceError("PAYMENT_EXCEEDS_EXPOSURE", "Pagamento excede o saldo em aberto.", 409)
    try:
        payment = Payment.objects.create(tab=tab, amount_cents=amount_cents, method=method, idempotency_key=idempotency_key, received_by_id=actor.staff_id)
    except IntegrityError:
        payment = Payment.objects.get(tab=tab, idempotency_key=idempotency_key)
    result = totals(tab)
    record_audit_event(actor=actor, event_type="payment.collected", entity_type="Payment", entity_id=str(payment.id), metadata={**result, "method": method})
    return payment, result


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
