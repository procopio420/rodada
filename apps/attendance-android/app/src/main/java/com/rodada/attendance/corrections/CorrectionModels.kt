package com.rodada.attendance.corrections

import com.rodada.attendance.operations.formatCents

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
    val financialDeltaCents: Long = 0,
    val chargesCents: Long,
    val paymentsCents: Long,
    val refundsCents: Long,
    val exposureCents: Long,
)

/** `cancel/` is deliberately restricted to early states by the server contract. */
fun CorrectionCommand.requiresPostProductionEndpoint(): Boolean =
    action != CorrectionAction.CANCEL || itemState !in setOf("NEW", "ACCEPTED")

/** Actions that the published correction contract can accept for this item state. */
fun correctionActionsFor(itemState: String): List<CorrectionAction> =
    if (itemState in setOf("NEW", "ACCEPTED")) listOf(CorrectionAction.CANCEL) else CorrectionAction.entries

fun correctionConsequence(result: CorrectionResult): String =
    when {
        result.kind == CorrectionAction.REPLACEMENT.apiKind && result.financialDeltaCents > 0 ->
            "Diferença a cobrar: + ${formatCents(result.financialDeltaCents)}."
        result.kind == CorrectionAction.REPLACEMENT.apiKind && result.financialDeltaCents == 0L ->
            "Sem diferença de valor."
        result.kind == CorrectionAction.REPLACEMENT.apiKind && result.refundRequiredCents > 0 ->
            "Estorno necessário: ${formatCents(result.refundRequiredCents)}."
        result.kind == CorrectionAction.REPLACEMENT.apiKind ->
            "Diferença de ${formatCents(-result.financialDeltaCents)} retirada da comanda."
        else -> when (result.financialDisposition) {
        "REFUND_REQUIRED" -> "Estorno necessário: a correção ainda precisa ser resolvida por um gerente."
        "COURTESY_REPLACEMENT" -> "Novo item enviado sem nova cobrança para o cliente."
        "REVERSE_OPEN_RESPONSIBILITY" -> "O valor foi retirado da comanda."
        "MANUAL_REVIEW_REQUIRED" -> "Esta correção precisa de revisão gerencial."
        else -> "Correção registrada."
        }
    }
