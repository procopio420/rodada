package com.rodada.attendance.payments

/** Only the authenticated backend status controls success/retry presentation. */
data class IntegratedPayment(
    val id: String,
    val tabId: String,
    val amountCents: Long,
    val status: String,
    val copyPaste: String = "",
    val qrCode: String = "",
) {
    val blocksNewCharge: Boolean get() = status !in setOf("CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED", "FAILED", "CANCELLED")
    val confirmed: Boolean get() = status in setOf("CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED")
    val message: String get() = when (status) {
        "CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED" -> "Pagamento confirmado pelo Rodada."
        "FAILED" -> "Pagamento não concluído. Escolha outro método."
        "CANCELLED" -> "Pagamento cancelado pelo provedor."
        "PROCESSING", "AUTHORIZED" -> "Processando pagamento. Não cobre novamente."
        "PENDING" -> "Aguardando pagamento Pix."
        else -> "Confirmando pagamento. Não cobre novamente."
    }
}
