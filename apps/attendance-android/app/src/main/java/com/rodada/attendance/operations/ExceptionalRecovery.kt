package com.rodada.attendance.operations

import org.json.JSONObject

data class ExceptionalRecoveryTarget(val tabId: String, val itemId: String? = null,
    val paymentId: String? = null, val correctionId: String? = null, val correctionStatus: String? = null) {
    fun validate(original: RecoveryIntent) {
        require(tabId.isNotBlank()) { "Comanda original ausente da resposta." }
        val matches = when (original) {
            is RecoveryIntent.Correction -> itemId == original.orderItemId && paymentId == null && correctionId == null
            is RecoveryIntent.Refund -> paymentId == original.paymentId && when (original.kind) {
                RefundRecoveryKind.DIRECT -> itemId == null && correctionId == null
                RefundRecoveryKind.SETTLE_CORRECTION -> original.correctionId != null && correctionId == original.correctionId &&
                    !itemId.isNullOrBlank() && correctionStatus in setOf("REQUESTED", "APPLIED", "REJECTED")
            }
            else -> false
        }
        require(matches) { "O contexto recebido não corresponde à operação original." }
    }

    fun validate(detail: TabDetail) {
        require(detail.summary.id == tabId &&
            (itemId == null || detail.orders.any { order -> order.items.any { it.id == itemId } }) &&
            (paymentId == null || detail.payments.any { it.id == paymentId })) {
            "O alvo original não foi encontrado na comanda consultada. Não repita a operação."
        }
    }

    companion object {
        fun fromJson(json: JSONObject) = ExceptionalRecoveryTarget(json.getString("tab_id"),
            json.nullableId("order_item_id"), json.nullableId("payment_id"), json.nullableId("correction_id"), json.nullableId("correction_status"))
        private fun JSONObject.nullableId(key: String) = if (!has(key) || isNull(key)) null else getString(key)
    }
}

data class ExceptionalRecoveryContext(val original: RecoveryIntent, val target: ExceptionalRecoveryTarget, val detail: TabDetail)
