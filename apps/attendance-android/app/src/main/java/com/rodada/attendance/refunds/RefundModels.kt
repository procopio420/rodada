package com.rodada.attendance.refunds

data class PaymentRefundSummary(
    val id: String,
    val amountCents: Long,
    val refundedCents: Long,
    val status: String,
) {
    val refundableCents: Long get() = (amountCents - refundedCents).coerceAtLeast(0)
}

sealed interface RefundCommand {
    val amountCents: Long
    val idempotencyKey: String
    val cashPointId: String?
}

data class DirectRefundCommand(
    val paymentId: String,
    override val amountCents: Long,
    val reason: String,
    override val idempotencyKey: String,
    override val cashPointId: String? = null,
) : RefundCommand

/** Exact amount is server validated against the correction's canonical refund requirement. */
data class SettleCorrectionRefundCommand(
    val correctionId: String,
    val paymentId: String,
    override val amountCents: Long,
    override val idempotencyKey: String,
    override val cashPointId: String? = null,
) : RefundCommand

data class RefundResult(
    val id: String,
    val paymentId: String?,
    val correctionId: String?,
    val status: String,
    val amountCents: Long,
    val chargesCents: Long,
    val paymentsCents: Long,
    val refundsCents: Long,
    val exposureCents: Long,
)

fun refundStatusLabel(status: String): String =
    when (status) {
        "CONFIRMED" -> "Confirmado"
        "PENDING", "PROCESSING" -> "Pendente"
        "CONFIRMATION_PENDING" -> "Verificando"
        "FAILED" -> "Falhou"
        else -> status
    }
