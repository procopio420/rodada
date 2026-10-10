package com.rodada.attendance.operations

import org.json.JSONObject

data class ServiceRequest(
    val id: String, val type: String, val state: String, val destination: String,
    val claimedById: String?, val ageSeconds: Long?,
) {
    fun belongsToOther(staffId: String) = claimedById != null && claimedById != staffId
    fun responsibility(staffId: String) = when {
        claimedById == staffId -> "Você está responsável"
        claimedById != null -> "Outro operador está responsável"
        else -> "Sem responsável"
    }
    val title get() = if (type == "BILL_REQUEST") "Pedido de conta" else "Atendimento"
    val ageLabel get() = ageSeconds?.takeIf { it >= 0 }?.let { "Solicitado há ${it / 60} min" } ?: "Tempo não informado"
    companion object {
        fun fromJson(json: JSONObject) = ServiceRequest(
            json.getString("id"), json.getString("task_type"), json.getString("state"),
            json.optString("destination_label").ifBlank { "Destino não informado" },
            if (json.isNull("claimed_by_id")) null else json.getString("claimed_by_id"),
            if (json.isNull("age_seconds")) null else json.getLong("age_seconds"),
        )
    }
}

data class ServiceRequestAction(val taskId: String, val complete: Boolean)
