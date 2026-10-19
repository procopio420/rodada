package com.rodada.attendance.operations

import org.json.JSONObject

data class ServiceRequest(
    val id: String, val type: String, val state: String, val destination: String,
    val claimedById: String?, val ageSeconds: Long?,
    val target: StaffTaskTarget = StaffTaskTarget.Unavailable,
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
            json.optString("claimed_by_id").takeIf { it.isNotBlank() && it != "null" },
            if (json.isNull("age_seconds")) null else json.getLong("age_seconds"),
            StaffTaskTarget.fromPayload(json),
        )
    }
}

data class ServiceRequestAction(val taskId: String, val complete: Boolean, val originatingSessionKey: String? = null) {
    fun belongsToSession(key: String) = originatingSessionKey == key
}

internal fun serviceRequestActionForSession(pending: ServiceRequestAction?, key: String, taskId: String, complete: Boolean) =
    pending?.takeIf { it.belongsToSession(key) } ?: ServiceRequestAction(taskId, complete, key)
