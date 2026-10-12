package com.rodada.attendance.operations

data class RecoveryEvidence(val id: String, val label: String, val capturedAtMillis: Long, val reviewOnly: Boolean)

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
}, createdAtMillis, reviewOnly)
