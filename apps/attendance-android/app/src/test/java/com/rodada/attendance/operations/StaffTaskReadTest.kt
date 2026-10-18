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
    @Test fun `canonical ready and picked up remain deliverable with exact item station and authorized label`() {
        for (itemState in listOf("READY", "PICKED_UP")) {
            val delivery = payload().put("task_type", "DELIVERY").put("item_state", itemState)
                .put("order_item_id", "original-item").put("order_id", "original-order")
                .put("product_name", "Chopp Pilsen").put("quantity", 2).put("fulfillment_station", "BAR")
                .put("tab_display_label", "Rafael").put("tab_display_reference", "#1049")
            val read = requireNotNull(StaffTaskRead.fromJson(delivery, "task", "DELIVERY").delivery)
            assertEquals(itemState, read.itemState); assertEquals("original-item", read.orderItemId)
            assertEquals("BAR", read.fulfillmentStation); assertEquals("Rafael", read.tabLabel)
            assertEquals("#1049", read.tabReference)
        }
    }

}
