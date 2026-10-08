package com.rodada.attendance.operations

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.corrections.CorrectionCommand
import com.rodada.attendance.corrections.CorrectionResult
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.corrections.correctionConsequence
import com.rodada.attendance.corrections.requiresPostProductionEndpoint
import com.rodada.attendance.refunds.DirectRefundCommand
import com.rodada.attendance.refunds.RefundCommand
import com.rodada.attendance.refunds.RefundsRepository
import com.rodada.attendance.refunds.SettleCorrectionRefundCommand
import com.rodada.attendance.refunds.refundStatusLabel
import kotlinx.coroutines.launch
import java.io.IOException
import java.util.UUID

data class OperationsUiState(
    val loading: Boolean = false,
    val submitting: Boolean = false,
    val tabs: List<TabSummary> = emptyList(),
    val products: List<Product> = emptyList(),
    val cashPoints: List<CashPoint> = emptyList(),
    val deliveryTasks: List<DeliveryTask> = emptyList(),
    val tables: List<TableSummary> = emptyList(),
    val selectedTab: TabDetail? = null,
    val cart: List<CartLine> = emptyList(),
    val errorMessage: String? = null,
    val noticeMessage: String? = null,
    /** Kept for the complete UI/ViewModel lifecycle and reused by a retry of this cart. */
    val orderIntentId: String? = null,
    val paymentIntentId: String? = null,
    val pendingPayment: RecoveryIntent.StartPayment? = null,
    /** Lets the composable close only the correction sheet that the server accepted. */
    val completedCorrectionItemId: String? = null,
    val connectivity: ConnectivityState = ConnectivityState.RECONNECTING,
    val lastSyncedAtMillis: Long? = null,
)

class OperationsViewModel(
    private val repository: OperationsRepository,
    private val pendingMutationIntentStore: PendingMutationIntentStore,
    private val authRepository: AuthRepository,
    private val correctionsRepository: CorrectionsRepository,
    private val refundsRepository: RefundsRepository,
) : ViewModel() {
    var state by mutableStateOf(OperationsUiState())
        private set

    private var loadedSessionKey: String? = null

    fun ensureLoaded(session: StoredSession) {
        val key = session.staffId + ":" + session.venueId
        if (loadedSessionKey == key && (state.tabs.isNotEmpty() || state.loading)) return
        if (loadedSessionKey != null && loadedSessionKey != key) {
            // Never leave a prior operator's draft cart or Tab context on a shared device.
            state = OperationsUiState()
        }
        loadedSessionKey = key
        refresh(session)
    }

    fun refresh(session: StoredSession) {
        state = state.copy(
            loading = true,
            errorMessage = null,
            noticeMessage = null,
            connectivity = if (state.tabs.isEmpty()) ConnectivityState.RECONNECTING else ConnectivityState.STALE,
        )
        viewModelScope.launch {
            runCatching {
                val tabs = repository.tabs(session)
                val products = repository.products(session)
                val deliveries = repository.deliveryTasks(session)
                val cashPoints = runCatching { repository.cashPoints(session) }.getOrDefault(emptyList())
                val tables = runCatching { repository.tables(session) }.getOrDefault(emptyList())
                val detail = state.selectedTab?.summary?.id?.let { id ->
                    runCatching { repository.tabDetail(session, id) }.getOrNull()
                }
                RefreshSnapshot(tabs, products, cashPoints, deliveries, tables, detail)
            }.onSuccess { snapshot ->
                state = state.copy(
                    loading = false,
                    tabs = snapshot.tabs,
                    products = snapshot.products,
                    cashPoints = snapshot.cashPoints,
                    deliveryTasks = snapshot.deliveryTasks,
                    tables = snapshot.tables,
                    selectedTab = snapshot.detail ?: state.selectedTab,
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                )
            }.onFailure {
                state = state.copy(loading = false)
                showFailure(it)
            }
        }
    }

    fun openTab(session: StoredSession, label: String) = action {
        val opened = repository.openTab(session, label)
        val detail = repository.tabDetail(session, opened.id)
        state = state.copy(
            tabs = listOf(opened) + state.tabs.filterNot { it.id == opened.id },
            selectedTab = detail,
            cart = emptyList(),
            noticeMessage = "Comanda aberta.",
        )
    }

    fun selectTab(session: StoredSession, tabId: String) = action {
        val detail = repository.tabDetail(session, tabId)
        val retained = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.ConfirmOrder>().firstOrNull { it.tabId == tabId }
        val retainedPayment = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.StartPayment>().firstOrNull { it.tabId == tabId }
        val retainedCorrection = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.Correction>().firstOrNull { it.orderItemId in detail.orders.flatMap { order -> order.items }.map { item -> item.id } }
        val retainedRefund = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.Refund>().firstOrNull { refund -> detail.payments.any { it.id == refund.paymentId } }
        val retainedCart = retained?.toCart(state.products).orEmpty()
        state = state.copy(
            selectedTab = detail,
            cart = retainedCart,
            orderIntentId = retained?.idempotencyKey,
            paymentIntentId = retainedPayment?.idempotencyKey,
            pendingPayment = retainedPayment,
            noticeMessage = when {
                retained != null -> "Pedido pendente encontrado. Verifique o resultado antes de adicionar novos itens."
                retainedPayment != null -> "Pagamento pendente encontrado. Não tente cobrar novamente; reconcilie a mesma cobrança."
                retainedCorrection != null -> "Correção pendente encontrada. Atualize a comanda antes de repetir a ação."
                retainedRefund != null -> "Estorno pendente encontrado. Verifique o pagamento antes de tentar novamente."
                else -> null
            },
        )
    }

    fun clearSelection() {
        state = state.copy(selectedTab = null, cart = emptyList(), orderIntentId = null, paymentIntentId = null, pendingPayment = null)
    }

    fun addProduct(product: Product) {
        if (
            !product.active ||
                product.availability != "AVAILABLE" ||
                state.selectedTab?.summary?.state == "CLOSED" ||
                state.orderIntentId != null
        ) return
        val existing = state.cart.firstOrNull { it.product.id == product.id }
        val next =
            if (existing == null) state.cart + CartLine(product, 1)
            else state.cart.map { if (it.product.id == product.id) it.copy(quantity = it.quantity + 1) else it }
        state = state.copy(cart = next, noticeMessage = null)
    }

    fun changeCartQuantity(productId: String, delta: Int) {
        if (state.orderIntentId != null) return
        val next = state.cart.mapNotNull { line ->
            if (line.product.id != productId) line
            else line.copy(quantity = line.quantity + delta).takeIf { it.quantity > 0 }
        }
        state = state.copy(cart = next)
    }

    fun confirmOrder(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.cart.isEmpty() || tab.state == "CLOSED" || state.submitting) return
        val intentId = state.orderIntentId ?: UUID.randomUUID().toString()
        val intent = RecoveryIntent.ConfirmOrder(
                id = intentId,
                staffId = session.staffId,
                venueId = session.venueId,
                deviceId = session.deviceId,
                idempotencyKey = intentId,
                createdAtMillis = System.currentTimeMillis(),
                state = RecoveryState.CHECKING,
                tabId = tab.id,
                lines = state.cart.map { PendingOrderLine(it.product.id, it.quantity) },
        )
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, orderIntentId = intentId)
        viewModelScope.launch {
            runCatching {
                repository.confirmOrder(session, tab.id, state.cart, intentId)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(
                    submitting = false,
                    cart = emptyList(),
                    noticeMessage = "Pedido enviado para produção.",
                    orderIntentId = null,
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                )
                pendingMutationIntentStore.remove(intent.id)
            }.onFailure { error ->
                // Retrying this exact cart retains the same intent UUID. The API returns the
                // original Order instead of creating a second order after an ambiguous timeout.
                state = state.copy(submitting = false, orderIntentId = intentId)
                showFailure(error, "Verificando pedido. Não envie outro pedido; confirme novamente para reconciliar esta mesma intenção.")
            }
        }
    }

    fun collectPayment(
        session: StoredSession,
        amountCents: Long,
        method: PaymentMethod,
        cashPointId: String?,
    ) {
        val tab = state.selectedTab?.summary ?: return
        if (amountCents <= 0 || amountCents > tab.exposureCents || state.submitting) return
        state.pendingPayment?.let { pending ->
            if (pending.amountCents != amountCents || pending.method != method || pending.cashPointId != cashPointId) {
                state = state.copy(errorMessage = "Há um pagamento pendente nesta comanda. Refaça somente a mesma cobrança de ${formatCents(pending.amountCents)}.")
                return
            }
        }
        val key = state.paymentIntentId ?: UUID.randomUUID().toString()
        val intent = state.pendingPayment ?: RecoveryIntent.StartPayment(key, session.staffId, session.venueId, session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING, tab.id, amountCents, method, cashPointId)
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, paymentIntentId = key, pendingPayment = intent)
        viewModelScope.launch {
            runCatching {
                repository.collectPayment(session, tab.id, amountCents, method, key, cashPointId)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(
                    submitting = false,
                    paymentIntentId = null,
                    pendingPayment = null,
                    noticeMessage = "Pagamento registrado.",
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                )
                pendingMutationIntentStore.remove(intent.id)
            }.onFailure { error ->
                // Retrying this same action uses the same idempotency key and is safe server-side.
                state = state.copy(submitting = false)
                showFailure(error, "Verificando pagamento. Não tente cobrar novamente até reconciliar esta mesma cobrança.")
            }
        }
    }

    fun closeTab(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.submitting) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, completedCorrectionItemId = null)
        viewModelScope.launch {
            runCatching {
                repository.closeTab(session, tab.id)
                repository.tabDetail(session, tab.id)
            }.onSuccess { detail ->
                replaceDetail(detail)
                state = state.copy(submitting = false, noticeMessage = "Comanda fechada.")
            }.onFailure { error ->
                state = state.copy(submitting = false)
                showFailure(error)
            }
        }
    }

    /**
     * Corrections never reproduce financial policy locally.  The native client asks the
     * canonical service for the result, then reloads the affected Tab.
     */
    fun submitCorrection(session: StoredSession, command: CorrectionCommand, reauthPin: String?) {
        val tabId = state.selectedTab?.summary?.id ?: return
        if (state.submitting) return
        val intent = RecoveryIntent.Correction(
            id = command.idempotencyKey,
            staffId = session.staffId,
            venueId = session.venueId,
            deviceId = session.deviceId,
            idempotencyKey = command.idempotencyKey,
            createdAtMillis = System.currentTimeMillis(),
            state = RecoveryState.CHECKING,
            orderItemId = command.itemId,
            itemState = command.itemState,
            action = CorrectionRecoveryAction.valueOf(command.action.name),
            reasonCode = command.reasonCode,
            reasonText = command.reasonText.takeIf(String::isNotBlank),
            replacementProductId = command.replacementProductId,
        )
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, completedCorrectionItemId = null)
        viewModelScope.launch {
            runCatching {
                if (command.requiresPostProductionEndpoint()) {
                    authRepository.reauthenticate(session, reauthPin.orEmpty())
                }
                val result = correctionsRepository.submit(session, command)
                val detail = repository.tabDetail(session, tabId)
                result to detail
            }.onSuccess { (result, detail) ->
                replaceDetail(detail)
                state = state.copy(
                    submitting = false,
                    noticeMessage = correctionNotice(result),
                    completedCorrectionItemId = command.itemId,
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                )
                pendingMutationIntentStore.remove(intent.id)
            }.onFailure { error ->
                state = state.copy(submitting = false)
                if (error is OperationsApiException && error.code == "CORRECTION_STAGE_REQUIRES_APPROVAL") {
                    // The production state advanced between the cached Tab read and the command.
                    // Reload it so the next native attempt uses the manager-authorized endpoint,
                    // instead of repeatedly replaying a known-invalid early-cancel intent.
                    pendingMutationIntentStore.remove(intent.id)
                    viewModelScope.launch {
                        runCatching { repository.tabDetail(session, tabId) }.onSuccess(::replaceDetail)
                    }
                    showFailure(error, "O item avançou na produção. A comanda foi atualizada; confirme a correção autorizada.")
                } else {
                    if (error is OperationsApiException && error.status in 400..499) pendingMutationIntentStore.remove(intent.id)
                    showFailure(error, "A correção não foi confirmada. Atualize a comanda antes de repetir a ação.")
                }
            }
        }
    }

    /** Refunds are always preceded by a fresh server-backed privileged reauthentication. */
    fun submitRefund(session: StoredSession, command: RefundCommand, reauthPin: String) {
        val tabId = state.selectedTab?.summary?.id ?: return
        if (state.submitting) return
        val intent = when (command) {
            is DirectRefundCommand -> RecoveryIntent.Refund(
                command.idempotencyKey, session.staffId, session.venueId, session.deviceId,
                command.idempotencyKey, System.currentTimeMillis(), RecoveryState.CHECKING,
                RefundRecoveryKind.DIRECT, command.paymentId, null, command.amountCents,
                command.reason, command.cashPointId,
            )
            is SettleCorrectionRefundCommand -> RecoveryIntent.Refund(
                command.idempotencyKey, session.staffId, session.venueId, session.deviceId,
                command.idempotencyKey, System.currentTimeMillis(), RecoveryState.CHECKING,
                RefundRecoveryKind.SETTLE_CORRECTION, command.paymentId, command.correctionId,
                command.amountCents, null, command.cashPointId,
            )
        }
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                authRepository.reauthenticate(session, reauthPin)
                val result = refundsRepository.create(session, command)
                val detail = repository.tabDetail(session, tabId)
                result to detail
            }.onSuccess { (result, detail) ->
                replaceDetail(detail)
                state = state.copy(
                    submitting = false,
                    noticeMessage = "Estorno ${refundStatusLabel(result.status).lowercase()}.",
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                )
                pendingMutationIntentStore.remove(intent.id)
            }.onFailure { error ->
                state = state.copy(submitting = false)
                showFailure(error, "O estorno não foi confirmado. Não tente estornar novamente antes de verificar o pagamento.")
            }
        }
    }

    fun completeDelivery(session: StoredSession, taskId: String) {
        if (state.submitting) return
        val key = UUID.randomUUID().toString()
        val intent = RecoveryIntent.CompleteDelivery(
            key, session.staffId, session.venueId, session.deviceId, key,
            System.currentTimeMillis(), RecoveryState.CHECKING, taskId,
        )
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                repository.completeDelivery(session, taskId)
                repository.deliveryTasks(session)
            }.onSuccess { deliveries ->
                state = state.copy(submitting = false, deliveryTasks = deliveries, noticeMessage = "Entrega concluída.")
                pendingMutationIntentStore.remove(intent.id)
            }.onFailure { error ->
                state = state.copy(submitting = false)
                showFailure(error, "Verificando entrega. Atualize antes de tentar concluir novamente.")
            }
        }
    }

    fun occupyTable(session: StoredSession, tableId: String, tabId: String?) = tableAction(session) {
        repository.occupyTable(session, tableId, tabId)
        "Mesa ocupada."
    }

    fun attachTabToOccupancy(session: StoredSession, occupancyId: String, tabId: String) = tableAction(session) {
        repository.attachTabToOccupancy(session, occupancyId, tabId)
        "Comanda associada à ocupação."
    }

    fun releaseTable(session: StoredSession, tableId: String) = tableAction(session) {
        repository.releaseTable(session, tableId)
        "Mesa liberada para limpeza."
    }

    fun startTableCleaning(session: StoredSession, tableId: String) = tableAction(session) {
        repository.startTableCleaning(session, tableId)
        "Limpeza iniciada."
    }

    fun completeTableCleaning(session: StoredSession, tableId: String) = tableAction(session) {
        repository.completeTableCleaning(session, tableId)
        "Mesa disponível."
    }

    fun dismissMessage() {
        state = state.copy(errorMessage = null, noticeMessage = null)
    }

    private fun replaceDetail(detail: TabDetail) {
        state = state.copy(
            selectedTab = detail,
            tabs = listOf(detail.summary) + state.tabs.filterNot { it.id == detail.summary.id },
        )
    }

    private fun action(block: suspend () -> Unit) {
        if (state.submitting) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching { block() }
                .onSuccess { state = state.copy(submitting = false) }
                .onFailure {
                    state = state.copy(submitting = false)
                    showFailure(it)
                }
        }
    }

    private fun tableAction(session: StoredSession, block: suspend () -> String) = action {
        val notice = block()
        state = state.copy(tables = repository.tables(session), noticeMessage = notice)
    }

    private fun showFailure(error: Throwable, suffix: String = "") {
        val message =
            when (error) {
                is OperationsApiException -> "${error.code}: ${error.message}"
                is AuthApiException -> "${error.code}: ${error.message}"
                is IOException -> "Sem conexão com o Rodada."
                else -> error.message ?: "Falha inesperada."
            }
        state = state.copy(
            errorMessage = listOf(message, suffix).filter(String::isNotBlank).joinToString(" "),
            connectivity =
                when (error) {
                    is IOException -> ConnectivityState.OFFLINE
                    else -> state.connectivity
                },
        )
    }

    companion object {
        fun factory(
            repository: OperationsRepository,
            pendingMutationIntentStore: PendingMutationIntentStore,
            authRepository: AuthRepository,
            correctionsRepository: CorrectionsRepository,
            refundsRepository: RefundsRepository,
        ): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    OperationsViewModel(
                        repository,
                        pendingMutationIntentStore,
                        authRepository,
                        correctionsRepository,
                        refundsRepository,
                    ) as T
            }
    }

    private data class RefreshSnapshot(
        val tabs: List<TabSummary>,
        val products: List<Product>,
        val cashPoints: List<CashPoint>,
        val deliveryTasks: List<DeliveryTask>,
        val tables: List<TableSummary>,
        val detail: TabDetail?,
    )
}

private fun correctionNotice(result: CorrectionResult): String =
    when (result.financialDisposition) {
        "REFUND_REQUIRED" -> "Estorno necessário: abra o pagamento desta comanda para resolver ${formatCents(result.refundRequiredCents)}."
        else -> correctionConsequence(result)
    }

private fun RecoveryIntent.ConfirmOrder.toCart(products: List<Product>): List<CartLine> =
    lines.mapNotNull { line ->
        products.firstOrNull { it.id == line.productId }?.let { product ->
            CartLine(product = product, quantity = line.quantity)
        }
    }
