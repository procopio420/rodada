package com.rodada.attendance.operations

import com.rodada.attendance.auth.StoredSession

/**
 * Only staff-originated, idempotent order confirmations are eligible for foreground
 * replay. This is deliberately NOT a payment/refund/cash/fulfillment offline queue.
 *
 * CHECKING is replayable: a timeout or process kill may occur after the API commits.
 * The original idempotency key and original exact payload must be retained.
 */
internal object OrderRecoveryPolicy {
    fun awaitingReconciliation(intents: List<RecoveryIntent>): List<RecoveryIntent.ConfirmOrder> =
        intents.filterIsInstance<RecoveryIntent.ConfirmOrder>()
            .filter { it.state in setOf(RecoveryState.PENDING, RecoveryState.CHECKING, RecoveryState.SAFE_TO_RETRY) }
            .sortedWith(compareBy<RecoveryIntent.ConfirmOrder> { it.createdAtMillis }.thenBy { it.id })

    fun displayQueue(intents: List<RecoveryIntent>): List<RecoveryIntent.ConfirmOrder> =
        intents.filterIsInstance<RecoveryIntent.ConfirmOrder>()
            .filter { it.state != RecoveryState.CONFIRMED }
            .sortedWith(compareBy<RecoveryIntent.ConfirmOrder> { it.createdAtMillis }.thenBy { it.id })

    fun canReplay(intent: RecoveryIntent.ConfirmOrder, envelope: SessionBoundRecoveryIntent, session: StoredSession): Boolean =
        envelope.canReplay(session) && envelope.intent == intent &&
            intent.lines.isNotEmpty() && intent.lines.all { it.productId.isNotBlank() && it.quantity > 0 } &&
            intent.idempotencyKey.isNotBlank() && intent.tabId.isNotBlank() &&
            intent.state in setOf(RecoveryState.PENDING, RecoveryState.CHECKING, RecoveryState.SAFE_TO_RETRY)

    fun nextForTab(intents: List<RecoveryIntent>, tabId: String): RecoveryIntent.ConfirmOrder? =
        displayQueue(intents).firstOrNull { it.tabId == tabId }

    fun stateLabel(state: RecoveryState): String = when (state) {
        RecoveryState.PENDING -> "AGUARDANDO CONEXÃO"
        RecoveryState.CHECKING -> "VERIFICANDO NO SERVIDOR"
        RecoveryState.SAFE_TO_RETRY -> "RECONCILIAÇÃO PENDENTE"
        RecoveryState.ACTION_REQUIRED -> "EXIGE REVISÃO"
        RecoveryState.FAILED_TERMINAL -> "REVISÃO NECESSÁRIA"
        RecoveryState.CONFIRMED -> "CONFIRMADO"
    }
}
