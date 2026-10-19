package com.rodada.attendance.operations

import org.json.JSONObject

/** Immutable target captured when the release confirmation is opened. */
data class TableReleaseCommand(
    val tableId: String,
    val expectedOccupancyId: String,
    val expectedGeneration: Int,
) {
    init { require(expectedGeneration > 0) }
    fun toJson(): JSONObject = JSONObject()
        .put("expected_occupancy_id", expectedOccupancyId)
        .put("expected_generation", expectedGeneration)
}
