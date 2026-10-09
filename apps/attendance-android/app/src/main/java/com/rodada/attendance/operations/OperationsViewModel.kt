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
    val pixEnabled: Boolean = false,
    val tapSimulationEnabled: Boolean = false,
    val tapPhase: String? = null,
    val integratedPayment: com.rodada.attendance.payments.IntegratedPayment? = null,
    val operationState: org.json.JSONObject? = null,
    val operationPoints: List<Pair<String, String>> = emptyList(),
    val operationPreview: org.json.JSONObject? = null,
    val pendingTabOperation: RecoveryIntent.TabStructure? = null,
    val operationCompleted: Boolean = false,
    val loading: Boolean = false,
    val submitting: Boolean = false,
    val tabs: List<TabSummary> = emptyList(),
    val customers: List<CustomerSummary> = emptyList(),
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

    fun loadTabOperations(session: StoredSession) = action {
        state = state.copy(operationState = null, operationPreview = null, operationCompleted = false)
        val id = state.selectedTab?.summary?.id ?: return@action
        val pending = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.TabStructure>().firstOrNull { it.tabId == id }
        val points = repository.servicePoints(session).getJSONArray("results")
        state = state.copy(operationState = repository.operationState(session, id),
            operationPoints = List(points.length()) { points.getJSONObject(it).let { p -> p.getString("id") to p.getString("label") } },
            operationPreview = null, pendingTabOperation = pending, operationCompleted = false,
            tabs = repository.tabs(session), tables = repository.tables(session), connectivity = ConnectivityState.ONLINE,
            lastSyncedAtMillis = System.currentTimeMillis())
    }

    fun clearOperationPreview() { state = state.copy(operationPreview = null) }

    fun previewTabOperation(session: StoredSession, command: org.json.JSONObject) = action {
        if (state.connectivity != ConnectivityState.ONLINE) error("Atualize a conexão antes de continuar.")
        val id = state.selectedTab?.summary?.id ?: return@action
        state = state.copy(operationPreview = repository.tabOperation(session, id, command, preview = true))
    }

    fun commitTabOperation(session: StoredSession, command: org.json.JSONObject) = action {
        if (state.connectivity != ConnectivityState.ONLINE) error("Atualize a conexão antes de continuar.")
        val id = state.selectedTab?.summary?.id ?: return@action
        val pending = state.pendingTabOperation
        val intent = pending ?: RecoveryIntent.TabStructure(
            id = java.util.UUID.randomUUID().toString(), staffId = session.staffId, venueId = session.venueId,
            deviceId = session.deviceId, idempotencyKey = command.getString("idempotency_key"),
            createdAtMillis = System.currentTimeMillis(), state = RecoveryState.PENDING, tabId = id, commandJson = command.toString())
        pendingMutationIntentStore.save(intent)
        state = state.copy(pendingTabOperation = intent)
        try {
            repository.tabOperation(session, id, org.json.JSONObject(intent.commandJson))
        } catch (error: OperationsApiException) {
            // Deterministic server rejection means no commit. Network ambiguity retains the exact command.
            if (error.status in 400..499) {
                pendingMutationIntentStore.remove(intent.id)
                state = state.copy(pendingTabOperation = null, operationPreview = null)
                state = state.copy(operationState = repository.operationState(session, id), tabs = repository.tabs(session))
            }
            throw error
        }
        pendingMutationIntentStore.remove(intent.id)
        state = state.copy(pendingTabOperation = null, operationPreview = null, operationCompleted = true,
            operationState = null, noticeMessage = "Operação confirmada pelo servidor.")
        replaceDetail(repository.tabDetail(session, id))
        state = state.copy(tabs = repository.tabs(session), tables = repository.tables(session))
    }

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
        if (state.loading || state.submitting) return
        state = state.copy(
            loading = true,
            errorMessage = null,
            noticeMessage = null,
            connectivity = if (state.tabs.isEmpty()) ConnectivityState.RECONNECTING else ConnectivityState.STALE,
        )
        viewModelScope.launch {
            runCatching {
                val caps = runCatching { repository.paymentCapabilities(session) }.getOrDefault(com.rodada.attendance.payments.PaymentCapabilities())
                state = state.copy(pixEnabled = caps.pix, tapSimulationEnabled = caps.tapToPay && caps.simulated && com.rodada.attendance.BuildConfig.DEBUG)
                val tabs = repository.tabs(session)
                val products = repository.products(session)
                val deliveries = repository.deliveryTasks(session)
                val cashPoints = runCatching { repository.cashPoints(session) }.getOrDefault(emptyList())
                val tables = runCatching { repository.tables(session) }.getOrDefault(emptyList())
                val detail = state.selectedTab?.summary?.id?.let { id ->
                    repository.tabDetail(session, id)
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

    fun revalidateConnection(session: StoredSession) {
        viewModelScope.launch { refresh(session) }
    }

    fun markConnectionStale() {
        viewModelScope.launch { state = state.copy(connectivity = ConnectivityState.STALE) }
    }

    fun openTab(session: StoredSession, label: String, customerId: String? = null) = action {
        val opened = repository.openTab(session, label, customerId)
        val detail = repository.tabDetail(session, opened.id)
        state = state.copy(
            tabs = listOf(opened) + state.tabs.filterNot { it.id == opened.id },
            selectedTab = detail,
            cart = emptyList(),
            noticeMessage = "Comanda aberta.",
        )
    }

    fun searchCustomers(session: StoredSession, query: String) = action {
        state = state.copy(customers = repository.customers(session, query))
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
            integratedPayment = null,
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
        state = state.copy(selectedTab = null, integratedPayment = null, cart = emptyList(), orderIntentId = null, paymentIntentId = null, pendingPayment = null)
    }

    fun addProduct(product: Product, customization: Customization = product.defaults()) {
        if (
            !product.active ||
                product.availability != "AVAILABLE" ||
                state.selectedTab?.summary?.state == "CLOSED" ||
                state.orderIntentId != null
        ) return
        if (product.customizationError(customization) != null) return
        val existing = state.cart.firstOrNull { it.product.id == product.id && it.customization == customization }
        val next =
            if (existing == null) state.cart + CartLine(product, 1, customization)
            else state.cart.map { if (it.lineId == existing.lineId) it.copy(quantity = it.quantity + 1) else it }
        state = state.copy(cart = next, noticeMessage = null)
    }

    fun editCartLine(lineId: String, customization: Customization) {
        if (state.orderIntentId != null || state.submitting) return
        state = state.copy(cart = state.cart.map { line ->
            if (line.lineId == lineId) line.copy(customization = customization, product = state.products.firstOrNull { it.id == line.product.id } ?: line.product) else line
        })
    }

    fun changeCartQuantity(productId: String, delta: Int) {
        if (state.orderIntentId != null) return
        val next = state.cart.mapNotNull { line ->
            if (line.lineId != productId) line
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
                lines = state.cart.map { PendingOrderLine(it.product.id, it.quantity, it.customization) },
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
                if (error is OperationsApiException && error.status in 400..499) {
                    pendingMutationIntentStore.remove(intent.id)
                    state = state.copy(orderIntentId = null)
                    runCatching { repository.tabDetail(session, tab.id) }.onSuccess(::replaceDetail)
                    runCatching { repository.products(session) }.onSuccess { state = state.copy(products = it) }
                    showFailure(error)
                    return@onFailure
                }
                showFailure(error, "Verificando pedido. Não envie outro pedido; confirme novamente para reconciliar esta mesma intenção.")
            }
        }
    }

    private fun startTapSimulation(session: StoredSession, amountCents: Long, method: PaymentMethod) {
        val tab = state.selectedTab?.summary ?: return
        if (!state.tapSimulationEnabled || state.submitting || state.connectivity != ConnectivityState.ONLINE) return
        if (amountCents <= 0 || amountCents > tab.exposureCents || state.pendingPayment != null) return
        val key = UUID.randomUUID().toString()
        val intent = RecoveryIntent.StartPayment(key, session.staffId, session.venueId, session.deviceId,
            key, System.currentTimeMillis(), RecoveryState.CHECKING, tab.id, amountCents, method, null)
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, pendingPayment = intent, paymentIntentId = key,
            tapPhase = "SIMULAÇÃO — preparando tentativa no servidor")
        viewModelScope.launch {
            runCatching {
                val prepared = repository.integratedPayment(session, tab.id, amountCents, key, "TAP_TO_PAY")
                require(prepared.simulated) // Never run fake capture against a real merchant.
                state = state.copy(integratedPayment = prepared)
                val provider = com.rodada.attendance.payments.SumUpTapToPayProvider(
                    com.rodada.attendance.payments.TapDeviceCapabilities(30, true, true, true), true,
                    com.rodada.attendance.payments.DeterministicSumUpSdk(), simulated = true,
                    onEvent = { event -> state = state.copy(tapPhase = com.rodada.attendance.payments.tapEventMessage(event, true)) },
                )
                provider.cardProcessing = if (method == PaymentMethod.TAP_DEBIT) com.rodada.attendance.payments.CardProcessing.DEBIT else com.rodada.attendance.payments.CardProcessing.CREDIT
                provider.initialize()
                provider.collect(com.rodada.attendance.payments.TapPaymentRequest(prepared.id, prepared.amountCents))
                provider.tearDown()
                repository.reconcileIntegrated(session, prepared.id)
            }.onSuccess { acceptIntegrated(session, it) }.onFailure {
                state = state.copy(submitting = false, tapPhase = "SIMULAÇÃO — resultado desconhecido; reconcilie sem cobrar novamente")
                showFailure(it)
            }
        }
    }

    fun startPix(session: StoredSession, amountCents: Long) {
        val tab = state.selectedTab?.summary ?: return
        if (!state.pixEnabled || state.submitting || state.connectivity != ConnectivityState.ONLINE) return
        if (amountCents <= 0 || amountCents > tab.exposureCents) return
        val pending = state.pendingPayment
        if (pending != null && (pending.method != PaymentMethod.PIX || pending.amountCents != amountCents)) return
        val key = pending?.idempotencyKey ?: UUID.randomUUID().toString()
        val intent = pending ?: RecoveryIntent.StartPayment(key, session.staffId, session.venueId,
            session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING,
            tab.id, amountCents, PaymentMethod.PIX, null)
        pendingMutationIntentStore.save(intent)
        state = state.copy(submitting = true, pendingPayment = intent, paymentIntentId = key, errorMessage = null)
        viewModelScope.launch {
            runCatching { repository.integratedPayment(session, tab.id, amountCents, key) }
                .onSuccess { acceptIntegrated(session, it) }
                .onFailure {
                    state = state.copy(submitting = false)
                    showFailure(it, "Confirmando Pix. Verifique a mesma intenção; não cobre novamente.")
                }
        }
    }

    fun reconcilePix(session: StoredSession) {
        if (state.submitting) return
        val payment = state.integratedPayment
        if (payment == null) {
            val pending = state.pendingPayment
            val persisted = state.selectedTab?.payments?.lastOrNull { it.method in setOf("PIX", "TAP_TO_PAY") && it.status !in setOf("FAILED", "CANCELLED", "EXPIRED") }
            if (persisted != null) {
                reconcilePixId(session, persisted.id)
            } else if (pending != null) {
                state = state.copy(submitting = true)
                viewModelScope.launch {
                    runCatching { repository.integratedPayment(session, pending.tabId, pending.amountCents,
                        pending.idempotencyKey, pending.method.apiValue) }
                        .onSuccess { acceptIntegrated(session, it) }
                        .onFailure { state = state.copy(submitting = false); showFailure(it) }
                }
            }
            return
        }
        reconcilePixId(session, payment.id)
    }

    private fun reconcilePixId(session: StoredSession, id: String) {
        state = state.copy(submitting = true, errorMessage = null)
        viewModelScope.launch {
            runCatching { repository.reconcileIntegrated(session, id) }
                .onSuccess { acceptIntegrated(session, it) }
                .onFailure {
                    state = state.copy(submitting = false)
                    showFailure(it, "Pagamento ainda não verificado. Não cobre novamente.")
                }
        }
    }

    private suspend fun acceptIntegrated(session: StoredSession, payment: com.rodada.attendance.payments.IntegratedPayment) {
        state = state.copy(submitting = false, integratedPayment = payment, noticeMessage = payment.message)
        if (!payment.blocksNewCharge) {
            state.pendingPayment?.let { pendingMutationIntentStore.remove(it.id) }
            state = state.copy(pendingPayment = null, paymentIntentId = null)
        }
        runCatching { repository.tabDetail(session, payment.tabId) }.onSuccess(::replaceDetail)
    }

    fun collectPayment(
        session: StoredSession,
        amountCents: Long,
        method: PaymentMethod,
        cashPointId: String?,
    ) {
        if (method == PaymentMethod.TAP_CREDIT || method == PaymentMethod.TAP_DEBIT) {
            startTapSimulation(session, amountCents, method)
            return
        }
        if (method == PaymentMethod.PIX) {
            startPix(session, amountCents)
            return
        }
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

    fun resolveLimit(session: StoredSession, limitCents: Long?, reason: String, pin: String,
                     expiresAt: String, key: String) = action {
        val tabId = state.selectedTab?.summary?.id ?: return@action
        if (limitCents == null) repository.requestApproval(session, tabId, reason, key)
        else {
            authRepository.reauthenticate(session, pin)
            repository.approveLimit(session, tabId, limitCents, reason, expiresAt, key)
        }
        replaceDetail(repository.tabDetail(session, tabId))
        state = state.copy(noticeMessage = if (limitCents == null) "Solicitação enviada à gerência." else "Limite temporário aprovado.")
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
    lines.map { line ->
        // Missing/deactivated catalog rows must not change an ambiguous command payload.
        val product = products.firstOrNull { it.id == line.productId }
            ?: Product(line.productId, "Item indisponível", 0, false, "", "UNAVAILABLE")
        CartLine(product = product, quantity = line.quantity, customization = line.customization)
    }
