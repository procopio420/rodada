package com.rodada.attendance.auth

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureSessionStore(context: Context) {
    private val preferences =
        context.getSharedPreferences("rodada_secure_session", Context.MODE_PRIVATE)

    fun save(session: StoredSession) {
        val json =
            JSONObject()
                .put("access_token", session.tokens.accessToken)
                .put("access_expires_at", session.tokens.accessExpiresAt)
                .put("refresh_token", session.tokens.refreshToken)
                .put("refresh_expires_at", session.tokens.refreshExpiresAt)
                .put("session_id", session.sessionId)
                .put("staff_id", session.staffId)
                .put("staff_display_name", session.staffDisplayName)
                .put("venue_id", session.venueId)
                .put("venue_slug", session.venueSlug)
                .put("venue_name", session.venueName)
                .put("role", session.role)
                .put("device_id", session.deviceId)
                .put("device_trust_state", session.deviceTrustState)
                .put("capabilities", JSONArray(session.capabilities.toList()))
                .toString()

        preferences.edit().putString(KEY_PAYLOAD, encrypt(json)).apply()
    }

    fun load(): StoredSession? {
        val payload = preferences.getString(KEY_PAYLOAD, null) ?: return null
        return try {
            val json = JSONObject(decrypt(payload))
            StoredSession(
                tokens =
                    AuthTokens(
                        accessToken = json.getString("access_token"),
                        accessExpiresAt = json.getString("access_expires_at"),
                        refreshToken = json.getString("refresh_token"),
                        refreshExpiresAt = json.getString("refresh_expires_at"),
                    ),
                sessionId = json.optString("session_id"),
                staffId = json.getString("staff_id"),
                staffDisplayName = json.getString("staff_display_name"),
                venueId = json.getString("venue_id"),
                venueSlug = json.getString("venue_slug"),
                venueName = json.getString("venue_name"),
                role = json.getString("role"),
                deviceId = json.getString("device_id"),
                deviceTrustState = json.getString("device_trust_state"),
                capabilities = json.optJSONArray("capabilities")?.let { capabilities ->
                    buildSet { for (index in 0 until capabilities.length()) add(capabilities.getString(index)) }
                }.orEmpty(),
            )
        } catch (_: Exception) {
            clear()
            null
        }
    }

    fun clear() {
        preferences.edit().remove(KEY_PAYLOAD).apply()
    }

    private fun encrypt(plaintext: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val ciphertext = cipher.doFinal(plaintext.toByteArray(Charsets.UTF_8))
        return listOf(
            VERSION,
            Base64.encodeToString(cipher.iv, Base64.NO_WRAP),
            Base64.encodeToString(ciphertext, Base64.NO_WRAP),
        ).joinToString(":")
    }

    private fun decrypt(payload: String): String {
        val parts = payload.split(":", limit = 3)
        require(parts.size == 3 && parts[0] == VERSION)

        val cipher = Cipher.getInstance(TRANSFORMATION)
        val iv = Base64.decode(parts[1], Base64.NO_WRAP)
        val ciphertext = Base64.decode(parts[2], Base64.NO_WRAP)
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(128, iv))
        return cipher.doFinal(ciphertext).toString(Charsets.UTF_8)
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = keyStore.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing

        val generator =
            KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                ANDROID_KEYSTORE,
            )
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .setRandomizedEncryptionRequired(true)
                .build(),
        )
        return generator.generateKey()
    }

    private companion object {
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "rodada_staff_session_v1"
        const val KEY_PAYLOAD = "encrypted_session"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val VERSION = "v1"
    }
}
