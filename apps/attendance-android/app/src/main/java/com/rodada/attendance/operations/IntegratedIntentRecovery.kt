package com.rodada.attendance.operations

import com.rodada.attendance.payments.IntegratedPayment

internal fun validateIntegratedIntent(original: RecoveryIntent.StartPayment, payment: IntegratedPayment) {
    check(payment.id.isNotBlank() && payment.tabId == original.tabId && payment.amountCents == original.amountCents &&
        payment.method == original.method.apiValue) { "A resposta não corresponde ao pagamento original." }
}

/** Resolve UUID first, even if this Tab has older terminal provider payments. */
internal suspend fun recoverIntegratedIntent(original: RecoveryIntent.StartPayment,
    replay: suspend (RecoveryIntent.StartPayment) -> IntegratedPayment,
    reconcile: suspend (String) -> IntegratedPayment,
): IntegratedPayment {
    val associated = replay(original)
    validateIntegratedIntent(original, associated)
    val canonical = reconcile(associated.id)
    check(canonical.id == associated.id) { "A reconsulta retornou outro recebimento." }
    validateIntegratedIntent(original, canonical)
    return canonical
}
