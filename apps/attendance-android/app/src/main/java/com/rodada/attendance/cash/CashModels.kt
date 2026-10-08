package com.rodada.attendance.cash

/**
 * Server snapshots for the cash domain. Amounts are integer cents and movement amounts are
 * signed, exactly as returned by the canonical API.
 */
data class CashPointSnapshot(
    val id: String,
    val label: String,
    val activeShift: CashShiftSnapshot?,
)

data class CashShiftSnapshot(
    val id: String,
    val cashPointId: String,
    val businessDate: String,
    val status: String,
    val openingFloatCents: Long,
    val countedAmountCents: Long?,
    val expectedAmountCentsSnapshot: Long?,
    val discrepancyCents: Long?,
    val reviewStatus: String,
    val version: Long,
    val expectedCents: Long?,
    val expectedAtCloseCents: Long?,
    val postCloseCorrectionCents: Long?,
    val correctedExpectedCents: Long?,
)

data class CashShiftDetail(
    val shift: CashShiftSnapshot,
    val movements: List<CashMovementSnapshot>,
)

data class CashMovementSnapshot(
    val id: String,
    val kind: String,
    val amountCents: Long,
    val paymentId: String?,
    val refundId: String?,
    val actorId: String,
    val reason: String,
    val occurredAt: String,
    val recordedAt: String,
    val isPostCloseCorrection: Boolean,
)

data class OpenCashShiftCommand(
    val cashPointId: String,
    val openingFloatCents: Long,
    val businessDate: String,
    val idempotencyKey: String,
)

data class CashMovementCommand(
    val amountCents: Long,
    val reason: String,
    val idempotencyKey: String,
)

data class CashWithdrawalCommand(
    val amountCents: Long,
    val reason: String,
    val idempotencyKey: String,
    /** Only set by an explicitly authorized UI flow; the server remains authoritative. */
    val allowNegativeExpected: Boolean = false,
)

data class CloseCashShiftCommand(
    val countedAmountCents: Long,
    val reviewThresholdCents: Long,
    /** Canonical optimistic-lock version returned by the latest shift snapshot. */
    val expectedVersion: Long?,
)

data class LateCashCorrectionCommand(
    val amountCents: Long,
    val reason: String,
    val idempotencyKey: String,
    val correctionOfId: String? = null,
)

class CashApiException(
    val status: Int,
    val code: String,
    override val message: String,
) : Exception(message)
