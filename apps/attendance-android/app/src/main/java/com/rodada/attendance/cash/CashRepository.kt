package com.rodada.attendance.cash

import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession

/**
 * Authenticated access boundary for CashShift. Server capabilities and recent reauthentication
 * remain the source of truth; this repository deliberately performs no local authorization.
 */
/**
 * Small seam used by the native Caixa state holder.  It deliberately mirrors only canonical
 * server commands; it is not a client-side drawer ledger.
 */
interface CashGateway {
    suspend fun cashPoints(session: StoredSession): List<CashPointSnapshot>
    suspend fun activeShift(session: StoredSession, cashPointId: String): CashShiftSnapshot
    suspend fun openShift(session: StoredSession, command: OpenCashShiftCommand): CashShiftSnapshot
    suspend fun shiftDetail(session: StoredSession, shiftId: String): CashShiftDetail
    suspend fun supply(session: StoredSession, shiftId: String, command: CashMovementCommand): CashMovementSnapshot
    suspend fun withdraw(session: StoredSession, shiftId: String, command: CashWithdrawalCommand): CashMovementSnapshot
    suspend fun startCount(session: StoredSession, shiftId: String): CashShiftSnapshot
    suspend fun close(session: StoredSession, shiftId: String, command: CloseCashShiftCommand): CashShiftSnapshot
    suspend fun review(session: StoredSession, shiftId: String, reason: String): CashShiftSnapshot
}

class CashRepository(private val authRepository: AuthRepository) : CashGateway {
    private val client = CashHttpClient(BuildConfig.RODADA_API_BASE_URL)

    override suspend fun cashPoints(session: StoredSession) =
        authRepository.withAuthorizedAccess(session, client::cashPoints)

    override suspend fun activeShift(session: StoredSession, cashPointId: String) =
        authRepository.withAuthorizedAccess(session) { client.activeShift(it, cashPointId) }

    override suspend fun openShift(session: StoredSession, command: OpenCashShiftCommand) =
        authRepository.withAuthorizedAccess(session) { client.openShift(it, command) }

    override suspend fun shiftDetail(session: StoredSession, shiftId: String) =
        authRepository.withAuthorizedAccess(session) { client.shiftDetail(it, shiftId) }

    override suspend fun supply(session: StoredSession, shiftId: String, command: CashMovementCommand) =
        authRepository.withAuthorizedAccess(session) { client.supply(it, shiftId, command) }

    override suspend fun withdraw(session: StoredSession, shiftId: String, command: CashWithdrawalCommand) =
        authRepository.withAuthorizedAccess(session) { client.withdraw(it, shiftId, command) }

    override suspend fun startCount(session: StoredSession, shiftId: String) =
        authRepository.withAuthorizedAccess(session) { client.startCount(it, shiftId) }

    override suspend fun close(session: StoredSession, shiftId: String, command: CloseCashShiftCommand) =
        authRepository.withAuthorizedAccess(session) { client.close(it, shiftId, command) }

    override suspend fun review(session: StoredSession, shiftId: String, reason: String) =
        authRepository.withAuthorizedAccess(session) { client.review(it, shiftId, reason) }

    suspend fun lateCorrection(session: StoredSession, shiftId: String, command: LateCashCorrectionCommand) =
        authRepository.withAuthorizedAccess(session) { client.lateCorrection(it, shiftId, command) }
}
