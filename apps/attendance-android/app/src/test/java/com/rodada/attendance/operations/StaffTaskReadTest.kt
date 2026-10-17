package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StaffTaskReadTest {
    private fun payload() = JSONObject().put("id", "task").put("task_type", "BILL_REQUEST")
        .put("state", "OPEN").put("target_version", 1).put("destination_label", "Mesa 12")
        .put("target", JSONObject().put("kind", "TABLE").put("table_id", "11111111-1111-4111-8111-111111111111")
            .put("occupancy_id", "22222222-2222-4222-8222-222222222222").put("generation", 3))
    @Test fun `fresh revoked guest projection routes only to table and never to queued tab`() {
        val read = StaffTaskRead.fromJson(payload(), "task", "BILL_REQUEST")
        assertTrue(read.service.target is StaffTaskTarget.Table)
        assertFalse(read.service.target is StaffTaskTarget.Tab)
        assertEquals("BILL_REQUEST", read.service.type)
        assertNull(read.delivery)
    }
    @Test fun `wrong task type state and delivery no longer ready fail closed`() {
        for (bad in listOf(payload().put("id", "other"), payload().put("task_type", "SERVICE_REQUEST"), payload().put("state", "DONE"))) {
            assertThrows(IllegalStateException::class.java) { StaffTaskRead.fromJson(bad, "task", "BILL_REQUEST") }
        }
        val delivery = payload().put("task_type", "DELIVERY").put("item_state", "DELIVERED").put("order_item_id", "item")
        assertThrows(IllegalStateException::class.java) { StaffTaskRead.fromJson(delivery, "task", "DELIVERY") }
    }
}
