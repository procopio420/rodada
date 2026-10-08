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

enum class RecoveryState { PENDING, CHECKING, CONFIRMED, SAFE_TO_RETRY, ACTION_REQUIRED, FAILED_TERMINAL }

/**
 * These enums describe the command captured by the app, not client-side policy. The
 * server remains authoritative when a recovered command is checked or retried.
 */
enum class CorrectionRecoveryAction { CANCEL, REMAKE, REPLACEMENT }

enum class RefundRecoveryKind { DIRECT, SETTLE_CORRECTION }

enum class CashMovementRecoveryKind { SUPPLY, WITHDRAWAL, LATE_CORRECTION }

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

    /**
     * Fields are sufficient to rebuild the original correction request with its original
     * idempotency key. They deliberately contain no approval or authentication material.
     */
    data class Correction(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val orderItemId: String,
        val itemState: String,
        val action: CorrectionRecoveryAction,
        val reasonCode: String,
        val reasonText: String?,
        val replacementProductId: String?,
    ) : RecoveryIntent {
        override fun toJson() =
            baseJson("CORRECTION")
                .put("order_item_id", orderItemId)
                .put("item_state", itemState)
                .put("action", action.name)
                .put("reason_code", reasonCode)
                .apply { if (reasonText != null) put("reason_text", reasonText) }
                .apply { if (replacementProductId != null) put("replacement_product_id", replacementProductId) }
    }

    /** A refund is recovered by checking the original payment/correction, never by creating a new key. */
    data class Refund(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val kind: RefundRecoveryKind,
        val paymentId: String,
        val correctionId: String?,
        val amountCents: Long,
        val reason: String?,
        val cashPointId: String?,
    ) : RecoveryIntent {
        override fun toJson() =
            baseJson("REFUND")
                .put("kind", kind.name)
                .put("payment_id", paymentId)
                .put("amount_cents", amountCents)
                .apply { if (correctionId != null) put("correction_id", correctionId) }
                .apply { if (reason != null) put("reason", reason) }
                .apply { if (cashPointId != null) put("cash_point_id", cashPointId) }
    }

    /**
     * A movement is retried only against the recorded shift. Current cash authority,
     * opening state and permissions are revalidated by the API at recovery time.
     */
    data class CashMovement(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val shiftId: String,
        val kind: CashMovementRecoveryKind,
        val amountCents: Long,
        val reason: String,
        val allowNegativeExpected: Boolean,
        val correctionOfId: String?,
    ) : RecoveryIntent {
        override fun toJson() =
            baseJson("CASH_MOVEMENT")
                .put("shift_id", shiftId)
                .put("kind", kind.name)
                .put("amount_cents", amountCents)
                .put("reason", reason)
                .put("allow_negative_expected", allowNegativeExpected)
                .apply { if (correctionOfId != null) put("correction_of_id", correctionOfId) }
    }

    /** Close has no provider-style client idempotency key; the snapshot/version pins recovery to one count. */
    data class CashClose(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val shiftId: String,
        val countedAmountCents: Long,
        val reviewThresholdCents: Long,
        val expectedVersion: Long?,
    ) : RecoveryIntent {
        override fun toJson() =
            baseJson("CASH_CLOSE")
                .put("shift_id", shiftId)
                .put("counted_amount_cents", countedAmountCents)
                .put("review_threshold_cents", reviewThresholdCents)
                .apply { if (expectedVersion != null) put("expected_version", expectedVersion) }
    }

    /**
     * Dispatch completion is server-idempotent by task state. The local key keeps the
     * recovery record stable while the app re-reads the canonical task outcome.
     */
    data class CompleteDelivery(
        override val id: String,
        override val staffId: String,
        override val venueId: String,
        override val deviceId: String,
        override val idempotencyKey: String,
        override val createdAtMillis: Long,
        override val state: RecoveryState,
        val deliveryTaskId: String,
    ) : RecoveryIntent {
        override fun toJson() = baseJson("COMPLETE_DELIVERY").put("delivery_task_id", deliveryTaskId)
    }

    fun baseJson(type: String) = JSONObject().put("type", type).put("id", id).put("staff_id", staffId).put("venue_id", venueId).put("device_id", deviceId).put("idempotency_key", idempotencyKey).put("created_at_millis", createdAtMillis).put("state", state.name)

    companion object {
        fun fromJson(json: JSONObject): RecoveryIntent? = try {
            val common = RecoveryIntentCommon(
                id = json.getString("id"),
                staffId = json.getString("staff_id"),
                venueId = json.getString("venue_id"),
                deviceId = json.getString("device_id"),
                idempotencyKey = json.getString("idempotency_key"),
                createdAtMillis = json.getLong("created_at_millis"),
                state = RecoveryState.valueOf(json.getString("state")),
            )
            when (json.getString("type")) {
                "CONFIRM_ORDER" -> {
                    val lines = json.getJSONArray("lines")
                    ConfirmOrder(common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state, json.getString("tab_id"), List(lines.length()) { index -> lines.getJSONObject(index).let { PendingOrderLine(it.getString("product_id"), it.getInt("quantity")) } })
                }
                "START_PAYMENT" -> {
                    StartPayment(common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state, json.getString("tab_id"), json.getLong("amount_cents"), PaymentMethod.valueOf(json.getString("method")), json.optString("cash_point_id").ifBlank { null })
                }
                "CORRECTION" -> Correction(
                    common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state,
                    json.getString("order_item_id"), json.getString("item_state"), CorrectionRecoveryAction.valueOf(json.getString("action")),
                    json.getString("reason_code"), json.optString("reason_text").ifBlank { null }, json.optString("replacement_product_id").ifBlank { null },
                )
                "REFUND" -> Refund(
                    common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state,
                    RefundRecoveryKind.valueOf(json.getString("kind")), json.getString("payment_id"), json.optString("correction_id").ifBlank { null },
                    json.getLong("amount_cents"), json.optString("reason").ifBlank { null }, json.optString("cash_point_id").ifBlank { null },
                )
                "CASH_MOVEMENT" -> CashMovement(
                    common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state,
                    json.getString("shift_id"), CashMovementRecoveryKind.valueOf(json.getString("kind")), json.getLong("amount_cents"),
                    json.getString("reason"), json.optBoolean("allow_negative_expected"), json.optString("correction_of_id").ifBlank { null },
                )
                "CASH_CLOSE" -> CashClose(
                    common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state,
                    json.getString("shift_id"), json.getLong("counted_amount_cents"), json.getLong("review_threshold_cents"),
                    if (json.has("expected_version") && !json.isNull("expected_version")) json.getLong("expected_version") else null,
                )
                "COMPLETE_DELIVERY" -> CompleteDelivery(
                    common.id, common.staffId, common.venueId, common.deviceId, common.idempotencyKey, common.createdAtMillis, common.state,
                    json.getString("delivery_task_id"),
                )
                else -> null
            }
        } catch (_: Exception) { null }
    }
}

private data class RecoveryIntentCommon(
    val id: String,
    val staffId: String,
    val venueId: String,
    val deviceId: String,
    val idempotencyKey: String,
    val createdAtMillis: Long,
    val state: RecoveryState,
)
