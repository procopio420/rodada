package com.rodada.attendance.cash

import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession

/**
 * Authenticated access boundary for CashShift. Server capabilities and recent reauthentication
 * remain the source of truth; this repository deliberately performs no local authorization.
 */
class CashRepository(private val authRepository: AuthRepository) {
    private val client = CashHttpClient(BuildConfig.RODADA_API_BASE_URL)

    suspend fun cashPoints(session: StoredSession) =
        authRepository.withAuthorizedAccess(session, client::cashPoints)

    suspend fun activeShift(session: StoredSession, cashPointId: String) =
        authRepository.withAuthorizedAccess(session) { client.activeShift(it, cashPointId) }

    suspend fun openShift(session: StoredSession, command: OpenCashShiftCommand) =
        authRepository.withAuthorizedAccess(session) { client.openShift(it, command) }

    suspend fun shiftDetail(session: StoredSession, shiftId: String) =
        authRepository.withAuthorizedAccess(session) { client.shiftDetail(it, shiftId) }

    suspend fun supply(session: StoredSession, shiftId: String, command: CashMovementCommand) =
        authRepository.withAuthorizedAccess(session) { client.supply(it, shiftId, command) }

    suspend fun withdraw(session: StoredSession, shiftId: String, command: CashWithdrawalCommand) =
        authRepository.withAuthorizedAccess(session) { client.withdraw(it, shiftId, command) }

    suspend fun startCount(session: StoredSession, shiftId: String) =
        authRepository.withAuthorizedAccess(session) { client.startCount(it, shiftId) }

    suspend fun close(session: StoredSession, shiftId: String, command: CloseCashShiftCommand) =
        authRepository.withAuthorizedAccess(session) { client.close(it, shiftId, command) }

    suspend fun review(session: StoredSession, shiftId: String, reason: String) =
        authRepository.withAuthorizedAccess(session) { client.review(it, shiftId, reason) }

    suspend fun lateCorrection(session: StoredSession, shiftId: String, command: LateCashCorrectionCommand) =
        authRepository.withAuthorizedAccess(session) { client.lateCorrection(it, shiftId, command) }
}
