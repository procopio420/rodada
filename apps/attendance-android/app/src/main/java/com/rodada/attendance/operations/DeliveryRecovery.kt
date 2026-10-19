package com.rodada.attendance.operations

import org.json.JSONObject

/** Exact task read for recovery, deliberately separate from active-queue navigation. */
internal data class DeliveryRecoveryRead(val taskId: String, val itemId: String, val taskState: String, val itemState: String) {
    val confirmed get() = taskState == "DONE" && itemState == "DELIVERED"
    val canComplete get() = taskState in setOf("OPEN", "CLAIMED") && itemState in setOf("READY", "PICKED_UP", "DELIVERED")
    companion object {
        fun fromJson(json: JSONObject, expectedTaskId: String): DeliveryRecoveryRead {
            check(json.getString("id") == expectedTaskId && json.getString("task_type") == "DELIVERY") { "A entrega consultada não corresponde à intenção original." }
            val itemId = json.getString("order_item_id")
            check(itemId.isNotBlank() && itemId != "null") { "Identidade do item ausente na entrega original." }
            return DeliveryRecoveryRead(expectedTaskId, itemId, json.getString("state"), json.getString("item_state"))
        }
    }
}

/** Task ID is the backend's idempotency identity. Never infer completion from queue absence. */
internal suspend fun reconcileDelivery(taskId: String, allowSubmit: Boolean,
    read: suspend () -> DeliveryRecoveryRead, submit: suspend () -> Unit, checkCurrent: () -> Unit): DeliveryRecoveryRead {
    checkCurrent()
    val before = read()
    checkCurrent()
    check(before.taskId == taskId) { "A entrega retornada não corresponde à original." }
    if (before.confirmed || !allowSubmit) return before
    check(before.canComplete) { "A entrega não permite conclusão; confira o estado canônico original." }
    // A transport failure remains unknown until a later explicit exact read. No blind replay.
    submit()
    checkCurrent()
    val after = read()
    checkCurrent()
    check(after.taskId == taskId && after.itemId == before.itemId) { "A identidade da entrega mudou durante a confirmação." }
    check(after.confirmed) { "Entrega ainda sem confirmação canônica. Preserve a intenção original." }
    return after
}
