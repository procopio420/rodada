package com.rodada.attendance.cash

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.operations.CashMovementRecoveryKind
import com.rodada.attendance.operations.PendingMutationIntentStore
import com.rodada.attendance.operations.RecoveryIntent
import com.rodada.attendance.operations.RecoveryState
import kotlinx.coroutines.launch
import java.io.IOException
import java.time.LocalDate
import java.util.UUID

data class CashShiftUiState(
    val loading: Boolean = false,
    val submitting: Boolean = false,
    val cashPoints: List<CashPointSnapshot> = emptyList(),
    val selectedCashPointId: String? = null,
    val detail: CashShiftDetail? = null,
    val errorMessage: String? = null,
    val noticeMessage: String? = null,
) {
    val selectedCashPoint: CashPointSnapshot?
        get() = cashPoints.firstOrNull { it.id == selectedCashPointId }
    val activeShift: CashShiftSnapshot?
        get() = detail?.shift ?: selectedCashPoint?.activeShift ?: selectedCashPoint?.pendingReviewShift
}

/**
 * Server-backed state holder for the Caixa operator surface.  Amounts remain integral cents;
 * expected and discrepancy are rendered from canonical snapshots and are never recomputed here.
 */
class CashShiftViewModel(
    private val gateway: CashGateway,
    private val authRepository: AuthRepository,
    private val pendingMutationIntentStore: PendingMutationIntentStore,
) : ViewModel() {
    var state by mutableStateOf(CashShiftUiState())
        private set

    private var loadedSessionKey: String? = null

    fun ensureLoaded(session: StoredSession) {
        val key = "${session.staffId}:${session.venueId}"
        if (loadedSessionKey == key && (state.cashPoints.isNotEmpty() || state.loading)) return
        if (loadedSessionKey != null && loadedSessionKey != key) state = CashShiftUiState()
        loadedSessionKey = key
        refresh(session)
    }

    fun refresh(session: StoredSession) {
        state = state.copy(loading = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                val points = gateway.cashPoints(session)
                val selectedId = state.selectedCashPointId.takeIf { id -> points.any { it.id == id } }
                    ?: points.firstOrNull { it.activeShift != null }?.id
                    ?: points.firstOrNull()?.id
                val detail = points.firstOrNull { it.id == selectedId }
                    ?.let { point -> point.activeShift ?: point.pendingReviewShift }
                    ?.id
                    ?.let { gateway.shiftDetail(session, it) }
                LoadedCash(points, selectedId, detail)
            }.onSuccess { loaded ->
                state = state.copy(
                    loading = false,
                    cashPoints = loaded.points,
                    selectedCashPointId = loaded.selectedId,
                    detail = loaded.detail,
                )
            }.onFailure { fail(it) }
        }
    }

    fun selectCashPoint(session: StoredSession, cashPointId: String) {
        if (state.submitting || state.selectedCashPointId == cashPointId) return
        state = state.copy(selectedCashPointId = cashPointId, detail = null, loading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                val point = state.cashPoints.firstOrNull { it.id == cashPointId }
                point?.let { it.activeShift ?: it.pendingReviewShift }?.id?.let { gateway.shiftDetail(session, it) }
            }.onSuccess { detail -> state = state.copy(loading = false, detail = detail) }
                .onFailure { fail(it) }
        }
    }

    fun openShift(session: StoredSession, openingFloatCents: Long) {
        val point = state.selectedCashPoint ?: return
        if (openingFloatCents < 0) {
            state = state.copy(errorMessage = "O fundo inicial não pode ser negativo.")
            return
        }
        action {
            gateway.openShift(
                session,
                OpenCashShiftCommand(point.id, openingFloatCents, LocalDate.now().toString(), UUID.randomUUID().toString()),
            )
            reloadSelected(session, "Caixa aberto.")
        }
    }

    fun supply(session: StoredSession, amountCents: Long, reason: String) {
        if (amountCents <= 0) return invalidAmount()
        withActiveShift(session) { shift ->
            val key = UUID.randomUUID().toString()
            val intent = cashMovementIntent(session, shift.id, key, CashMovementRecoveryKind.SUPPLY, amountCents, reason)
            pendingMutationIntentStore.save(intent, session)
            gateway.supply(session, shift.id, CashMovementCommand(amountCents, reason.trim(), key))
            pendingMutationIntentStore.remove(intent.id)
            reloadSelected(session, "Suprimento registrado.")
        }
    }

    fun withdraw(session: StoredSession, amountCents: Long, reason: String) {
        if (amountCents <= 0) return invalidAmount()
        withActiveShift(session) { shift ->
            val key = UUID.randomUUID().toString()
            val intent = cashMovementIntent(session, shift.id, key, CashMovementRecoveryKind.WITHDRAWAL, amountCents, reason)
            pendingMutationIntentStore.save(intent, session)
            gateway.withdraw(session, shift.id, CashWithdrawalCommand(amountCents, reason.trim(), key))
            pendingMutationIntentStore.remove(intent.id)
            reloadSelected(session, "Sangria registrada.")
        }
    }

    fun startCount(session: StoredSession) = withActiveShift(session) { shift ->
        gateway.startCount(session, shift.id)
        reloadSelected(session, "Contagem iniciada. Informe o valor contado sem consultar o esperado.")
    }

    fun close(session: StoredSession, countedAmountCents: Long, reviewThresholdCents: Long = 0L) {
        if (countedAmountCents < 0) {
            state = state.copy(errorMessage = "O valor contado não pode ser negativo.")
            return
        }
        withActiveShift(session) { shift ->
            val key = UUID.randomUUID().toString()
            val intent = RecoveryIntent.CashClose(
                key, session.staffId, session.venueId, session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING,
                shift.id, countedAmountCents, reviewThresholdCents, shift.version,
            )
            pendingMutationIntentStore.save(intent, session)
            gateway.close(
                session,
                shift.id,
                CloseCashShiftCommand(countedAmountCents, reviewThresholdCents, shift.version),
            )
            pendingMutationIntentStore.remove(intent.id)
            reloadSelected(session, "Fechamento enviado para conferência.")
        }
    }

    fun review(session: StoredSession, reason: String, reauthPin: String) = withActiveShift(session) { shift ->
        authRepository.reauthenticate(session, reauthPin)
        gateway.review(session, shift.id, reason.trim())
        reloadSelected(session, "Divergência revisada.")
    }

    fun dismissMessage() {
        state = state.copy(errorMessage = null, noticeMessage = null)
    }

    private fun withActiveShift(session: StoredSession, block: suspend (CashShiftSnapshot) -> Unit) {
        val shift = state.activeShift ?: run {
            state = state.copy(errorMessage = "Abra um caixa antes de registrar esta operação.")
            return
        }
        action { block(shift) }
    }

    private suspend fun reloadSelected(session: StoredSession, notice: String) {
        val points = gateway.cashPoints(session)
        val id = state.selectedCashPointId
        val detail = points.firstOrNull { it.id == id }
            ?.let { point -> point.activeShift ?: point.pendingReviewShift }
            ?.id
            ?.let { gateway.shiftDetail(session, it) }
        state = state.copy(cashPoints = points, detail = detail, noticeMessage = notice)
    }

    private fun action(block: suspend () -> Unit) {
        if (state.submitting) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching { block() }
                .onSuccess { state = state.copy(submitting = false) }
                .onFailure { fail(it) }
        }
    }

    private fun invalidAmount() {
        state = state.copy(errorMessage = "Informe um valor maior que zero.")
    }

    private fun fail(error: Throwable) {
        val message = when (error) {
            is CashApiException -> "${error.code}: ${error.message}"
            is AuthApiException -> "${error.code}: ${error.message}"
            is IOException -> "Sem conexão com o Rodada. O caixa não foi alterado localmente."
            else -> error.message ?: "Falha inesperada no caixa."
        }
        state = state.copy(loading = false, submitting = false, errorMessage = message)
    }

    companion object {
        fun factory(
            gateway: CashGateway,
            authRepository: AuthRepository,
            pendingMutationIntentStore: PendingMutationIntentStore,
        ): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = CashShiftViewModel(gateway, authRepository, pendingMutationIntentStore) as T
        }
    }

    private data class LoadedCash(
        val points: List<CashPointSnapshot>,
        val selectedId: String?,
        val detail: CashShiftDetail?,
    )

    private fun cashMovementIntent(
        session: StoredSession,
        shiftId: String,
        key: String,
        kind: CashMovementRecoveryKind,
        amountCents: Long,
        reason: String,
    ) = RecoveryIntent.CashMovement(
        key, session.staffId, session.venueId, session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING,
        shiftId, kind, amountCents, reason.trim(), false, null,
    )
}
