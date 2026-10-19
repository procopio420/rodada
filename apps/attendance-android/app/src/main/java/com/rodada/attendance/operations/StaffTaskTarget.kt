package com.rodada.attendance.operations

import org.json.JSONObject
import java.util.UUID

/** Staff-safe PR218 projection. Display labels are never routing keys. */
sealed interface StaffTaskTarget {
    data class Tab(val tabId: String, val tableTarget: Table? = null) : StaffTaskTarget
    data class Table(val tableId: String, val occupancyId: String, val generation: Int) : StaffTaskTarget
    data object Unavailable : StaffTaskTarget

    companion object {
        fun fromPayload(payload: JSONObject): StaffTaskTarget {
            if (payload.opt("target_version") != 1) return Unavailable
            val target = payload.optJSONObject("target") ?: return Unavailable
            fun id(key: String): String? = target.optString(key).takeIf { raw ->
                runCatching { UUID.fromString(raw).toString() == raw.lowercase() }.getOrDefault(false)
            }
            fun tableContext(): Table? {
                val table = id("table_id") ?: return null
                val occupancy = id("occupancy_id") ?: return null
                val generation = target.opt("generation") as? Int ?: return null
                return if (generation >= 0) Table(table, occupancy, generation) else null
            }
            return when (target.optString("kind")) {
                "TAB" -> id("tab_id")?.let { Tab(it, tableContext()) } ?: Unavailable
                "TABLE" -> {
                    val table = id("table_id") ?: return Unavailable
                    val occupancy = id("occupancy_id") ?: return Unavailable
                    val generation = target.opt("generation") as? Int ?: return Unavailable
                    if (generation < 0) Unavailable else Table(table, occupancy, generation)
                }
                else -> Unavailable
            }
        }
    }
}

/** A label or another active occupancy of the same table cannot satisfy this target. */
internal fun StaffTaskTarget.Table.currentTable(tables: List<TableSummary>): TableSummary? =
    tables.firstOrNull { table -> table.id == tableId && table.status == "OCCUPIED" &&
        table.activeOccupancy?.let { it.id == occupancyId && it.generation == generation } == true }

/** Delivery location is optional on a Tab target; never reconstruct it from labels. */
internal fun StaffTaskTarget.currentDeliveryTable(tables: List<TableSummary>): TableSummary? = when (this) {
    is StaffTaskTarget.Table -> currentTable(tables)
    is StaffTaskTarget.Tab -> tableTarget?.currentTable(tables)
    StaffTaskTarget.Unavailable -> null
}
