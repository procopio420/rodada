package com.rodada.attendance.operations

/** Coordinates existing canonical operations; never invents ledger or payment policy. */
internal suspend fun settleReceipt(
    original: RecoveryIntent.StartPayment,
    collect: suspend (RecoveryIntent.StartPayment) -> String,
    persist: (RecoveryIntent.StartPayment) -> Unit,
    read: suspend (String) -> TabDetail,
    close: suspend (String) -> Unit,
    observed: (TabDetail) -> Unit,
): TabDetail {
    var confirmed = original
    if (confirmed.confirmedPaymentId == null) {
        val paymentId = collect(original)
        check(paymentId.isNotBlank()) { "Identidade do recebimento ausente." }
        confirmed = original.copy(confirmedPaymentId = paymentId)
        // A failed checkpoint prevents Close. Original UUID remains safe to reconcile.
        persist(confirmed)
    }
    var detail = read(original.tabId)
    check(detail.summary.id == original.tabId) { "Comanda recebida não corresponde à intenção original." }
    check(detail.payments.any { it.id == confirmed.confirmedPaymentId && !it.simulated && it.status == "CONFIRMED" }) {
        "Recebimento ainda não confirmado no histórico canônico."
    }
    observed(detail)
    if (original.closeRequested && detail.summary.state !in setOf("CLOSED", "CANCELLED")) {
        check(detail.summary.exposureCents == 0L) {
            "Recebido; há saldo atualizado. Mantenha aberta ou confira a conta antes de encerrar."
        }
        close(original.tabId)
        detail = read(original.tabId)
        observed(detail)
        check(detail.summary.state == "CLOSED") { "Recebido; encerramento ainda não confirmado." }
    }
    return detail
}
