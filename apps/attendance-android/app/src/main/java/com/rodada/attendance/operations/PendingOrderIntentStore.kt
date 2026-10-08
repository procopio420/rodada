package com.rodada.attendance.operations

import android.content.Context
import com.rodada.attendance.auth.StoredSession
import org.json.JSONArray
import org.json.JSONObject

/**
 * A deliberately narrow recovery record for an order whose server result is unknown.
 *
 * It contains no money or credential data.  The original idempotency key is retained so a
 * resumed request can only reconcile the original canonical Order; it must never become a
 * general offline command queue.
 */
class PendingOrderIntentStore(context: Context) {
    private val preferences = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    fun save(session: StoredSession, intent: PendingOrderIntent) {
        val lines = JSONArray()
        intent.lines.forEach { line ->
            lines.put(JSONObject().put("product_id", line.productId).put("quantity", line.quantity))
        }
        val payload =
            JSONObject()
                .put("staff_id", session.staffId)
                .put("venue_id", session.venueId)
                .put("tab_id", intent.tabId)
                .put("idempotency_key", intent.idempotencyKey)
                .put("lines", lines)
                .toString()
        preferences.edit().putString(KEY_PENDING_ORDER, payload).apply()
    }

    fun load(session: StoredSession): PendingOrderIntent? {
        val payload = preferences.getString(KEY_PENDING_ORDER, null) ?: return null
        return try {
            val json = JSONObject(payload)
            if (json.getString("staff_id") != session.staffId || json.getString("venue_id") != session.venueId) {
                // A command belongs to the original operator.  A switch must not replay it.
                clear()
                return null
            }
            val lines = json.getJSONArray("lines")
            PendingOrderIntent(
                tabId = json.getString("tab_id"),
                idempotencyKey = json.getString("idempotency_key"),
                lines = List(lines.length()) { index ->
                    val line = lines.getJSONObject(index)
                    PendingOrderLine(productId = line.getString("product_id"), quantity = line.getInt("quantity"))
                },
            )
        } catch (_: Exception) {
            clear()
            null
        }
    }

    fun clear() {
        preferences.edit().remove(KEY_PENDING_ORDER).apply()
    }

    private companion object {
        const val PREFERENCES = "rodada_pending_order_intent"
        const val KEY_PENDING_ORDER = "pending_order"
    }
}

data class PendingOrderIntent(
    val tabId: String,
    val idempotencyKey: String,
    val lines: List<PendingOrderLine>,
)

data class PendingOrderLine(val productId: String, val quantity: Int)
