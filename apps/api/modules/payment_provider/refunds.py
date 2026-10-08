"""Reserve refunds before I/O; only verified provider events change the ledger."""

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.ledger.models import Payment, PaymentStatus, Refund, RefundStatus
from modules.ledger.services import totals
from modules.ordering.models import Tab

from .models import ProviderRefundRequest
from .services import ProviderServiceError
from .sumup import minor


@transaction.atomic
def reserve_refund(*, payment_id, amount_cents, key, reason, actor):
    payment = Payment.objects.filter(pk=payment_id, tab__venue_id=actor.venue_id).first()
    if payment is None:
        raise ProviderServiceError("PAYMENT_NOT_FOUND", "Pagamento não encontrado.", 404)
    Tab.objects.select_for_update().get(pk=payment.tab_id)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    existing = Refund.objects.filter(payment=payment, idempotency_key=key).first()
    if existing:
        if existing.amount_cents != amount_cents or existing.reason != reason:
            raise ProviderServiceError(
                "IDEMPOTENCY_CONFLICT", "Intenção de estorno diferente.", 409
            )
        return existing, True
    reserved = (
        payment.refunds.exclude(status=RefundStatus.FAILED).aggregate(total=Sum("amount_cents"))[
            "total"
        ]
        or 0
    )
    if type(amount_cents) is not int or amount_cents <= 0 or not key or len(key) > 120:
        raise ProviderServiceError("INVALID_REFUND", "Estorno inválido.")
    if (
        payment.status not in PaymentStatus.confirmed_money_values()
        or amount_cents > payment.amount_cents - reserved
    ):
        raise ProviderServiceError(
            "REFUND_EXCEEDS_PAYMENT", "Valor não disponível para estorno.", 409
        )
    refund = Refund.objects.create(
        payment=payment,
        amount_cents=amount_cents,
        idempotency_key=key,
        reason=reason,
        created_by_id=actor.staff_id,
        status=RefundStatus.PENDING,
    )
    record_audit_event(
        actor=actor,
        event_type="payment.provider_refund_requested",
        entity_type="Refund",
        entity_id=str(refund.pk),
    )
    return refund, False


def request_provider_refund(*, payment_id, amount_cents, key, reason, actor, provider):
    if not hasattr(provider, "request_refund"):
        raise ProviderServiceError(
            "PROVIDER_REFUND_UNAVAILABLE", "Estorno integrado indisponível.", 409
        )
    payment = Payment.objects.get(
        pk=payment_id, tab__venue_id=actor.venue_id, provider=provider.provider_key
    )
    attempt = payment.provider_attempts.order_by("started_at").last()
    tx_id = attempt.metadata.get("transaction_id", "") if attempt else ""
    if not tx_id:
        raise ProviderServiceError(
            "TRANSACTION_UNVERIFIED", "Reconcilie o pagamento antes do estorno.", 409
        )
    # Snapshot existing provider events before submitting. They cannot confirm this request.
    tx = provider.transport(
        "GET", f"/v2.1/merchants/{provider.merchant_code}/transactions?id={tx_id}"
    )
    if tx.get("id") != tx_id or tx.get("merchant_code") != provider.merchant_code:
        raise ProviderServiceError("TRANSACTION_UNVERIFIED", "Estorno não verificado.", 409)
    baseline = [str(event["id"]) for event in tx.get("transaction_events", []) if event.get("id")]
    refund, replayed = reserve_refund(
        payment_id=payment_id, amount_cents=amount_cents, key=key, reason=reason, actor=actor
    )
    if not replayed:
        ProviderRefundRequest.objects.create(
            refund=refund, transaction_id=tx_id, baseline_event_ids=baseline
        )
        try:
            provider.request_refund(transaction_id=tx_id, amount_cents=amount_cents)
        except Exception:  # noqa: BLE001 - provider request may have succeeded
            # Ambiguous requests remain reserved and are never resubmitted.
            return refund
    return refund


@transaction.atomic
def apply_refund_evidence(*, refund_id, event, actor):
    refund = Refund.objects.select_related("payment").get(
        pk=refund_id, payment__tab__venue_id=actor.venue_id
    )
    Tab.objects.select_for_update().get(pk=refund.payment.tab_id)
    payment = Payment.objects.select_for_update().get(pk=refund.payment_id)
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    if refund.status == RefundStatus.CONFIRMED:
        return refund
    if (
        event.get("event_type") != "REFUND"
        or event.get("status") != "SUCCESSFUL"
        or minor(event.get("amount")) != refund.amount_cents
        or not event.get("id")
    ):
        raise ProviderServiceError("REFUND_UNVERIFIED", "Estorno ainda não verificado.", 409)
    if (
        Refund.objects.filter(
            payment__provider=payment.provider, provider_refund_id=str(event["id"])
        )
        .exclude(pk=refund.pk)
        .exists()
    ):
        raise ProviderServiceError(
            "REFUND_EVENT_ALREADY_APPLIED", "Evento de estorno já aplicado.", 409
        )
    refund.provider_refund_id = str(event["id"])
    refund.status = RefundStatus.CONFIRMED
    refund.confirmed_at = timezone.now()
    refund.save(update_fields=["provider_refund_id", "status", "confirmed_at"])
    refunded = payment.refunds.filter(status=RefundStatus.CONFIRMED).aggregate(
        total=Sum("amount_cents")
    )["total"]
    payment.status = (
        PaymentStatus.REFUNDED
        if refunded == payment.amount_cents
        else PaymentStatus.PARTIALLY_REFUNDED
    )
    payment.save(update_fields=["status"])
    from modules.house_account.services import sync_attention

    sync_attention(payment.tab, actor)
    record_audit_event(
        actor=actor,
        event_type="payment.refunded",
        entity_type="Refund",
        entity_id=str(refund.pk),
        metadata={"payment_id": str(payment.pk), **totals(payment.tab)},
    )
    return refund


def reconcile_provider_refund(*, refund_id, actor, provider):
    request = ProviderRefundRequest.objects.select_related("refund__payment").get(
        refund_id=refund_id,
        refund__payment__tab__venue_id=actor.venue_id,
        refund__payment__provider=provider.provider_key,
    )
    if request.refund.status == RefundStatus.CONFIRMED:
        return request.refund
    from urllib.parse import quote, urlencode

    tx = provider.transport(
        "GET",
        f"/v2.1/merchants/{quote(provider.merchant_code, safe='')}/transactions?"
        + urlencode({"id": request.transaction_id}),
    )
    if tx.get("id") != request.transaction_id or tx.get("merchant_code") != provider.merchant_code:
        raise ProviderServiceError("REFUND_UNVERIFIED", "Transação de estorno não verificada.", 409)
    events = [
        event
        for event in tx.get("transaction_events", [])
        if event.get("event_type") == "REFUND"
        and event.get("status") == "SUCCESSFUL"
        and str(event.get("id")) not in request.baseline_event_ids
        and minor(event.get("amount")) == request.refund.amount_cents
    ]
    if len(events) != 1:
        raise ProviderServiceError("REFUND_UNVERIFIED", "Estorno exige reconciliação.", 409)
    return apply_refund_evidence(refund_id=refund_id, event=events[0], actor=actor)
