package com.rodada.attendance.operations

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.rodada.attendance.auth.StoredSession
import org.json.JSONArray
import org.json.JSONObject
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class PendingOrderLine(val productId: String, val quantity: Int)

/**
 * A deliberately closed set of encrypted recovery records. This is not an offline queue:
 * callers must re-read canonical state and retry only their original idempotent command.
 */
class PendingMutationIntentStore(context: Context) {
    private val preferences = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    fun save(intent: RecoveryIntent) {
        val records = loadAll().filterNot { it.id == intent.id } + intent
        write(records)
    }

    fun loadFor(session: StoredSession): List<RecoveryIntent> =
        loadAll().filter { it.staffId == session.staffId && it.venueId == session.venueId && it.deviceId == session.deviceId }

    fun remove(intentId: String) = write(loadAll().filterNot { it.id == intentId })

    private fun write(intents: List<RecoveryIntent>) {
        val payload = JSONArray().apply { intents.forEach { put(it.toJson()) } }.toString()
        preferences.edit().putString(KEY_PAYLOAD, encrypt(payload)).apply()
    }

    private fun loadAll(): List<RecoveryIntent> {
        val payload = preferences.getString(KEY_PAYLOAD, null) ?: return emptyList()
        return try {
            val records = JSONArray(decrypt(payload))
            buildList {
                for (index in 0 until records.length()) RecoveryIntent.fromJson(records.getJSONObject(index))?.let(::add)
            }
        } catch (_: Exception) {
            preferences.edit().remove(KEY_PAYLOAD).apply()
            emptyList()
        }
    }

    private fun encrypt(plaintext: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        return listOf(VERSION, Base64.encodeToString(cipher.iv, Base64.NO_WRAP), Base64.encodeToString(cipher.doFinal(plaintext.toByteArray()), Base64.NO_WRAP)).joinToString(":")
    }

    private fun decrypt(payload: String): String {
        val parts = payload.split(":", limit = 3)
        require(parts.size == 3 && parts[0] == VERSION)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(128, Base64.decode(parts[1], Base64.NO_WRAP)))
        return cipher.doFinal(Base64.decode(parts[2], Base64.NO_WRAP)).toString(Charsets.UTF_8)
    }

    private fun getOrCreateKey(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setRandomizedEncryptionRequired(true)
                .build())
        }.generateKey()
    }

    private companion object {
        const val PREFERENCES = "rodada_pending_mutation_intents"
        const val KEY_PAYLOAD = "encrypted_intents"
        const val KEY_ALIAS = "rodada_pending_mutation_intents_v1"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val VERSION = "v1"
    }
}

enum class RecoveryState { PENDING, CHECKING, CONFIRMED, SAFE_TO_RETRY, ACTION_REQUIRED }

sealed interface RecoveryIntent {
    val id: String
    val staffId: String
    val venueId: String
    val deviceId: String
    val idempotencyKey: String
    val createdAtMillis: Long
    val state: RecoveryState
    fun toJson(): JSONObject

    data class ConfirmOrder(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val tabId: String,
        val lines: List<PendingOrderLine>,
    ) : RecoveryIntent {
        override fun toJson() = baseJson("CONFIRM_ORDER").put("tab_id", tabId).put("lines", JSONArray().apply { lines.forEach { put(JSONObject().put("product_id", it.productId).put("quantity", it.quantity)) } })
    }

    data class StartPayment(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val tabId: String,
        val amountCents: Long,
        val method: PaymentMethod,
        val cashPointId: String?,
    ) : RecoveryIntent {
        override fun toJson() = baseJson("START_PAYMENT").put("tab_id", tabId).put("amount_cents", amountCents).put("method", method.name).apply { if (cashPointId != null) put("cash_point_id", cashPointId) }
    }

    fun baseJson(type: String) = JSONObject().put("type", type).put("id", id).put("staff_id", staffId).put("venue_id", venueId).put("device_id", deviceId).put("idempotency_key", idempotencyKey).put("created_at_millis", createdAtMillis).put("state", state.name)

    companion object {
        fun fromJson(json: JSONObject): RecoveryIntent? = try {
            val common = { state: RecoveryState -> arrayOf(json.getString("id"), json.getString("staff_id"), json.getString("venue_id"), json.getString("device_id"), json.getString("idempotency_key"), json.getLong("created_at_millis"), state) }
            when (json.getString("type")) {
                "CONFIRM_ORDER" -> {
                    val values = common(RecoveryState.valueOf(json.getString("state")))
                    val lines = json.getJSONArray("lines")
                    ConfirmOrder(values[0] as String, values[1] as String, values[2] as String, values[3] as String, values[4] as String, values[5] as Long, values[6] as RecoveryState, json.getString("tab_id"), List(lines.length()) { index -> lines.getJSONObject(index).let { PendingOrderLine(it.getString("product_id"), it.getInt("quantity")) } })
                }
                "START_PAYMENT" -> {
                    val values = common(RecoveryState.valueOf(json.getString("state")))
                    StartPayment(values[0] as String, values[1] as String, values[2] as String, values[3] as String, values[4] as String, values[5] as Long, values[6] as RecoveryState, json.getString("tab_id"), json.getLong("amount_cents"), PaymentMethod.valueOf(json.getString("method")), json.optString("cash_point_id").ifBlank { null })
                }
                else -> null
            }
        } catch (_: Exception) { null }
    }
}
