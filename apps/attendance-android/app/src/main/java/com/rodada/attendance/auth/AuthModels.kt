package com.rodada.attendance.auth

data class AuthTokens(
    val accessToken: String,
    val accessExpiresAt: String,
    val refreshToken: String,
    val refreshExpiresAt: String,
)

data class StoredSession(
    val tokens: AuthTokens,
    val staffId: String,
    val staffDisplayName: String,
    val venueId: String,
    val venueSlug: String,
    val venueName: String,
    val role: String,
    val deviceId: String,
    val deviceTrustState: String,
) {
    fun withTokens(next: AuthTokens): StoredSession = copy(tokens = next)
}

data class LoginRequest(
    val venueSlug: String,
    val loginIdentifier: String,
    val pin: String,
    val installationId: String,
    val platform: String = "ANDROID",
    val friendlyLabel: String = "Rodada Atendimento",
)

data class MeSnapshot(
    val staffId: String,
    val staffDisplayName: String,
    val venueId: String,
    val venueSlug: String,
    val venueName: String,
    val role: String,
    val deviceTrustState: String,
)

data class ReauthReceipt(
    val reauthenticatedAt: String,
    val validUntil: String,
)

class AuthApiException(
    val status: Int,
    val code: String,
    override val message: String,
) : Exception(message)

data class AuthUiState(
    val loading: Boolean = true,
    val session: StoredSession? = null,
    val errorMessage: String? = null,
    val reauthValidUntil: String? = null,
)


data class AccessInvalidationEvent(
    val id: Long,
    val eventType: String,
)

data class AccessInvalidationFeed(
    val cursor: Long,
    val results: List<AccessInvalidationEvent>,
)

data class InvalidationPollResult(
    val session: StoredSession,
    val cursor: Long,
    val changed: Boolean,
)
