package com.rodada.attendance.corrections

/**
 * Deliberately typed correction commands.  The client only chooses an operational
 * intent; policy, approval and financial disposition remain server-authoritative.
 */
enum class CorrectionAction(val apiKind: String, val label: String) {
    CANCEL("CANCEL_ITEM", "Cancelar"),
    REMAKE("REMAKE", "Refazer"),
    REPLACEMENT("REPLACEMENT", "Trocar"),
}

data class CorrectionCommand(
    val itemId: String,
    val itemState: String,
    val action: CorrectionAction,
    val reasonCode: String,
    val reasonText: String,
    val idempotencyKey: String,
    val replacementProductId: String? = null,
)

data class CorrectionResult(
    val id: String,
    val status: String,
    val kind: String,
    val financialDisposition: String,
    val refundRequiredCents: Long,
    val replacementOrderItemId: String?,
    val orderItemId: String,
    val orderItemState: String,
    val chargesCents: Long,
    val paymentsCents: Long,
    val refundsCents: Long,
    val exposureCents: Long,
)

/** `cancel/` is deliberately restricted to early states by the server contract. */
fun CorrectionCommand.requiresPostProductionEndpoint(): Boolean =
    action != CorrectionAction.CANCEL || itemState !in setOf("NEW", "ACCEPTED")

fun correctionConsequence(result: CorrectionResult): String =
    when (result.financialDisposition) {
        "REFUND_REQUIRED" -> "Estorno necessário: a correção ainda precisa ser resolvida por um gerente."
        "COURTESY_REPLACEMENT" -> "Novo item enviado sem nova cobrança para o cliente."
        "REVERSE_OPEN_RESPONSIBILITY" -> "O valor foi retirado da comanda."
        "MANUAL_REVIEW_REQUIRED" -> "Esta correção precisa de revisão gerencial."
        else -> "Correção registrada."
    }
