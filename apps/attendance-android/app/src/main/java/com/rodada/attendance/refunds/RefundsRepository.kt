package com.rodada.attendance.refunds

import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession

class RefundsRepository(private val authRepository: AuthRepository) {
    private val client = RefundsHttpClient(BuildConfig.RODADA_API_BASE_URL)

    suspend fun create(session: StoredSession, command: RefundCommand): RefundResult =
        authRepository.withAuthorizedAccess(session) { client.create(it, command) }
}
