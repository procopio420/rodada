"""Two-person post-close cash correction workflow.

The approval transaction creates one append-only movement and one durable
decision. Neither a rejected nor pending proposal touches the cash ledger.
"""
from django.db import transaction
from django.utils import timezone

from modules.audit.services import record_audit_event
from modules.cash.models import CashCorrectionRequest, CashMovement
from modules.cash.services import CashServiceError, _shift_for_actor, record_late_cash_correction


class CashCorrectionError(Exception):
    def __init__(self, code, message, status_code=409):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def correction_payload(row):
    return dict(
        id=str(row.id),
        shift_id=str(row.shift_id),
        business_date=row.shift.business_date,
        cash_point_label=row.shift.cash_point.label,
        amount_cents=row.amount_cents,
        reason=row.reason,
        requested_at=row.requested_at,
        requested_by=str(row.requested_by_id),
        correction_of_id=str(row.correction_of_id) if row.correction_of_id else None,
        idempotency_key=row.idempotency_key,
        status=row.status,
        version=row.version,
        decided_at=row.decided_at,
        decided_by=str(row.decided_by_id) if row.decided_by_id else None,
        decision_reason=row.decision_reason,
        movement_id=str(row.movement_id) if row.movement_id else None,
    )


def _audit(actor, event, request, **details):
    record_audit_event(
        actor=actor,
        event_type=event,
        entity_type="CashCorrectionRequest",
        entity_id=str(request.pk),
        metadata={"shift_id": str(request.shift_id), "amount_cents": request.amount_cents, **details},
    )


@transaction.atomic
def request_cash_correction(*, shift_id, amount_cents, reason, idempotency_key, actor, correction_of_id=None):
    if type(amount_cents) is not int or not -2_000_000_000 <= amount_cents <= 2_000_000_000 or amount_cents == 0:
        raise CashCorrectionError("INVALID_CORRECTION_AMOUNT", "Informe um valor não nulo em centavos.", 400)
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 240:
        raise CashCorrectionError("CORRECTION_REASON_REQUIRED", "Informe o motivo da correção.", 400)
    if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key.strip()) <= 120:
        raise CashCorrectionError("IDEMPOTENCY_KEY_REQUIRED", "Informe uma chave de idempotência.", 400)
    shift = _shift_for_actor(shift_id=shift_id, actor=actor, lock=True)
    if shift.status != "CLOSED":
        raise CashCorrectionError("CASH_SHIFT_NOT_CLOSED", "Correções exigem caixa fechado.")
    original = None
    if correction_of_id:
        original = CashMovement.objects.filter(pk=correction_of_id, shift=shift).first()
        if original is None:
            raise CashCorrectionError("CASH_MOVEMENT_NOT_FOUND", "Movimento original não encontrado.", 404)
    key = idempotency_key.strip()
    existing = CashCorrectionRequest.objects.filter(shift=shift, idempotency_key=key).first()
    if existing:
        if (existing.amount_cents, existing.reason, existing.correction_of_id) != (
            amount_cents, reason.strip(), original.pk if original else None
        ):
            raise CashCorrectionError("IDEMPOTENCY_CONFLICT", "Chave já utilizada para outra proposta.")
        return existing, False
    row = CashCorrectionRequest.objects.create(
        shift=shift, requested_by_id=actor.staff_id, requested_at=timezone.now(),
        amount_cents=amount_cents, reason=reason.strip(), idempotency_key=key, correction_of=original,
    )
    _audit(actor, "cash.correction_requested", row, status="PENDING")
    return row, True


@transaction.atomic
def decide_cash_correction(*, request_id, expected_version, decision, reason, actor):
    if decision not in ("APPROVED", "REJECTED"):
        raise CashCorrectionError("INVALID_CORRECTION_DECISION", "A decisão deve ser aprovar ou rejeitar.", 400)
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 240:
        raise CashCorrectionError("CORRECTION_DECISION_REASON_REQUIRED", "Justifique a decisão.", 400)
    # Scope before locking; locks are always shift -> proposal -> movement.
    candidate = CashCorrectionRequest.objects.filter(pk=request_id, shift__venue_id=actor.venue_id).first()
    if candidate is None:
        raise CashCorrectionError("CORRECTION_NOT_FOUND", "Correção não encontrada.", 404)
    shift = _shift_for_actor(shift_id=candidate.shift_id, actor=actor, lock=True)
    row = CashCorrectionRequest.objects.select_for_update().get(pk=candidate.pk)
    if row.requested_by_id == actor.staff_id:
        raise CashCorrectionError("SELF_APPROVAL_FORBIDDEN", "Outro gerente deve decidir esta correção.", 403)
    if row.status != "PENDING":
        # Safe replay after a lost response, never create another movement.
        if row.status == decision and row.decision_reason == reason.strip() and row.version == expected_version + 1:
            return row
        raise CashCorrectionError("CORRECTION_ALREADY_DECIDED", "Esta proposta já recebeu decisão.")
    if type(expected_version) is not int or expected_version != row.version:
        raise CashCorrectionError("STALE_VERSION", "Atualize a proposta antes de decidir.")
    if shift.status != "CLOSED":
        raise CashCorrectionError("CASH_SHIFT_NOT_CLOSED", "O turno precisa estar fechado.")
    if decision == "APPROVED":
        try:
            movement = record_late_cash_correction(
                shift_id=shift.pk, amount_cents=row.amount_cents, reason=row.reason,
                idempotency_key="approved-correction:" + str(row.pk), actor=actor,
                correction_of_id=row.correction_of_id,
            )
        except CashServiceError as error:
            raise CashCorrectionError(error.code, error.message, error.status_code) from error
        row.movement = movement
    row.status = decision
    row.version += 1
    row.decided_by_id = actor.staff_id
    row.decided_at = timezone.now()
    row.decision_reason = reason.strip()
    row.save(update_fields=["movement", "status", "version", "decided_by", "decided_at", "decision_reason"])
    _audit(actor, "cash.correction_decided", row, decision=decision, movement_id=str(row.movement_id) if row.movement_id else None)
    return row
