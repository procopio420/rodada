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
                if (error.status != 401) {
                    if (error.status == 403) secureStore.clear()
                    throw error
                }

                val nextTokens =
                    try {
                        client.refresh(stored.tokens.refreshToken)
                    } catch (refreshError: AuthApiException) {
                        if (refreshError.status == 401 || refreshError.status == 403) {
                            secureStore.clear()
                        }
                        throw refreshError
                    }

                val refreshed = stored.withTokens(nextTokens)
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
            val next = client.switchOperator(current.tokens.accessToken, loginIdentifier, pin)
            val hydrated =
                if (next.venueId.isBlank()) {
                    next.copy(
                        venueId = current.venueId,
                        venueSlug = current.venueSlug,
                        venueName = current.venueName,
                    )
                } else {
                    next
                }
            secureStore.save(hydrated)
            hydrated
        }

    suspend fun reauthenticate(current: StoredSession, pin: String): ReauthReceipt =
        withContext(Dispatchers.IO) {
            client.reauthenticate(current.tokens.accessToken, pin)
        }

    suspend fun lock(current: StoredSession) =
        withContext(Dispatchers.IO) {
            try {
                client.lock(current.tokens.accessToken)
            } finally {
                secureStore.clear()
            }
        }

    suspend fun logout(current: StoredSession) =
        withContext(Dispatchers.IO) {
            try {
                client.logout(current.tokens.accessToken)
            } finally {
                secureStore.clear()
            }
        }

    fun clearLocalSession() {
        secureStore.clear()
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
