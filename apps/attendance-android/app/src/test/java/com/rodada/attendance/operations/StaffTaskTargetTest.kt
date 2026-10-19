package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class StaffTaskTargetTest {
    private val tab = "11111111-1111-4111-8111-111111111111"
    private val table = "22222222-2222-4222-8222-222222222222"
    private val occupancy = "33333333-3333-4333-8333-333333333333"
    private fun payload(kind: String, version: Int = 1) = JSONObject().put("target_version", version).put("target",
        JSONObject().put("kind", kind).put("tab_id", tab).put("table_id", table).put("occupancy_id", occupancy).put("generation", 7))
    @Test fun `only versioned server projection yields a routable target`() {
        assertEquals(StaffTaskTarget.Tab(tab, StaffTaskTarget.Table(table, occupancy, 7)), StaffTaskTarget.fromPayload(payload("TAB")))
        assertEquals(StaffTaskTarget.Table(table, occupancy, 7), StaffTaskTarget.fromPayload(payload("TABLE")))
        for (bad in listOf(JSONObject().put("destination_label", "Mesa $tab"), payload("UNAVAILABLE"), payload("TAB", 2), payload("FUTURE"))) {
            assertEquals(StaffTaskTarget.Unavailable, StaffTaskTarget.fromPayload(bad))
        }
    }
    @Test fun `partial malformed and label-derived identities fail closed`() {
        for (key in listOf("table_id", "occupancy_id", "generation")) {
            val partial = payload("TABLE"); partial.getJSONObject("target").remove(key)
            assertEquals(StaffTaskTarget.Unavailable, StaffTaskTarget.fromPayload(partial))
        }
        val malformed = payload("TAB"); malformed.getJSONObject("target").put("tab_id", "Mesa 08")
        assertEquals(StaffTaskTarget.Unavailable, StaffTaskTarget.fromPayload(malformed))
        for (generation in listOf("7", 7.5, -1, JSONObject.NULL)) {
            val bad = payload("TABLE"); bad.getJSONObject("target").put("generation", generation)
            assertEquals(StaffTaskTarget.Unavailable, StaffTaskTarget.fromPayload(bad))
        }
        assertEquals(StaffTaskTarget.Unavailable, StaffTaskTarget.fromPayload(payload("TAB").put("target_version", "1")))
    }
    @Test fun `typed table target requires the exact live occupancy and generation`() {
        val target = StaffTaskTarget.Table(table, occupancy, 7)
        val live = TableSummary(table, "08", "OCCUPIED", "OPEN", false, null, TableOccupancy(occupancy, 7, emptyList()))
        assertEquals(live, target.currentTable(listOf(live)))
        assertNull(target.copy(generation = 6).currentTable(listOf(live)))
        assertNull(target.copy(occupancyId = tab).currentTable(listOf(live)))
        assertNull(target.currentTable(listOf(live.copy(status = "DIRTY"))))
        assertNull(target.currentTable(listOf(live.copy(id = tab, label = "08"))))
    }
    @Test fun `delivery retains optional typed location for closed or open Tabs`() {
        val target = StaffTaskTarget.fromPayload(payload("TAB"))
        val live = TableSummary(table, "08", "OCCUPIED", "DIRECT", false, null,
            TableOccupancy(occupancy, 7, listOf(TableOccupancyTab(tab, "Closed", "CLOSED"))))
        assertEquals(live, target.currentDeliveryTable(listOf(live)))
        assertNull(target.currentDeliveryTable(listOf(live.copy(activeOccupancy = live.activeOccupancy!!.copy(generation = 8)))))
        val partial = payload("TAB"); partial.getJSONObject("target").remove("generation")
        assertEquals(StaffTaskTarget.Tab(tab), StaffTaskTarget.fromPayload(partial))
        assertNull(StaffTaskTarget.fromPayload(partial).currentDeliveryTable(listOf(live)))
    }

}
