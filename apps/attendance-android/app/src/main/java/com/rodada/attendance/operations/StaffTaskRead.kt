package com.rodada.attendance.operations

import org.json.JSONObject

/** A queue row is a hint. Navigation uses this fresh, exact staff task read. */
data class StaffTaskRead(val service: ServiceRequest, val delivery: DeliveryTask?) {
    companion object {
        fun fromJson(json: JSONObject, expectedId: String, expectedType: String): StaffTaskRead {
            check(json.getString("id") == expectedId && json.getString("task_type") == expectedType) { "A tarefa consultada não corresponde à selecionada." }
            check(json.getString("state") in setOf("OPEN", "CLAIMED")) { "A tarefa já saiu da fila. Atualize antes de agir." }
            val service = ServiceRequest.fromJson(json)
            val delivery = if (expectedType == "DELIVERY") {
                check(json.optString("item_state") == "READY" && !json.isNull("order_item_id")) { "O item não está mais pronto para entrega." }
                DeliveryTask(expectedId, service.state, service.destination, json.getString("product_name"),
                    json.getInt("quantity"), json.optString("tab_display_label").takeUnless { it == "null" }.orEmpty(), service.ageSeconds ?: 0,
                    service.target, json.optString("fulfillment_station").takeIf { it.isNotBlank() && it != "null" },
                    json.getString("order_item_id"), json.optString("order_id").takeIf { it.isNotBlank() && it != "null" }, service.claimedById, json.getString("item_state"), json.optString("tab_display_reference").takeUnless { it.isBlank() || it == "null" })
            } else null
            return StaffTaskRead(service, delivery)
        }
    }
}
