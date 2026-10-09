import hashlib
import json
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.models import AuditEvent
from modules.audit.services import record_audit_event
from modules.ledger.models import Payment, PaymentMethod, PaymentStatus
from modules.ledger.services import exposure_cents
from modules.ordering.models import Tab, TabState

from .adapters import (
    PaymentProvider,
    ProviderLookupInput,
    ProviderResult,
    ProviderStartInput,
)
from .models import (
    PaymentAttempt,
    PaymentAttemptStatus,
    ProviderEvent,
    ProviderEventProcessingStatus,
)


@dataclass(frozen=True)
class ProviderServiceError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict | None = None


_PROVIDER_METHODS = {
    PaymentMethod.TAP_TO_PAY,
    PaymentMethod.CARD_ONLINE,
    PaymentMethod.PIX,
}
_PENDING_STATUSES = {
    PaymentStatus.CREATED,
    PaymentStatus.PENDING,
    PaymentStatus.PROCESSING,
    PaymentStatus.AUTHORIZED,
    PaymentStatus.CONFIRMATION_PENDING,
}
_TERMINAL_ATTEMPT_STATUSES = {
    PaymentAttemptStatus.CONFIRMED,
    PaymentAttemptStatus.FAILED,
    PaymentAttemptStatus.CANCELLED,
}


def _payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _record_external_audit(*, payment: Payment, event_type: str, metadata: dict):
    """Provider callbacks have no staff credential and must not impersonate one."""
    return AuditEvent.objects.create(
        venue_id=payment.tab.venue_id,
        event_type=event_type,
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata=metadata,
    )


def _payment_for_actor(*, payment_id, actor: ActorContext) -> Payment:
    payment = (
        Payment.objects.select_for_update()
        .select_related("tab")
        .filter(pk=payment_id, tab__venue_id=actor.venue_id)
        .first()
    )
    if payment is None:
        raise ProviderServiceError("PAYMENT_NOT_FOUND", "Pagamento não encontrado.", 404)
    return payment


def _assert_provider_method(method: str):
    if not isinstance(method, str):
        raise ProviderServiceError("INVALID_PAYMENT", "Método de pagamento inválido.")
    if method not in _PROVIDER_METHODS:
        raise ProviderServiceError(
            "PROVIDER_METHOD_REQUIRED", "Método não exige um provedor de pagamento.", 409
        )


@transaction.atomic
def _create_or_replay_provider_payment(
    *,
    amount_cents: int,
    method: str,
    idempotency_key: str,
    provider: PaymentProvider,
    tab_id,
    actor: ActorContext,
    expected_version=None,
) -> tuple[Payment, PaymentAttempt, bool]:
    _assert_provider_method(method)
    if (
        type(amount_cents) is not int
        or not 0 < amount_cents <= 2147483647
        or not isinstance(idempotency_key, str)
        or not 0 < len(idempotency_key) <= 120
        or (
            expected_version is not None
            and (type(expected_version) is not int or expected_version < 1)
        )
    ):
        raise ProviderServiceError("INVALID_PAYMENT", "Pagamento inválido.")
    capability = {
        PaymentMethod.PIX: "pix",
        PaymentMethod.TAP_TO_PAY: "tap_to_pay",
        PaymentMethod.CARD_ONLINE: "card_online",
    }[method]
    if not getattr(provider.capabilities, capability):
        raise ProviderServiceError(
            "PROVIDER_METHOD_UNAVAILABLE", "Método integrado indisponível.", 409
        )
    tab = Tab.objects.select_for_update().filter(pk=tab_id, venue_id=actor.venue_id).first()
    if tab is None:
        raise ProviderServiceError("TAB_NOT_FOUND", "Comanda não encontrada.", 404)
    existing = Payment.objects.filter(tab=tab, idempotency_key=idempotency_key).first()
    if existing is not None:
        if (
            existing.amount_cents != amount_cents
            or existing.method != method
            or existing.provider != provider.provider_key
        ):
            raise ProviderServiceError(
                "IDEMPOTENCY_CONFLICT", "A chave já foi usada para outro pagamento.", 409
            )
        attempt = existing.provider_attempts.order_by("started_at", "id").first()
        if attempt is None:
            raise ProviderServiceError(
                "PAYMENT_PROVIDER_INTEGRITY_ERROR", "Pagamento sem tentativa de provedor.", 409
            )
        return existing, attempt, True
    if tab.state == TabState.CLOSED:
        raise ProviderServiceError("TAB_CLOSED", "Comanda fechada não recebe pagamento.", 409)
    if Payment.objects.filter(tab=tab, status__in=_PENDING_STATUSES, provider__gt="").exists():
        raise ProviderServiceError(
            "PAYMENT_ALREADY_PENDING",
            "Há um pagamento integrado aguardando confirmação; não cobre novamente.",
            409,
        )
    if expected_version is not None and tab.version != expected_version:
        raise ProviderServiceError("VERSION_CONFLICT", "Comanda mudou. Confira o pagamento.", 409)
    from modules.ledger.pricing import assert_settleable, PricingError
    try:
        assert_settleable(tab)
    except PricingError as error:
        raise ProviderServiceError(error.code, error.message, error.status_code) from error
    if amount_cents > exposure_cents(tab):
        raise ProviderServiceError(
            "PAYMENT_EXCEEDS_EXPOSURE", "Pagamento excede o saldo em aberto.", 409
        )
    try:
        payment = Payment.objects.create(
            tab=tab,
            amount_cents=amount_cents,
            method=method,
            idempotency_key=idempotency_key,
            provider=provider.provider_key,
            status=PaymentStatus.CREATED,
            received_by_id=actor.staff_id,
        )
        attempt = PaymentAttempt.objects.create(
            payment=payment,
            idempotency_key=idempotency_key,
            provider=provider.provider_key,
            status=PaymentAttemptStatus.PROCESSING,
        )
    except IntegrityError as error:
        raise ProviderServiceError(
            "IDEMPOTENCY_CONFLICT", "Pagamento já está em andamento.", 409
        ) from error
    record_audit_event(
        actor=actor,
        event_type="payment.provider_initiated",
        entity_type="Payment",
        entity_id=str(payment.id),
        metadata={
            "provider": provider.provider_key,
            "method": method,
            "amount_cents": amount_cents,
        },
    )
    return payment, attempt, False


def initiate_provider_payment(
    *,
    amount_cents: int,
    method: str,
    idempotency_key: str,
    provider: PaymentProvider,
    tab_id,
    actor: ActorContext,
    expected_version=None,
) -> tuple[Payment, PaymentAttempt, bool]:
    """Persist intent before external I/O; an ambiguous start is never retried here."""
    payment, attempt, replayed = _create_or_replay_provider_payment(
        amount_cents=amount_cents,
        method=method,
        idempotency_key=idempotency_key,
        provider=provider,
        tab_id=tab_id,
        actor=actor,
        expected_version=expected_version,
    )
    if replayed:
        return payment, attempt, True
    try:
        result = provider.start_payment(
            ProviderStartInput(
                payment_id=str(payment.id),
                merchant_reference=str(payment.id),
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                method=payment.method,
                idempotency_key=payment.idempotency_key,
            )
        )
    except Exception:  # noqa: BLE001 - adapters may surface SDK-specific transport failures.
        # A timeout can mean the provider accepted the charge.  Reconciliation,
        # not another start call, is the only safe next operation.
        result = ProviderResult(
            status=PaymentStatus.CONFIRMATION_PENDING, error_code="START_AMBIGUOUS"
        )
    payment, attempt, _ = apply_provider_result(
        payment_id=payment.id,
        attempt_id=attempt.id,
        result=result,
        actor=actor,
        audit_event="payment.provider_start_resolved",
    )
    return payment, attempt, False


@transaction.atomic
def apply_provider_result(
    *,
    payment_id,
    attempt_id,
    result: ProviderResult,
    actor: ActorContext | None = None,
    audit_event: str = "payment.provider_reconciled",
) -> tuple[Payment, PaymentAttempt, bool]:
    """Apply only provider-normalized facts; a confirmed Payment never regresses."""
    tab_id = Payment.objects.values_list("tab_id", flat=True).get(pk=payment_id)
    Tab.objects.select_for_update().get(pk=tab_id)
    payment = Payment.objects.select_for_update().select_related("tab").get(pk=payment_id)
    attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt_id, payment=payment)
    incoming = result.status
    valid_statuses = _PENDING_STATUSES | {
        PaymentStatus.CONFIRMED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
        PaymentStatus.EXPIRED,
    }
    if incoming not in valid_statuses:
        raise ProviderServiceError("INVALID_PROVIDER_STATUS", "Status de provedor inválido.", 409)
    if result.provider_payment_id and payment.provider_payment_id not in (
        "",
        result.provider_payment_id,
    ):
        raise ProviderServiceError(
            "PROVIDER_REFERENCE_CONFLICT",
            "Referência do provedor não corresponde ao pagamento.",
            409,
        )

    if (
        payment.status in PaymentStatus.confirmed_money_values()
        and incoming != PaymentStatus.CONFIRMED
    ):
        return payment, attempt, True
    if (
        payment.status in PaymentStatus.confirmed_money_values()
        and incoming == PaymentStatus.CONFIRMED
    ):
        return payment, attempt, True

    if (
        payment.status in (PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.EXPIRED)
        and incoming in _PENDING_STATUSES
    ):
        return payment, attempt, True

    settlement_key = (
        result.metadata.get("settlement_key", "") if incoming == PaymentStatus.CONFIRMED else ""
    )
    if settlement_key:
        # Serialize ownership across Tabs/Venues; distinct checkout IDs cannot spend
        # the same merchant transaction twice. DB uniqueness is the final guard.
        if transaction.get_connection().vendor == "postgresql":
            with transaction.get_connection().cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    [
                        int.from_bytes(
                            hashlib.sha256(settlement_key.encode()).digest()[:8], "big", signed=True
                        )
                    ],
                )
        if (
            Payment.objects.filter(provider_settlement_key=settlement_key)
            .exclude(pk=payment.pk)
            .exists()
        ):
            incoming = PaymentStatus.CONFIRMATION_PENDING
            result = ProviderResult(status=incoming, error_code="SETTLEMENT_ALREADY_OWNED")
            settlement_key = ""

    now = timezone.now()
    previous_status = payment.status
    payment_updates = []
    attempt_updates = []
    if result.provider_payment_id and not payment.provider_payment_id:
        payment.provider_payment_id = result.provider_payment_id
        payment_updates.append("provider_payment_id")
    if result.provider_attempt_id and not attempt.provider_attempt_id:
        attempt.provider_attempt_id = result.provider_attempt_id
        attempt_updates.append("provider_attempt_id")
    if result.metadata:
        # Adapters must provide sanitized operational metadata only.
        attempt.metadata = {**attempt.metadata, **result.metadata}
        attempt_updates.append("metadata")
    if result.error_code:
        attempt.error_code = result.error_code
        attempt_updates.append("error_code")

    if incoming == PaymentStatus.CONFIRMED:
        if settlement_key:
            payment.provider_settlement_key = settlement_key
            payment_updates.append("provider_settlement_key")
        payment.tab.version += 1
        payment.tab.save(update_fields=["version"])
        payment.status, payment.confirmed_at = PaymentStatus.CONFIRMED, now
        attempt.status, attempt.finished_at = PaymentAttemptStatus.CONFIRMED, now
        payment_updates.extend(["status", "confirmed_at"])
        attempt_updates.extend(["status", "finished_at"])
    elif incoming in (PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.EXPIRED):
        payment.status = incoming
        setattr(
            payment,
            "failed_at"
            if incoming in (PaymentStatus.FAILED, PaymentStatus.EXPIRED)
            else "cancelled_at",
            now,
        )
        attempt.status = (
            PaymentAttemptStatus.FAILED
            if incoming in (PaymentStatus.FAILED, PaymentStatus.EXPIRED)
            else PaymentAttemptStatus.CANCELLED
        )
        attempt.finished_at = now
        payment_updates.extend(
            [
                "status",
                "failed_at"
                if incoming in (PaymentStatus.FAILED, PaymentStatus.EXPIRED)
                else "cancelled_at",
            ]
        )
        attempt_updates.extend(["status", "finished_at"])
    elif incoming == PaymentStatus.CONFIRMATION_PENDING:
        payment.status = PaymentStatus.CONFIRMATION_PENDING
        attempt.status = PaymentAttemptStatus.CONFIRMATION_PENDING
        payment_updates.append("status")
        attempt_updates.append("status")
    elif payment.status != PaymentStatus.CONFIRMATION_PENDING:
        # Pending/authorized provider facts move forward, but cannot make a
        # previous ambiguous outcome look safely retryable again.
        payment.status = incoming
        attempt.status = PaymentAttemptStatus.PROCESSING
        payment_updates.append("status")
        attempt_updates.append("status")

    if payment_updates:
        payment.save(update_fields=sorted(set(payment_updates)))
        from modules.house_account.services import sync_attention

        sync_attention(payment.tab, actor)
    if attempt_updates:
        attempt.save(update_fields=sorted(set(attempt_updates)))
    metadata = {
        "provider": payment.provider,
        "status": payment.status,
        "previous_status": previous_status,
        "attempt_id": str(attempt.id),
    }
    if actor is not None:
        record_audit_event(
            actor=actor,
            event_type=audit_event,
            entity_type="Payment",
            entity_id=str(payment.id),
            metadata=metadata,
        )
    else:
        _record_external_audit(payment=payment, event_type=audit_event, metadata=metadata)
    return payment, attempt, False


@transaction.atomic
def ingest_provider_webhook(
    *, provider: PaymentProvider, payload: dict, signature: str
) -> tuple[ProviderEvent, bool]:
    if not provider.verify_webhook(payload=payload, signature=signature):
        raise ProviderServiceError(
            "INVALID_PROVIDER_SIGNATURE", "Assinatura de provedor inválida.", 401
        )
    try:
        normalized = provider.parse_webhook(payload=payload)
    except Exception as error:
        raise ProviderServiceError(
            "PROVIDER_EVENT_UNVERIFIED", "Evento não verificado; reenvie para reconciliação.", 503
        ) from error
    if transaction.get_connection().vendor == "postgresql":
        lock_key = int.from_bytes(
            hashlib.sha256(
                f"{provider.provider_key}:{normalized.provider_event_id}".encode()
            ).digest()[:8],
            "big",
            signed=True,
        )
        with transaction.get_connection().cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_key])
    if not normalized.provider_event_id:
        raise ProviderServiceError("INVALID_PROVIDER_EVENT", "Evento sem identificador.", 400)
    event_hash = _payload_hash(payload)
    existing = (
        ProviderEvent.objects.select_for_update()
        .filter(provider=provider.provider_key, provider_event_id=normalized.provider_event_id)
        .first()
    )
    if existing is not None:
        if existing.payload_hash != event_hash:
            raise ProviderServiceError(
                "PROVIDER_EVENT_CONFLICT",
                "Evento do provedor conflita com evidência recebida.",
                409,
            )
        return existing, True

    payment = Payment.objects.filter(
        pk=normalized.merchant_reference, provider=provider.provider_key
    ).first()
    if payment:
        Tab.objects.select_for_update().get(pk=payment.tab_id)
        payment = Payment.objects.select_for_update().select_related("tab").get(pk=payment.pk)
    event = ProviderEvent.objects.create(
        provider=provider.provider_key,
        provider_event_id=normalized.provider_event_id,
        payload_hash=event_hash,
        event_type=normalized.event_type,
        payment=payment,
        metadata=normalized.metadata,
    )
    if payment is None:
        event.processing_status = ProviderEventProcessingStatus.FAILED
        event.processing_error = "PAYMENT_NOT_FOUND"
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "processing_error", "processed_at"])
        return event, False
    attempt = payment.provider_attempts.order_by("started_at", "id").last()
    if attempt is None:
        event.processing_status = ProviderEventProcessingStatus.FAILED
        event.processing_error = "ATTEMPT_NOT_FOUND"
        event.processed_at = timezone.now()
        event.save(update_fields=["processing_status", "processing_error", "processed_at"])
        return event, False
    event.attempt = attempt
    payment, _attempt, ignored = apply_provider_result(
        payment_id=payment.id,
        attempt_id=attempt.id,
        result=ProviderResult(
            status=normalized.status,
            provider_payment_id=normalized.provider_payment_id,
            provider_attempt_id=normalized.provider_attempt_id,
            metadata=normalized.metadata,
        ),
        audit_event="payment.provider_webhook_applied",
    )
    event.processing_status = (
        ProviderEventProcessingStatus.IGNORED if ignored else ProviderEventProcessingStatus.APPLIED
    )
    event.processed_at = timezone.now()
    event.save(update_fields=["attempt", "processing_status", "processed_at"])
    return event, False


def reconcile_provider_payment(
    *, payment_id, provider: PaymentProvider, actor: ActorContext | None = None
) -> tuple[Payment, PaymentAttempt]:
    """Explicit recovery for pending/ambiguous payments; it never starts another charge."""
    with transaction.atomic():
        if actor is not None:
            payment = _payment_for_actor(payment_id=payment_id, actor=actor)
        else:
            payment = Payment.objects.select_related("tab").get(
                pk=payment_id, provider=provider.provider_key
            )
        if payment.provider != provider.provider_key:
            raise ProviderServiceError(
                "PROVIDER_MISMATCH", "Provedor não corresponde ao pagamento.", 409
            )
        if payment.status not in _PENDING_STATUSES:
            attempt = payment.provider_attempts.order_by("started_at", "id").last()
            if attempt is None:
                raise ProviderServiceError("ATTEMPT_NOT_FOUND", "Tentativa não encontrada.", 409)
            return payment, attempt
        attempt = payment.provider_attempts.order_by("started_at", "id").last()
        if attempt is None:
            raise ProviderServiceError("ATTEMPT_NOT_FOUND", "Tentativa não encontrada.", 409)
    try:
        result = provider.lookup_payment(
            ProviderLookupInput(
                payment_id=str(payment.id),
                merchant_reference=str(payment.id),
                provider_payment_id=payment.provider_payment_id,
            )
        )
    except Exception:  # noqa: BLE001 - reconciliation outages are intentionally non-terminal.
        result = ProviderResult(
            status=PaymentStatus.CONFIRMATION_PENDING, error_code="RECONCILIATION_UNAVAILABLE"
        )
    payment, attempt, _ = apply_provider_result(
        payment_id=payment.id,
        attempt_id=attempt.id,
        result=result,
        actor=actor,
        audit_event="payment.provider_reconciled",
    )
    return payment, attempt
