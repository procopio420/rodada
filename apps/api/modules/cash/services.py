"""Commands and queries for cash custody.

Payment/refund hooks deliberately live here rather than in ledger so ledger
remains provider and drawer agnostic.  The caller must invoke the hook inside
the same database transaction that makes a cash payment/refund confirmed.
"""

from dataclasses import dataclass
from datetime import date

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from modules.access.context import ActorContext
from modules.audit.services import record_audit_event
from modules.cash.models import (
    CashMovement,
    CashMovementKind,
    CashPoint,
    CashReviewStatus,
    CashShift,
    CashShiftStatus,
    CashTenderDetail,
)


@dataclass(frozen=True)
class CashServiceError(Exception):
    code: str
    message: str
    status_code: int = 400


def _movement_total(shift: CashShift, *, post_close: bool | None = None) -> int:
    movements = shift.movements.all()
    if post_close is not None:
        movements = movements.filter(is_post_close_correction=post_close)
    return movements.aggregate(total=Sum("amount_cents"))["total"] or 0


def _audit(actor: ActorContext, event_type: str, shift: CashShift, **metadata) -> None:
    record_audit_event(
        actor=actor,
        event_type=event_type,
        entity_type="CashShift",
        entity_id=str(shift.id),
        metadata={
            "cash_point_id": str(shift.cash_point_id),
            "cash_shift_id": str(shift.id),
            **metadata,
        },
    )


def _cash_point_for_actor(*, cash_point_id, actor: ActorContext, lock: bool = False) -> CashPoint:
    points = CashPoint.objects
    if lock:
        points = points.select_for_update()
    point = points.filter(pk=cash_point_id, venue_id=actor.venue_id).first()
    if not point:
        raise CashServiceError("CASH_POINT_NOT_FOUND", "Ponto de caixa não encontrado.", 404)
    return point


def _shift_for_actor(*, shift_id, actor: ActorContext, lock: bool = False) -> CashShift:
    shifts = CashShift.objects.select_related("cash_point")
    if lock:
        shifts = shifts.select_for_update()
    shift = shifts.filter(pk=shift_id, venue_id=actor.venue_id).first()
    if not shift:
        raise CashServiceError("CASH_SHIFT_NOT_FOUND", "Turno de caixa não encontrado.", 404)
    return shift


def _active_shift(*, point: CashPoint, lock: bool = False) -> CashShift:
    shifts = CashShift.objects.filter(
        cash_point=point,
        status__in=(CashShiftStatus.OPEN, CashShiftStatus.COUNTING),
    ).select_related("cash_point")
    if lock:
        shifts = shifts.select_for_update()
    shift = shifts.first()
    if not shift:
        raise CashServiceError("ACTIVE_CASH_SHIFT_REQUIRED", "Abra um turno de caixa para continuar.", 409)
    return shift


def _require_open(shift: CashShift) -> None:
    if shift.status == CashShiftStatus.COUNTING:
        raise CashServiceError("CASH_SHIFT_COUNTING", "Caixa em conferência; movimentos estão bloqueados.", 409)
    if shift.status != CashShiftStatus.OPEN:
        raise CashServiceError("CASH_SHIFT_CLOSED", "Turno de caixa fechado.", 409)


def _require_key(idempotency_key: str) -> None:
    if not idempotency_key or len(idempotency_key) > 120:
        raise CashServiceError("IDEMPOTENCY_KEY_REQUIRED", "Chave de idempotência inválida.")


def _replay_or_conflict(
    *, shift: CashShift, idempotency_key: str, kind: str, amount_cents: int, reason: str
) -> CashMovement | None:
    existing = CashMovement.objects.filter(shift=shift, idempotency_key=idempotency_key).first()
    if not existing:
        return None
    if existing.kind != kind or existing.amount_cents != amount_cents or existing.reason != reason:
        raise CashServiceError(
            "IDEMPOTENCY_CONFLICT", "Chave já usada para outro movimento de caixa.", 409
        )
    return existing


def _create_movement(
    *,
    shift: CashShift,
    kind: str,
    amount_cents: int,
    idempotency_key: str,
    actor: ActorContext,
    reason: str = "",
    payment_id=None,
    refund_id=None,
    correction_of: CashMovement | None = None,
    is_post_close_correction: bool = False,
    occurred_at=None,
) -> tuple[CashMovement, bool]:
    replay = _replay_or_conflict(
        shift=shift,
        idempotency_key=idempotency_key,
        kind=kind,
        amount_cents=amount_cents,
        reason=reason,
    )
    if replay:
        return replay, False
    try:
        # Keep a caught uniqueness race from poisoning the outer command
        # transaction (Django marks an atomic block rollback-only otherwise).
        with transaction.atomic():
            movement = CashMovement.objects.create(
                shift=shift,
                kind=kind,
                amount_cents=amount_cents,
                payment_id=payment_id,
                refund_id=refund_id,
                actor_id=actor.staff_id,
                actor_session_id=actor.session_id,
                device_id=actor.device_id,
                reason=reason,
                occurred_at=occurred_at or timezone.now(),
                idempotency_key=idempotency_key,
                correction_of=correction_of,
                is_post_close_correction=is_post_close_correction,
            )
    except IntegrityError:
        # A unique payment/refund link or idempotency key won a concurrent race.
        movement = CashMovement.objects.filter(shift=shift, idempotency_key=idempotency_key).first()
        if movement:
            return movement, False
        if payment_id:
            movement = CashMovement.objects.filter(payment_id=payment_id).first()
        elif refund_id:
            movement = CashMovement.objects.filter(refund_id=refund_id).first()
        else:
            movement = None
        if movement:
            return movement, False
        raise
    return movement, True


@transaction.atomic
def open_cash_shift(
    *,
    cash_point_id,
    opening_float_cents: int,
    business_date,
    idempotency_key: str,
    actor: ActorContext,
) -> CashShift:
    _require_key(idempotency_key)
    if opening_float_cents < 0:
        raise CashServiceError("INVALID_OPENING_FLOAT", "Fundo inicial não pode ser negativo.")
    if not isinstance(business_date, date):
        raise CashServiceError("INVALID_BUSINESS_DATE", "Data operacional inválida.")
    point = _cash_point_for_actor(cash_point_id=cash_point_id, actor=actor, lock=True)
    if not point.active:
        raise CashServiceError("CASH_POINT_INACTIVE", "Ponto de caixa inativo.", 409)
    replay = CashShift.objects.filter(
        cash_point=point, opening_idempotency_key=idempotency_key
    ).first()
    if replay:
        if replay.opening_float_cents != opening_float_cents or replay.business_date != business_date:
            raise CashServiceError("IDEMPOTENCY_CONFLICT", "Chave já usada para outra abertura.", 409)
        return replay
    if CashShift.objects.filter(
        cash_point=point, status__in=(CashShiftStatus.OPEN, CashShiftStatus.COUNTING)
    ).exists():
        raise CashServiceError("CASH_SHIFT_ALREADY_ACTIVE", "Já existe turno ativo neste caixa.", 409)
    shift = CashShift.objects.create(
        venue_id=actor.venue_id,
        cash_point=point,
        business_date=business_date,
        opened_by_id=actor.staff_id,
        opening_float_cents=opening_float_cents,
        opening_idempotency_key=idempotency_key,
    )
    if opening_float_cents:
        _create_movement(
            shift=shift,
            kind=CashMovementKind.OPENING_FLOAT,
            amount_cents=opening_float_cents,
            idempotency_key="opening:" + idempotency_key,
            actor=actor,
        )
    _audit(actor, "cash.shift_opened", shift, opening_float_cents=opening_float_cents)
    return shift


def cash_shift_position(shift: CashShift) -> dict:
    """Return deterministic active or corrected historical cash position."""
    if shift.status == CashShiftStatus.CLOSED:
        correction_cents = _movement_total(shift, post_close=True)
        expected_snapshot = shift.expected_amount_cents_snapshot
        return {
            "expected_cents": expected_snapshot,
            "expected_at_close_cents": expected_snapshot,
            "post_close_correction_cents": correction_cents,
            "corrected_expected_cents": (
                expected_snapshot + correction_cents if expected_snapshot is not None else None
            ),
            "counted_amount_cents": shift.counted_amount_cents,
            "discrepancy_cents": shift.discrepancy_cents,
        }
    expected = _movement_total(shift)
    return {
        "expected_cents": expected,
        "expected_at_close_cents": None,
        "post_close_correction_cents": 0,
        "corrected_expected_cents": expected,
        "counted_amount_cents": None,
        "discrepancy_cents": None,
    }


def active_cash_shift(*, cash_point_id, actor: ActorContext) -> CashShift:
    """Resolve the OPEN/COUNTING shift selectable for a physical cash point."""
    point = _cash_point_for_actor(cash_point_id=cash_point_id, actor=actor)
    return _active_shift(point=point)


def cash_shift_movements(*, shift_id, actor: ActorContext):
    shift = _shift_for_actor(shift_id=shift_id, actor=actor)
    return shift.movements.select_related("actor", "payment", "refund").order_by("recorded_at", "id")


@transaction.atomic
def supply_cash(
    *, shift_id, amount_cents: int, reason: str, idempotency_key: str, actor: ActorContext
) -> CashMovement:
    _require_key(idempotency_key)
    if amount_cents <= 0 or not reason.strip():
        raise CashServiceError("INVALID_CASH_SUPPLY", "Suprimento exige valor positivo e motivo.")
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    _require_open(shift)
    movement, created = _create_movement(
        shift=shift,
        kind=CashMovementKind.SUPPLY,
        amount_cents=amount_cents,
        idempotency_key=idempotency_key,
        actor=actor,
        reason=reason.strip(),
    )
    if created:
        shift.version += 1
        shift.save(update_fields=["version"])
        _audit(actor, "cash.supplied", shift, movement_id=str(movement.id), amount_cents=amount_cents, reason=reason.strip())
    return movement


@transaction.atomic
def withdraw_cash(
    *,
    shift_id,
    amount_cents: int,
    reason: str,
    idempotency_key: str,
    actor: ActorContext,
    allow_negative_expected: bool = False,
) -> CashMovement:
    _require_key(idempotency_key)
    if amount_cents <= 0 or not reason.strip():
        raise CashServiceError("INVALID_CASH_WITHDRAWAL", "Sangria exige valor positivo e motivo.")
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    _require_open(shift)
    if not allow_negative_expected and _movement_total(shift) - amount_cents < 0:
        raise CashServiceError(
            "CASH_WITHDRAWAL_EXCEEDS_EXPECTED",
            "Sangria excede o valor esperado; exige override autorizado.",
            409,
        )
    movement, created = _create_movement(
        shift=shift,
        kind=CashMovementKind.WITHDRAWAL,
        amount_cents=-amount_cents,
        idempotency_key=idempotency_key,
        actor=actor,
        reason=reason.strip(),
    )
    if created:
        shift.version += 1
        shift.save(update_fields=["version"])
        _audit(actor, "cash.withdrawn", shift, movement_id=str(movement.id), amount_cents=-amount_cents, reason=reason.strip())
    return movement


@transaction.atomic
def start_cash_count(*, shift_id, actor: ActorContext) -> CashShift:
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    if shift.status == CashShiftStatus.COUNTING:
        return shift
    if shift.status != CashShiftStatus.OPEN:
        raise CashServiceError("CASH_SHIFT_CLOSED", "Turno de caixa fechado.", 409)
    shift.status = CashShiftStatus.COUNTING
    shift.version += 1
    shift.save(update_fields=["status", "version"])
    _audit(actor, "cash.count_started", shift, version=shift.version)
    return shift


@transaction.atomic
def close_cash_shift(
    *,
    shift_id,
    counted_amount_cents: int,
    review_threshold_cents: int,
    actor: ActorContext,
    expected_version: int | None = None,
) -> CashShift:
    if counted_amount_cents < 0 or review_threshold_cents < 0:
        raise CashServiceError("INVALID_CASH_COUNT", "Contagem e limite devem ser não negativos.")
    # Payment/refund hooks lock CashPoint then CashShift.  Keep the same order
    # here so a payment-versus-close race serializes instead of deadlocking.
    initial_shift = _shift_for_actor(shift_id=shift_id, actor=actor)
    _cash_point_for_actor(cash_point_id=initial_shift.cash_point_id, actor=actor, lock=True)
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    if shift.status == CashShiftStatus.CLOSED:
        if shift.counted_amount_cents != counted_amount_cents:
            raise CashServiceError("CASH_SHIFT_ALREADY_CLOSED", "Turno já fechado com outra contagem.", 409)
        return shift
    if shift.status != CashShiftStatus.COUNTING:
        raise CashServiceError("CASH_SHIFT_NOT_COUNTING", "Inicie a conferência antes de fechar.", 409)
    if expected_version is not None and expected_version != shift.version:
        raise CashServiceError("CASH_SHIFT_VERSION_CONFLICT", "Caixa mudou; atualize antes de fechar.", 409)
    expected = _movement_total(shift)
    discrepancy = counted_amount_cents - expected
    shift.status = CashShiftStatus.CLOSED
    shift.closed_by_id = actor.staff_id
    shift.closed_at = timezone.now()
    shift.counted_amount_cents = counted_amount_cents
    shift.expected_amount_cents_snapshot = expected
    shift.discrepancy_cents = discrepancy
    shift.review_status = (
        CashReviewStatus.PENDING
        if abs(discrepancy) > review_threshold_cents
        else CashReviewStatus.NOT_REQUIRED
    )
    shift.version += 1
    shift.save(
        update_fields=[
            "status", "closed_by", "closed_at", "counted_amount_cents",
            "expected_amount_cents_snapshot", "discrepancy_cents", "review_status", "version",
        ]
    )
    _audit(
        actor,
        "cash.shift_closed",
        shift,
        expected_amount_cents=expected,
        counted_amount_cents=counted_amount_cents,
        discrepancy_cents=discrepancy,
        review_status=shift.review_status,
    )
    return shift


@transaction.atomic
def review_cash_discrepancy(*, shift_id, reason: str, actor: ActorContext) -> CashShift:
    if not reason.strip():
        raise CashServiceError("CASH_REVIEW_REASON_REQUIRED", "Informe o motivo da revisão.")
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    if shift.status != CashShiftStatus.CLOSED:
        raise CashServiceError("CASH_SHIFT_NOT_CLOSED", "Feche o turno antes de revisar.", 409)
    if shift.review_status == CashReviewStatus.REVIEWED:
        if shift.review_reason != reason.strip():
            raise CashServiceError("CASH_REVIEW_ALREADY_RECORDED", "Turno já foi revisado.", 409)
        return shift
    if shift.review_status != CashReviewStatus.PENDING:
        raise CashServiceError("CASH_REVIEW_NOT_REQUIRED", "Este turno não exige revisão.", 409)
    shift.review_status = CashReviewStatus.REVIEWED
    shift.reviewed_by_id = actor.staff_id
    shift.reviewed_at = timezone.now()
    shift.review_reason = reason.strip()
    shift.version += 1
    shift.save(update_fields=["review_status", "reviewed_by", "reviewed_at", "review_reason", "version"])
    _audit(actor, "cash.discrepancy_reviewed", shift, reason=reason.strip(), discrepancy_cents=shift.discrepancy_cents)
    return shift


@transaction.atomic
def record_late_cash_correction(
    *,
    shift_id,
    amount_cents: int,
    reason: str,
    idempotency_key: str,
    actor: ActorContext,
    correction_of_id=None,
    occurred_at=None,
) -> CashMovement:
    _require_key(idempotency_key)
    if amount_cents == 0 or not reason.strip():
        raise CashServiceError("INVALID_LATE_CORRECTION", "Correção exige valor não nulo e motivo.")
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    if shift.status != CashShiftStatus.CLOSED:
        raise CashServiceError("CASH_SHIFT_NOT_CLOSED", "Correção tardia exige turno fechado.", 409)
    correction_of = None
    if correction_of_id:
        correction_of = CashMovement.objects.filter(pk=correction_of_id, shift=shift).first()
        if not correction_of:
            raise CashServiceError("CASH_MOVEMENT_NOT_FOUND", "Movimento original não encontrado.", 404)
    movement, created = _create_movement(
        shift=shift,
        kind=CashMovementKind.CORRECTION,
        amount_cents=amount_cents,
        idempotency_key=idempotency_key,
        actor=actor,
        reason=reason.strip(),
        correction_of=correction_of,
        is_post_close_correction=True,
        occurred_at=occurred_at,
    )
    if created:
        shift.version += 1
        shift.save(update_fields=["version"])
        _audit(
            actor,
            "cash.late_correction_recorded",
            shift,
            movement_id=str(movement.id),
            amount_cents=amount_cents,
            correction_of_id=str(correction_of_id) if correction_of_id else None,
            reason=reason.strip(),
        )
    return movement


@transaction.atomic
def record_cash_payment_movement(
    *,
    payment_id,
    cash_point_id,
    amount_due_cents: int,
    amount_tendered_cents: int | None,
    idempotency_key: str,
    actor: ActorContext,
) -> CashMovement:
    """Integration hook for a *confirmed* CASH Payment.

    This is intentionally not called by a client: ledger must call it inside
    its payment-confirmation transaction, before that transaction commits.
    """
    from modules.ledger.models import Payment, PaymentMethod, PaymentStatus

    _require_key(idempotency_key)
    payment = (
        Payment.objects.select_for_update()
        .select_related("tab")
        .filter(pk=payment_id, tab__venue_id=actor.venue_id)
        .first()
    )
    if not payment:
        raise CashServiceError("PAYMENT_NOT_FOUND", "Pagamento não encontrado.", 404)
    if payment.method != PaymentMethod.CASH or payment.status not in PaymentStatus.confirmed_money_values():
        raise CashServiceError("PAYMENT_NOT_CONFIRMED_CASH", "Pagamento não é dinheiro confirmado.", 409)
    if amount_due_cents < payment.amount_cents:
        raise CashServiceError("INVALID_CASH_TENDER", "Valor devido não pode ser menor que o pagamento.")
    tendered = amount_tendered_cents if amount_tendered_cents is not None else payment.amount_cents
    if tendered < payment.amount_cents:
        raise CashServiceError("INVALID_CASH_TENDER", "Valor recebido é menor que o pagamento.")
    point = _cash_point_for_actor(cash_point_id=cash_point_id, actor=actor, lock=True)
    shift = _active_shift(point=point, lock=True)
    _require_open(shift)
    existing = CashMovement.objects.filter(payment=payment).first()
    if existing:
        if existing.shift.cash_point_id != point.id or existing.amount_cents != payment.amount_cents:
            raise CashServiceError("PAYMENT_CASH_MOVEMENT_CONFLICT", "Pagamento já pertence a outro caixa.", 409)
        return existing
    movement, created = _create_movement(
        shift=shift,
        kind=CashMovementKind.CASH_PAYMENT,
        amount_cents=payment.amount_cents,
        idempotency_key=idempotency_key,
        actor=actor,
        payment_id=payment.id,
    )
    if created:
        CashTenderDetail.objects.create(
            payment=payment,
            shift=shift,
            amount_due_cents=amount_due_cents,
            amount_tendered_cents=tendered,
            change_given_cents=tendered - payment.amount_cents,
        )
        shift.version += 1
        shift.save(update_fields=["version"])
        _audit(actor, "cash.payment_recorded", shift, movement_id=str(movement.id), payment_id=str(payment.id), amount_cents=payment.amount_cents)
    return movement


@transaction.atomic
def record_cash_refund_movement(
    *, refund_id, cash_point_id, idempotency_key: str, actor: ActorContext
) -> CashMovement:
    """Integration hook for a confirmed Refund physically paid from a drawer."""
    from modules.ledger.models import PaymentMethod, Refund, RefundStatus

    _require_key(idempotency_key)
    refund = (
        Refund.objects.select_for_update()
        .select_related("payment__tab")
        .filter(pk=refund_id, payment__tab__venue_id=actor.venue_id)
        .first()
    )
    if not refund:
        raise CashServiceError("REFUND_NOT_FOUND", "Estorno não encontrado.", 404)
    if refund.status != RefundStatus.CONFIRMED or refund.payment.method != PaymentMethod.CASH:
        raise CashServiceError("REFUND_NOT_CONFIRMED_CASH", "Estorno não é dinheiro confirmado.", 409)
    point = _cash_point_for_actor(cash_point_id=cash_point_id, actor=actor, lock=True)
    shift = _active_shift(point=point, lock=True)
    _require_open(shift)
    existing = CashMovement.objects.filter(refund=refund).first()
    if existing:
        if existing.shift.cash_point_id != point.id or existing.amount_cents != -refund.amount_cents:
            raise CashServiceError("REFUND_CASH_MOVEMENT_CONFLICT", "Estorno já pertence a outro caixa.", 409)
        return existing
    movement, created = _create_movement(
        shift=shift,
        kind=CashMovementKind.CASH_REFUND,
        amount_cents=-refund.amount_cents,
        idempotency_key=idempotency_key,
        actor=actor,
        refund_id=refund.id,
    )
    if created:
        shift.version += 1
        shift.save(update_fields=["version"])
        _audit(actor, "cash.refund_recorded", shift, movement_id=str(movement.id), refund_id=str(refund.id), amount_cents=-refund.amount_cents)
    return movement


def cash_close_preview(*, shift_id, actor: ActorContext) -> dict:
    shift = _shift_for_actor(shift_id=shift_id, actor=actor)
    result = cash_shift_position(shift)
    result.update({"shift_id": str(shift.id), "status": shift.status, "version": shift.version})
    return result


def unresolved_cash_exceptions(*, business_date, actor: ActorContext) -> list[CashShift]:
    return list(
        CashShift.objects.filter(venue_id=actor.venue_id, business_date=business_date)
        .exclude(status=CashShiftStatus.CLOSED, review_status=CashReviewStatus.REVIEWED)
        .order_by("cash_point__label", "opened_at")
    )
