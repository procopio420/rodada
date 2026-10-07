package com.rodada.attendance.auth

import android.content.Context
import com.rodada.attendance.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AuthRepository(context: Context) {
    private val appContext = context.applicationContext
    private val secureStore = SecureSessionStore(appContext)
    private val installationIdStore = InstallationIdStore(appContext)
    private val client = AuthHttpClient(BuildConfig.RODADA_API_BASE_URL)

    suspend fun restoreSession(): StoredSession? =
        withContext(Dispatchers.IO) {
            val stored = secureStore.load() ?: return@withContext null

            try {
                val me = client.me(stored.tokens.accessToken)
                val updated = stored.merge(me)
                secureStore.save(updated)
                updated
            } catch (error: AuthApiException) {
                if (error.code != "ACCESS_TOKEN_EXPIRED") {
                    if (error.status == 401 || error.status == 403) secureStore.clear()
                    throw error
                }

                val refreshed = refreshStoredSession(stored)
                val me = client.me(refreshed.tokens.accessToken)
                val updated = refreshed.merge(me)
                secureStore.save(updated)
                updated
            }
        }

    suspend fun login(
        venueSlug: String,
        loginIdentifier: String,
        pin: String,
    ): StoredSession =
        withContext(Dispatchers.IO) {
            val session =
                client.login(
                    LoginRequest(
                        venueSlug = venueSlug,
                        loginIdentifier = loginIdentifier,
                        pin = pin,
                        installationId = installationIdStore.getOrCreate(),
                    ),
                )
            secureStore.save(session)
            session
        }

    suspend fun switchOperator(
        current: StoredSession,
        loginIdentifier: String,
        pin: String,
    ): StoredSession =
        withContext(Dispatchers.IO) {
            val next =
                withAccessRefresh(current) { accessToken ->
                    client.switchOperator(accessToken, loginIdentifier, pin)
                }
            val latest = secureStore.load() ?: current
            val hydrated =
                if (next.venueId.isBlank()) {
                    next.copy(
                        venueId = latest.venueId,
                        venueSlug = latest.venueSlug,
                        venueName = latest.venueName,
                    )
                } else {
                    next
                }
            secureStore.save(hydrated)
            hydrated
        }

    suspend fun reauthenticate(current: StoredSession, pin: String): ReauthReceipt =
        withContext(Dispatchers.IO) {
            withAccessRefresh(current) { accessToken ->
                client.reauthenticate(accessToken, pin)
            }
        }

    suspend fun lock(current: StoredSession) =
        withContext(Dispatchers.IO) {
            try {
                withAccessRefresh(current) { accessToken ->
                    client.lock(accessToken)
                }
            } finally {
                secureStore.clear()
            }
        }

    suspend fun logout(current: StoredSession) =
        withContext(Dispatchers.IO) {
            try {
                withAccessRefresh(current) { accessToken ->
                    client.logout(accessToken)
                }
            } finally {
                secureStore.clear()
            }
        }

    fun clearLocalSession() {
        secureStore.clear()
    }

    private fun refreshStoredSession(session: StoredSession): StoredSession {
        val nextTokens =
            try {
                client.refresh(session.tokens.refreshToken)
            } catch (error: AuthApiException) {
                if (error.status == 401 || error.status == 403) secureStore.clear()
                throw error
            }
        return session.withTokens(nextTokens).also(secureStore::save)
    }

    private fun <T> withAccessRefresh(
        fallback: StoredSession,
        action: (String) -> T,
    ): T {
        var current = secureStore.load() ?: fallback
        return try {
            action(current.tokens.accessToken)
        } catch (error: AuthApiException) {
            if (error.code != "ACCESS_TOKEN_EXPIRED") throw error
            current = refreshStoredSession(current)
            action(current.tokens.accessToken)
        }
    }

    private fun StoredSession.merge(me: MeSnapshot): StoredSession =
        copy(
            staffId = me.staffId,
            staffDisplayName = me.staffDisplayName,
            venueId = me.venueId,
            venueSlug = me.venueSlug,
            venueName = me.venueName,
            role = me.role,
            deviceTrustState = me.deviceTrustState.ifBlank { deviceTrustState },
        )
}
