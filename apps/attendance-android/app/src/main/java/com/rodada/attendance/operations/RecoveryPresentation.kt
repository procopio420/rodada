package com.rodada.attendance.operations

data class RecoveryEvidence(val id: String, val label: String, val capturedAtMillis: Long, val reviewOnly: Boolean,
    val tabId: String? = null, val taskId: String? = null, val summary: String = "", val status: String = "", val shiftId: String? = null) {
    val canOpenContext: Boolean get() = !reviewOnly && (tabId != null || taskId != null || shiftId != null)
}

fun RecoveryIntent.evidence(reviewOnly: Boolean = false) = RecoveryEvidence(id, when (this) {
    is RecoveryIntent.ConfirmOrder -> "Pedido"
    is RecoveryIntent.StartPayment -> "Recebimento"
    is RecoveryIntent.Correction -> "Correção de pedido"
    is RecoveryIntent.Refund -> "Estorno"
    is RecoveryIntent.Pricing -> "Ajuste de conta"
    is RecoveryIntent.TabStructure -> "Operação de comanda"
    is RecoveryIntent.CashMovement -> "Movimento de caixa"
    is RecoveryIntent.CashClose -> "Fechamento de caixa"
    is RecoveryIntent.CompleteDelivery -> "Conclusão de entrega"
}, createdAtMillis, reviewOnly,
    tabId = when (this) {
        is RecoveryIntent.ConfirmOrder -> tabId
        is RecoveryIntent.StartPayment -> tabId
        is RecoveryIntent.Pricing -> tabId
        is RecoveryIntent.TabStructure -> tabId
        else -> null
    }.takeUnless { reviewOnly },
    taskId = (this as? RecoveryIntent.CompleteDelivery)?.deliveryTaskId.takeUnless { reviewOnly },
    summary = when (this) {
        is RecoveryIntent.ConfirmOrder -> "${lines.sumOf { it.quantity.toLong() }} unidades guardadas"
        is RecoveryIntent.StartPayment -> "${formatCents(amountCents)} · ${method.label}"
        else -> ""
    }, status = OrderRecoveryPolicy.stateLabel(state), shiftId = when (this) {
        is RecoveryIntent.CashMovement -> shiftId
        is RecoveryIntent.CashClose -> shiftId
        else -> null
    }.takeUnless { reviewOnly })

fun OperationsUiState.pendingEvidence(): List<RecoveryEvidence> =
    (recoveryEvidence + queuedOrders.map { it.evidence() }).distinctBy { it.id }.sortedBy { it.capturedAtMillis }
