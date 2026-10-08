package com.rodada.attendance.operations

import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession

class OperationsRepository(private val authRepository: AuthRepository) {
    private val client = OperationsHttpClient(BuildConfig.RODADA_API_BASE_URL)

    suspend fun tabs(session: StoredSession) = authRepository.withAuthorizedAccess(session, client::tabs)

    suspend fun openTab(session: StoredSession, label: String) =
        authRepository.withAuthorizedAccess(session) { client.openTab(it, label) }

    suspend fun tabDetail(session: StoredSession, tabId: String) =
        authRepository.withAuthorizedAccess(session) { client.tabDetail(it, tabId) }

    suspend fun products(session: StoredSession) = authRepository.withAuthorizedAccess(session, client::products)

    suspend fun deliveryTasks(session: StoredSession) = authRepository.withAuthorizedAccess(session, client::deliveryTasks)

    suspend fun completeDelivery(session: StoredSession, taskId: String) =
        authRepository.withAuthorizedAccess(session) { client.completeDelivery(it, taskId) }

    suspend fun confirmOrder(
        session: StoredSession,
        tabId: String,
        lines: List<CartLine>,
        intentId: String,
    ) = authRepository.withAuthorizedAccess(session) { client.confirmOrder(it, tabId, lines, intentId) }

    suspend fun collectPayment(
        session: StoredSession,
        tabId: String,
        amountCents: Long,
        method: PaymentMethod,
        idempotencyKey: String,
    ) = authRepository.withAuthorizedAccess(session) {
        client.collectPayment(it, tabId, amountCents, method, idempotencyKey)
    }

    suspend fun closeTab(session: StoredSession, tabId: String) =
        authRepository.withAuthorizedAccess(session) { client.closeTab(it, tabId) }
}
