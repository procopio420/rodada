package com.rodada.attendance.operations

/** Coordinates existing canonical operations; never invents ledger or payment policy. */
internal suspend fun settleReceipt(
    original: RecoveryIntent.StartPayment,
    collect: suspend (RecoveryIntent.StartPayment) -> String,
    persist: (RecoveryIntent.StartPayment) -> Unit,
    read: suspend (String) -> TabDetail,
    close: suspend (String) -> Unit,
    observed: (TabDetail) -> Unit,
    checkCurrent: () -> Unit = {},
): TabDetail {
    checkCurrent()
    var confirmed = original
    if (confirmed.confirmedPaymentId == null) {
        val paymentId = collect(original)
        checkCurrent()
        check(paymentId.isNotBlank()) { "Identidade do recebimento ausente." }
        confirmed = original.copy(confirmedPaymentId = paymentId)
        // A failed checkpoint prevents Close. Original UUID remains safe to reconcile.
        persist(confirmed)
    }
    var detail = read(original.tabId)
    checkCurrent()
    check(detail.summary.id == original.tabId) { "Comanda recebida não corresponde à intenção original." }
    check(detail.payments.any { receiptMatches(original, confirmed.confirmedPaymentId, it) }) {
        "Recebimento ainda não confirmado no histórico canônico."
    }
    check(detail.summary.state != "CLOSED" || detail.summary.exposureCents == 0L) { "Encerramento divergente do saldo canônico." }
    check(!original.closeRequested || detail.summary.state != "CANCELLED") { "Recebido; comanda cancelada exige revisão do estado canônico." }
    observed(detail)
    if (original.closeRequested && detail.summary.state !in setOf("CLOSED", "CANCELLED")) {
        check(detail.summary.exposureCents == 0L) {
            "Recebido; há saldo atualizado. Mantenha aberta ou confira a conta antes de encerrar."
        }
        close(original.tabId)
        detail = read(original.tabId)
        checkCurrent()
        check(detail.summary.id == original.tabId && detail.summary.state == "CLOSED" && detail.summary.exposureCents == 0L &&
            detail.payments.any { receiptMatches(original, confirmed.confirmedPaymentId, it) }) {
            "Recebido; encerramento ainda não confirmado."
        }
        observed(detail)
    }
    return detail
}

internal fun receiptMatches(original: RecoveryIntent.StartPayment, paymentId: String?, payment: TabPayment): Boolean =
    payment.id == paymentId && !payment.simulated && payment.status == "CONFIRMED" &&
        payment.amountCents == original.amountCents && payment.method == original.method.apiValue
