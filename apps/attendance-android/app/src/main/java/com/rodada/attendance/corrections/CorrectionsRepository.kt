package com.rodada.attendance.corrections

import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession

/** Auth refresh/revocation stays centralized in AuthRepository for correction commands too. */
class CorrectionsRepository(private val authRepository: AuthRepository) {
    private val client = CorrectionsHttpClient(BuildConfig.RODADA_API_BASE_URL)

    suspend fun submit(session: StoredSession, command: CorrectionCommand): CorrectionResult =
        authRepository.withAuthorizedAccess(session) { client.submit(it, command) }
}
