package com.rodada.attendance.operations

import org.json.JSONObject

/** A successful POST is insufficient until this exact Order appears in its Tab. */
data class OrderConfirmationReceipt(val orderId: String, val tabId: String) {
    fun requireReadback(detail: TabDetail) {
        if (detail.summary.id != tabId || detail.orders.none { it.id == orderId }) unverified()
    }

    companion object {
        private val uuid = Regex("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", RegexOption.IGNORE_CASE)

        fun fromJson(body: JSONObject, expectedTabId: String): OrderConfirmationReceipt {
            val orderId = body.optString("id")
            val tabId = body.optString("tab_id")
            if (!uuid.matches(orderId) || !uuid.matches(tabId) || tabId != expectedTabId) unverified()
            return OrderConfirmationReceipt(orderId, tabId)
        }

        private fun unverified(): Nothing = throw OperationsApiException(
            502, "ORDER_CONFIRMATION_UNVERIFIED",
            "Resultado do pedido ainda não confirmado. Verifique a mesma intenção antes de continuar.",
        )
    }
}
