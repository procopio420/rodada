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
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlin.coroutines.coroutineContext
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.realtime.SseOperationalRealtime
import com.rodada.attendance.realtime.RealtimeSignal
import com.rodada.attendance.realtime.OperationalRealtime
import java.io.IOException
import java.util.UUID

data class OperationsUiState(
    val pixEnabled: Boolean = false,
    val paymentProviderSimulated: Boolean = false,
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
    val historyTabs: List<TabSummary> = emptyList(),
    val historyLoading: Boolean = false,
    val historyLoaded: Boolean = false,
    val historyError: String? = null,
    val historyDetailId: String? = null,
    val historyDetail: TabDetail? = null,
    val historyDetailLoading: Boolean = false,
    val historyDetailError: String? = null,
    val customers: List<CustomerSummary> = emptyList(),
    val products: List<Product> = emptyList(),
    val cashPoints: List<CashPoint> = emptyList(),
    val deliveryTasks: List<DeliveryTask> = emptyList(),
    val deliveryTasksFresh: Boolean = false,
    val deliveryTasksLoading: Boolean = false,
    val deliveryTasksError: String? = null,
    val serviceRequests: List<ServiceRequest> = emptyList(),
    val serviceRequestsFresh: Boolean = false,
    val serviceRequestsError: String? = null,
    val pendingServiceAction: ServiceRequestAction? = null,
    val recoveryEvidence: List<RecoveryEvidence> = emptyList(),
    val recoveryEvidenceReadable: Boolean = false,
    val recoveryDeliveryTaskId: String? = null,
    val exceptionalRecoveryContext: ExceptionalRecoveryContext? = null,
    val tables: List<TableSummary> = emptyList(),
    val pendingTableService: RecoveryIntent.TableService? = null,
    val selectedTab: TabDetail? = null,
    val cart: List<CartLine> = emptyList(),
    val errorMessage: String? = null,
    val noticeMessage: String? = null,
    /** Kept for the complete UI/ViewModel lifecycle and reused by a retry of this cart. */
    val orderIntentId: String? = null,
    val paymentIntentId: String? = null,
    val pendingPayment: RecoveryIntent.StartPayment? = null,
    val queuedOrders: List<RecoveryIntent.ConfirmOrder> = emptyList(),
    /** Lets the composable close only the correction sheet that the server accepted. */
    val completedCorrectionItemId: String? = null,
    val completedOrderTabId: String? = null,
    val connectivity: ConnectivityState = ConnectivityState.RECONNECTING,
    val lastSyncedAtMillis: Long? = null,
    val contextRecoveryPending: Boolean = false,
)

class OperationsViewModel(
    private val repository: OperationsRepository,
    private val pendingMutationIntentStore: PendingMutationIntentStore,
    private val authRepository: AuthRepository,
    private val correctionsRepository: CorrectionsRepository,
    private val refundsRepository: RefundsRepository,
    private val realtime: OperationalRealtime = SseOperationalRealtime(BuildConfig.RODADA_API_BASE_URL, authRepository),
) : ViewModel() {
    var state by mutableStateOf(OperationsUiState())
        private set

    private val orderObservations by lazy {
        PassiveOrderObservations(BuildConfig.RODADA_API_BASE_URL, BuildConfig.VERSION_NAME) { origin ->
            authRepository.observationAccessToken(origin.venueId, origin.staffId, origin.deviceId, origin.sessionId)
        }
    }
    private fun observationOrigin(session: StoredSession) =
        ObservationOrigin(session.venueId, session.staffId, session.deviceId, session.sessionId)

    private var loadedSessionKey: String? = null
    private var refreshGeneration = 0L
    private val financialResponses = FinancialResponseFence()
    private val tabDrafts = TabDraftContexts()
    private var realtimeJob: Job? = null
    private var refreshJob: Job? = null
    private val historyDetailReads = LatestHistoryRead()
    private var deliveryRefreshJob: Job? = null
    private var serviceRefreshJob: Job? = null
    private var orderReplayJob: Job? = null
    private var streamConnected = false
    private var coreReadHealthy = false
    private var invalidationJob: Job? = null
    private var refreshRequested = false

    fun startRealtime(session: StoredSession) {
        stopRealtime()
        realtimeJob = viewModelScope.launch {
            realtime.subscribe(session).collect { signal ->
                when (signal) {
                    RealtimeSignal.Connected -> {
                        streamConnected = true
                        if (coreReadHealthy && state.connectivity != ConnectivityState.OFFLINE && state.lastSyncedAtMillis != null) state = state.copy(connectivity = ConnectivityState.ONLINE)
                    }
                    RealtimeSignal.Reconnecting -> {
                        streamConnected = false
                        state = state.copy(connectivity = state.connectivity.onRealtimeReconnect(state.lastSyncedAtMillis, System.currentTimeMillis()))
                    }
                    RealtimeSignal.Refresh -> {
                        // Coalesce bursts while retaining one revalidation after an in-flight read.
                        refreshRequested = true
                        if (invalidationJob?.isActive != true) {
                            invalidationJob = viewModelScope.launch {
                                while (refreshRequested) {
                                    refreshRequested = false
                                    delay(200)
                                    refreshJob?.join()
                                    refresh(session)
                                    refreshJob?.join()
                                }
                            }
                        }
                    }
                    is RealtimeSignal.Revalidate -> {
                        // A resume cursor is accepted only after canonical reads succeed.
                        refreshJob?.join()
                        val previous = state.lastSyncedAtMillis
                        refresh(session)
                        refreshJob?.join()
                        signal.accepted.complete(state.lastSyncedAtMillis != previous)
                    }
                }
            }
        }
    }

    fun pauseOrderRecovery() {
        // Lifecycle STOP interrupts any in-flight replay; CHECKING stays durable.
        orderReplayJob?.cancel()
        orderReplayJob = null
    }

    fun stopRealtime() {
        realtimeJob?.cancel()
        realtimeJob = null
        invalidationJob?.cancel()
        refreshRequested = false
        streamConnected = false
    }

    fun loadTabOperations(session: StoredSession) = action(session) {
        state = state.copy(operationState = null, operationPreview = null, operationCompleted = false)
        val id = state.selectedTab?.summary?.id ?: return@action
        val pending = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.TabStructure>().firstOrNull { it.tabId == id }
        val points = awaitCurrent { repository.servicePoints(session) }.getJSONArray("results")
        state = state.copy(operationState = awaitCurrent { repository.operationState(session, id) },
            operationPoints = List(points.length()) { points.getJSONObject(it).let { p -> p.getString("id") to p.getString("label") } },
            operationPreview = null, pendingTabOperation = pending, operationCompleted = false,
            tabs = awaitCurrent { repository.tabs(session) }, tables = awaitCurrent { repository.tables(session) }, connectivity = ConnectivityState.ONLINE,
            lastSyncedAtMillis = System.currentTimeMillis())
    }

    fun clearOperationPreview() { state = state.copy(operationPreview = null) }

    fun previewTabOperation(session: StoredSession, command: org.json.JSONObject) = action(session) {
        if (state.connectivity != ConnectivityState.ONLINE) error("Atualize a conexão antes de continuar.")
        val id = state.selectedTab?.summary?.id ?: return@action
        state = state.copy(operationPreview = awaitCurrent { repository.tabOperation(session, id, command, preview = true) })
    }

    fun commitTabOperation(session: StoredSession, command: org.json.JSONObject) = action(session) {
        if (state.connectivity != ConnectivityState.ONLINE) error("Atualize a conexão antes de continuar.")
        val id = state.selectedTab?.summary?.id ?: return@action
        val pending = state.pendingTabOperation
        val intent = pending ?: RecoveryIntent.TabStructure(
            id = java.util.UUID.randomUUID().toString(), staffId = session.staffId, venueId = session.venueId,
            deviceId = session.deviceId, idempotencyKey = command.getString("idempotency_key"),
            createdAtMillis = System.currentTimeMillis(), state = RecoveryState.PENDING, tabId = id, commandJson = command.toString())
        pendingMutationIntentStore.save(intent, session)
        state = state.copy(pendingTabOperation = intent)
        try {
            awaitCurrent { repository.tabOperation(session, id, org.json.JSONObject(intent.commandJson)) }
        } catch (error: OperationsApiException) {
            // Deterministic server rejection means no commit. Network ambiguity retains the exact command.
            if (error.status in setOf(400, 404, 409, 422)) {
                pendingMutationIntentStore.remove(intent.id)
                state = state.copy(pendingTabOperation = null, operationPreview = null,
                    operationState = null, connectivity = ConnectivityState.STALE)
                refreshAfterTabOperationRejection(error) {
                    val canonical = awaitCurrent { repository.operationState(session, id) }
                    val tabs = awaitCurrent { repository.tabs(session) }
                    state = state.copy(operationState = canonical, tabs = tabs,
                        connectivity = ConnectivityState.ONLINE)
                }
            }
            throw error
        }
        pendingMutationIntentStore.remove(intent.id)
        state = state.copy(pendingTabOperation = null, operationPreview = null, operationCompleted = true,
            operationState = null, noticeMessage = "Operação confirmada pelo servidor.")
        replaceDetail(awaitCurrent { repository.tabDetail(session, id) })
        state = state.copy(tabs = awaitCurrent { repository.tabs(session) }, tables = awaitCurrent { repository.tables(session) })
    }

    fun pendingPricing(session: StoredSession, tabId: String) = pendingMutationIntentStore.loadFor(session)
        .filterIsInstance<RecoveryIntent.Pricing>().firstOrNull { it.tabId == tabId }

    suspend fun pricing(session: StoredSession, tabId: String, command: org.json.JSONObject? = null, action: String = "") =
        repository.pricing(session, tabId, command, action)

    suspend fun commitPricing(session: StoredSession, tabId: String, command: org.json.JSONObject, approval: Boolean, pin: String) {
        if (pin.isNotBlank()) repository.reauthenticatePricing(session, pin)
        val key = command.getString("idempotency_key")
        val intent = pendingPricing(session, tabId) ?: RecoveryIntent.Pricing(key, session.staffId, session.venueId,
            session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING, tabId, command.toString())
        pendingMutationIntentStore.save(intent, session)
        try {
            repository.pricing(session, tabId, org.json.JSONObject(intent.commandJson), if (approval) "approval-request/" else "")
        } catch (error: OperationsApiException) {
            if (error.status in 400..499 && error.code != "REAUTH_REQUIRED") pendingMutationIntentStore.remove(intent.id)
            throw error
        }
        pendingMutationIntentStore.remove(intent.id)
        refresh(session)
    }

    fun ensureLoaded(session: StoredSession) {
        val key = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"
        if (loadedSessionKey == key && (state.tabs.isNotEmpty() || state.loading)) return
        if (loadedSessionKey != null && loadedSessionKey != key) {
            // Never let an old foreground replay continue after operator/session switch.
            orderReplayJob?.cancel()
            orderReplayJob = null
            refreshJob?.cancel()
            refreshJob = null
            deliveryRefreshJob?.cancel()
            deliveryRefreshJob = null
            serviceRefreshJob?.cancel()
            serviceRefreshJob = null
            stopRealtime()
            // Never leave a prior operator's draft cart or Tab context on a shared device.
            coreReadHealthy = false
            state = OperationsUiState()
        }
        if (loadedSessionKey != key) {
            refreshGeneration++
            financialResponses.invalidate()
        }
        loadedSessionKey = key
        tabDrafts.enterSession(key)
        loadOrderQueue(session)
        refresh(session)
    }

    fun refresh(session: StoredSession) {
        val expectedSession = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"
        if (loadedSessionKey != null && loadedSessionKey != expectedSession) return
        if (refreshJob?.isActive == true || state.submitting) return
        coreReadHealthy = false
        val generation = refreshGeneration
        state = state.copy(
            loading = true,
            deliveryTasksFresh = false,
            deliveryTasksLoading = true,
            errorMessage = null,
            noticeMessage = pendingMutationIntentStore.reviewMessage(session),
            connectivity = if (state.tabs.isEmpty()) ConnectivityState.RECONNECTING else ConnectivityState.STALE,
        )
        refreshJob = viewModelScope.launch {
            runCatching {
                pendingMutationIntentStore.loadFor(session).map { it.evidence() } +
                    pendingMutationIntentStore.blockedFor(session).map { it.evidence(reviewOnly = true) }
            }.onSuccess { state = state.copy(recoveryEvidence = it.sortedBy { row -> row.capturedAtMillis }, recoveryEvidenceReadable = true) }
                .onFailure { state = state.copy(recoveryEvidence = emptyList(), recoveryEvidenceReadable = false, noticeMessage = pendingMutationIntentStore.reviewMessage(session)) }
            if (deliveryRefreshJob?.isActive != true) {
                deliveryRefreshJob = viewModelScope.launch { readDeliveryTasks(session) }
            }
            if (serviceRefreshJob?.isActive != true) {
                serviceRefreshJob = viewModelScope.launch { readServiceRequests(session) }
            }
            runCatching {
                val caps = runCatching { repository.paymentCapabilities(session) }.getOrDefault(com.rodada.attendance.payments.PaymentCapabilities())
                coroutineContext.ensureActive()
                state = state.copy(pixEnabled = caps.pix, paymentProviderSimulated = caps.simulated, tapSimulationEnabled = caps.tapToPay && caps.simulated && com.rodada.attendance.BuildConfig.DEBUG)
                val tabs = repository.tabs(session)
                val products = repository.products(session)
                val cashPoints = runCatching { repository.cashPoints(session) }.getOrDefault(emptyList())
                val tables = runCatching { repository.tables(session) }.getOrDefault(emptyList())
                val detail = state.selectedTab?.summary?.id?.let { id ->
                    repository.tabDetail(session, id)
                }
                RefreshSnapshot(tabs, products, cashPoints, tables, detail)
            }.onSuccess { snapshot ->
                coroutineContext.ensureActive()
                if (generation != refreshGeneration) return@launch
                coreReadHealthy = true
                state = state.copy(
                    loading = false,
                    tabs = snapshot.tabs,
                    products = snapshot.products,
                    cashPoints = snapshot.cashPoints,
                    tables = snapshot.tables,
                    pendingTableService = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().firstOrNull(),
                    selectedTab = snapshot.detail ?: state.selectedTab,
                    connectivity = ConnectivityState.ONLINE,
                    lastSyncedAtMillis = System.currentTimeMillis(),
                    contextRecoveryPending = snapshot.detail?.let { detail -> pendingMutationIntentStore.loadFor(session).any { it.targetsContext(detail) } } ?: false,
                )
                // Canonical HTTP read, not SSE alone, authorizes order reconciliation.
                loadOrderQueue(session)
                resumePendingOrders(session)
            }.onFailure {
                coroutineContext.ensureActive()
                if (generation != refreshGeneration) return@launch
                state = state.copy(loading = false)
                showFailure(it)
            }
        }
    }

    /** History is intentionally fetched only on request, not with every SSE/foreground refresh. */
    fun loadTabHistory(session: StoredSession) {
        val guard = sessionActionGuard(session)
        if (state.historyLoading || !guard.isCurrent()) return
        state = state.copy(historyLoading = true, historyError = null)
        viewModelScope.launch {
            runCatching { guard.awaitCurrent { repository.tabHistory(session) } }
                .onSuccess { rows ->
                    if (guard.isCurrent()) state = state.copy(
                        historyTabs = rows, historyLoading = false, historyLoaded = true, historyError = null)
                }
                .onFailure {
                    if (guard.isCurrent()) state = state.copy(
                        historyLoading = false, historyLoaded = false,
                        historyError = "Não foi possível carregar o histórico. Tente novamente.")
                }
        }
    }

    fun inspectHistory(session: StoredSession, tabId: String?) {
        val guard = sessionActionGuard(session)
        if (!guard.isCurrent()) return
        val read = historyDetailReads.start()
        state = state.copy(historyDetailId = tabId, historyDetail = null,
            historyDetailLoading = tabId != null, historyDetailError = null)
        if (tabId == null) return
        viewModelScope.launch {
            runCatching { guard.awaitCurrent { repository.tabDetail(session, tabId) } }.onSuccess { detail ->
                if (guard.isCurrent() && historyDetailReads.isCurrent(read) && state.historyDetailId == tabId) state = state.copy(
                    historyDetail = detail, historyDetailLoading = false)
            }.onFailure {
                if (guard.isCurrent() && historyDetailReads.isCurrent(read) && state.historyDetailId == tabId) state = state.copy(
                    historyDetailLoading = false, historyDetailError = "Não foi possível consultar a comanda.")
            }
        }
    }

    private suspend fun readDeliveryTasks(session: StoredSession) {
        val result = runCatching { repository.deliveryTasks(session) }
        coroutineContext.ensureActive()
        result.onSuccess { state = state.copy(deliveryTasks = it, deliveryTasksFresh = true, deliveryTasksLoading = false, deliveryTasksError = null) }
            .onFailure { state = state.copy(deliveryTasksFresh = false, deliveryTasksLoading = false,
                deliveryTasksError = "Entregas desatualizadas. Atualize para conferir. Pedidos continuam disponíveis com a conexão atualizada.") }
    }

    private suspend fun readServiceRequests(session: StoredSession, guard: FinancialResponseFence.Guard = sessionActionGuard(session)) {
        if (!guard.isCurrent()) return
        state = state.copy(serviceRequestsFresh = false)
        val result = runCatching { guard.awaitCurrent { repository.serviceRequests(session) } }
        coroutineContext.ensureActive()
        result.onSuccess { state = state.copy(serviceRequests = it, serviceRequestsFresh = true, serviceRequestsError = null) }
            .onFailure {
                if (guard.isCurrent()) state = state.copy(serviceRequestsFresh = false, serviceRequestsError = "Chamadas desatualizadas. Atualize antes de agir.")
            }
    }

    fun updateServiceRequest(session: StoredSession, taskId: String, complete: Boolean) = action(session) {
        if (!state.serviceRequestsFresh) error("Atualize as chamadas antes de agir.")
        val key = sessionKey(session)
        val intent = serviceRequestActionForSession(state.pendingServiceAction, key, taskId, complete)
        try {
            awaitCurrent { repository.serviceRequestAction(session, intent) }
            state = state.copy(pendingServiceAction = null, noticeMessage = if (intent.complete) "Chamada concluída." else "Chamada assumida.")
        } catch (failure: Exception) {
            check()
            val ambiguous = failure is IOException || (failure is OperationsApiException && failure.status >= 500)
            state = state.copy(pendingServiceAction = if (ambiguous) intent else null)
            if (ambiguous) error("Resultado não confirmado. Verifique a mesma chamada antes de executar outra ação.")
            throw failure
        } finally { if (isCurrent()) readServiceRequests(session, this) }
    }

    fun revalidateConnection(session: StoredSession) {
        viewModelScope.launch { refresh(session) }
    }

    suspend fun readPartySize(session: StoredSession, occupancyId: String) = repository.partySize(session, occupancyId)
    suspend fun recordPartySize(session: StoredSession, occupancyId: String, command: PartySizeCommand) = repository.partySize(session, occupancyId, command)

    fun markConnectionStale() {
        coreReadHealthy = false
        viewModelScope.launch { state = state.copy(connectivity = ConnectivityState.STALE, serviceRequestsFresh = false, deliveryTasksFresh = false) }
    }

    fun openTab(session: StoredSession, label: String, customerId: String? = null) = action(session) {
        check(state.cart.isEmpty() && state.orderIntentId == null && state.pendingTableService == null) { "Conclua o rascunho ou verifique o atendimento pendente antes de abrir outra comanda." }
        val opened = awaitCurrent { repository.openTab(session, label, customerId) }
        val detail = awaitCurrent { repository.tabDetail(session, opened.id) }
        state = state.copy(
            tabs = listOf(opened) + state.tabs.filterNot { it.id == opened.id },
            selectedTab = detail,
            cart = emptyList(),
            noticeMessage = "Comanda aberta.",
        )
    }

    fun searchCustomers(session: StoredSession, query: String) = action(session) {
        state = state.copy(customers = awaitCurrent { repository.customers(session, query) })
    }

    fun selectTab(session: StoredSession, tabId: String) {
        if (!state.canLeaveTabContext()) return
        action(session) {
            val records = pendingMutationIntentStore.loadFor(session)
            check(state.selectedTab == null || records.none { it.targetsContext(state.selectedTab!!) }) { "Verifique a pendência original antes de trocar de comanda." }
            loadTabContext(session, tabId, guard = this)
        }
    }

    /** Read-only navigation boundary; an old queue target never authorizes a deep link. */
    suspend fun readOperationalTask(session: StoredSession, id: String, type: String): StaffTaskRead {
        val expectedSession = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"
        check(loadedSessionKey == expectedSession) { "A sessão original mudou." }
        val read = repository.staffTask(session, id, type)
        val tables = if (read.service.target is StaffTaskTarget.Table) repository.tables(session) else null
        check(loadedSessionKey == expectedSession) { "A sessão original mudou." }
        state = if (type == "DELIVERY") state.copy(deliveryTasks = state.deliveryTasks.map { if (it.id == id) requireNotNull(read.delivery) else it })
            else state.copy(serviceRequests = state.serviceRequests.map { if (it.id == id) read.service else it })
        if (tables != null) state = state.copy(tables = tables)
        return read
    }

    fun openRecovery(session: StoredSession, intentId: String) {
        val delivery = runCatching { pendingMutationIntentStore.loadFor(session).firstOrNull { it.id == intentId } }
            .getOrElse { state = state.copy(errorMessage = "Registro ilegível. Preserve a evidência original."); return }
        if (delivery is RecoveryIntent.CompleteDelivery) {
            recoverDelivery(session, delivery, allowSubmit = false)
            return
        }
        openOtherRecovery(session, intentId)
    }

    private fun openOtherRecovery(session: StoredSession, intentId: String) = action(session) {
        val refreshingOriginal = state.exceptionalRecoveryContext?.original?.id == intentId
        check(refreshingOriginal || state.selectedTab == null && state.cart.isEmpty()) { "Volte à fila sem abandonar um rascunho para abrir esta pendência." }
        state = state.copy(exceptionalRecoveryContext = null)
        val original = pendingMutationIntentStore.loadFor(session).firstOrNull { it.id == intentId }
            ?: error("Registro indisponível na sessão original. Atualize as pendências; não recrie a operação.")
        val destination = original.evidence()
        check(destination.canOpenContext) { "Este registro exige revisão do contexto original pela gerência." }
        if (destination.needsExceptionalContext) {
            val target = awaitCurrent { repository.exceptionalRecoveryTarget(session, original) }
            val detail = awaitCurrent { repository.tabDetail(session, target.tabId) }
            target.validate(detail)
            awaitCurrent { authRepository.withAuthorizedAccess(session) { Unit } }
            check(pendingMutationIntentStore.loadFor(session).any { it == original }) { "A pendência mudou durante a leitura. Atualize antes de continuar." }
            state = state.copy(exceptionalRecoveryContext = ExceptionalRecoveryContext(original, target, detail))
        }
        destination.tabId?.let { tabId -> loadTabContext(session, tabId, original, this) }
        destination.taskId?.let { taskId ->
            val deliveries = awaitCurrent { repository.deliveryTasks(session) }
            awaitCurrent { authRepository.withAuthorizedAccess(session) { Unit } }
            check(pendingMutationIntentStore.loadFor(session).any { it == original }) { "A pendência mudou durante a leitura. Atualize antes de continuar." }
            state = state.copy(deliveryTasks = deliveries, recoveryDeliveryTaskId = taskId,
                noticeMessage = if (deliveries.none { it.id == taskId }) "Entrega ausente da fila atual. Isso não comprova conclusão; peça revisão do histórico original." else null)
        }
    }

    fun clearExceptionalRecoveryContext() {
        state = state.copy(exceptionalRecoveryContext = null)
    }

    /** Explicit path to the existing read-only queue; never resolves a financial intent. */
    fun leaveForExceptionalRecovery(session: StoredSession) {
        if (state.loading || state.submitting || state.orderIntentId != null || state.paymentIntentId != null || state.pendingPayment != null) return
        val detail = state.selectedTab ?: return
        val retained = pendingMutationIntentStore.loadFor(session).any {
            (it is RecoveryIntent.Correction || it is RecoveryIntent.Refund) && it.targetsContext(detail)
        }
        if (!retained) return
        tabDrafts.save(detail.summary.id, state.cart)
        state = state.copy(selectedTab = null, cart = emptyList(), contextRecoveryPending = false,
            exceptionalRecoveryContext = null, integratedPayment = null)
    }

    private suspend fun loadTabContext(session: StoredSession, tabId: String, original: RecoveryIntent? = null, guard: FinancialResponseFence.Guard = sessionActionGuard(session)) {
        guard.check()
        val scopeBeforeRead = loadedSessionKey
        check(state.pendingTableService == null) { "Verifique o atendimento pendente antes de selecionar outra comanda." }
        val detail = guard.awaitCurrent { repository.tabDetail(session, tabId) }
        check(detail.summary.id == tabId) { "A comanda retornada não corresponde à selecionada." }
        guard.awaitCurrent { authRepository.withAuthorizedAccess(session) { Unit } }
        check(loadedSessionKey == scopeBeforeRead) { "A sessão mudou durante a leitura. Selecione a comanda novamente." }
        val records = pendingMutationIntentStore.loadFor(session)
        if (original != null) check(records.any { it == original }) { "A pendência mudou durante a leitura. Atualize antes de continuar." }
        val retained = records.filterIsInstance<RecoveryIntent.ConfirmOrder>().firstOrNull { it.tabId == tabId && (original !is RecoveryIntent.ConfirmOrder || it.id == original.id) }
        val retainedPayment = records.filterIsInstance<RecoveryIntent.StartPayment>().firstOrNull { it.tabId == tabId && (original !is RecoveryIntent.StartPayment || it.id == original.id) }
        val retainedCorrection = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.Correction>().firstOrNull { it.orderItemId in detail.orders.flatMap { order -> order.items }.map { item -> item.id } }
        val retainedRefund = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.Refund>().firstOrNull { refund -> detail.payments.any { it.id == refund.paymentId } }
        tabDrafts.enterSession("${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}")
        state.selectedTab?.summary?.id?.let { tabDrafts.save(it, state.cart) }
        // A repeated round is an independent order; never restore it as editable cart lines.
        val retainedCart = when {
            retained == null -> tabDrafts.read(tabId)
            !retained.clearCartOnConfirmation -> if (state.selectedTab?.summary?.id == tabId) state.cart else tabDrafts.read(tabId)
            else -> retained.toCart(state.products)
        }
        state = state.copy(
            selectedTab = detail,
            integratedPayment = null,
            cart = retainedCart,
            orderIntentId = retained?.idempotencyKey,
            paymentIntentId = retainedPayment?.idempotencyKey,
            pendingPayment = retainedPayment,
            contextRecoveryPending = records.any { it.targetsContext(detail) },
            noticeMessage = pendingMutationIntentStore.reviewMessage(session) ?: when {
                retained != null -> "Pedido pendente encontrado. Verifique o resultado antes de adicionar novos itens."
                retainedPayment != null -> "Pagamento pendente encontrado. Não tente cobrar novamente; reconcilie a mesma cobrança."
                retainedCorrection != null -> "Correção pendente encontrada. Atualize a comanda antes de repetir a ação."
                retainedRefund != null -> "Estorno pendente encontrado. Verifique o pagamento antes de tentar novamente."
                else -> null
            },
        )
    }

    fun returnAfterConfirmedOrder(session: StoredSession): Boolean {
        if (state.submitting || state.loading || state.completedOrderTabId == null) return false
        val shouldReturn = state.shouldReturnAfterConfirmedOrder()
        state = state.copy(completedOrderTabId = null)
        if (!shouldReturn) return false
        clearSelection(session)
        return state.selectedTab == null
    }

    fun clearSelection(session: StoredSession? = null) {
        val records = try { session?.let { pendingMutationIntentStore.loadFor(it) } }
            catch (error: Exception) { showFailure(error); return }
        val pending = records?.let { current -> state.selectedTab?.let { detail -> current.any { it.targetsContext(detail) } } } == true
        if (records != null) state = state.copy(contextRecoveryPending = pending, recoveryEvidence = records.map { it.evidence() })
        if (!state.canLeaveTabContext() || pending) {
            if (pending) state = state.copy(contextRecoveryPending = true)
            state = state.copy(noticeMessage = "Verifique a operação pendente antes de sair. A intenção original está preservada.")
            return
        }
        state.selectedTab?.summary?.id?.let { tabDrafts.save(it, state.cart) }
        state = state.copy(selectedTab = null, integratedPayment = null, cart = emptyList(), orderIntentId = null, paymentIntentId = null, pendingPayment = null, contextRecoveryPending = false)
    }

    fun addProduct(product: Product, customization: Customization = product.defaults(), quantity: Int = 1) {
        if (
            !product.active ||
                product.availability != "AVAILABLE" ||
                state.selectedTab?.summary?.state == "CLOSED" ||
                state.orderIntentId != null
        ) return
        if (!state.canLeaveTabContext() || product.customizationError(customization) != null) return
        val next = addDraftQuantity(state.cart, product, customization, quantity)
        if (next == null) {
            state = state.copy(noticeMessage = "Máximo de 99 unidades por configuração. Revise a quantidade.")
            return
        }
        state = state.copy(cart = next, noticeMessage = null)
    }

    fun repeatOrder(session: StoredSession, tabId: String, review: RepeatOrderReview, quantities: Map<String, Int>) {
        val lines = state.repeatedOrderLines(tabId, review, quantities)
        if (lines == null) {
            state = state.copy(errorMessage = "A rodada ou o contexto mudou. Revise os itens e tente novamente.")
            return
        }
        // A round is an independent Order; never borrow the manual cart.
        queueOrder(session, tabId, lines, clearCartOnConfirmation = false)
    }

    fun editCartLine(lineId: String, customization: Customization) {
        if (!state.canLeaveTabContext()) return
        val line = state.cart.firstOrNull { it.lineId == lineId } ?: return
        val product = state.products.firstOrNull { it.id == line.product.id } ?: return
        if (product.customizationError(customization) != null) return
        val next = editDraftConfiguration(state.cart, lineId, product, customization)
        state = if (next == null) state.copy(noticeMessage = "Máximo de 99 unidades por configuração. Revise a quantidade.") else state.copy(cart = next)
    }

    fun changeCartQuantity(lineId: String, delta: Int) {
        if (!state.canLeaveTabContext()) return
        val line = state.cart.firstOrNull { it.lineId == lineId } ?: return
        val product = state.products.firstOrNull { it.id == line.product.id }
        if (delta > 0 && (product == null || !product.active || product.availability != "AVAILABLE")) return
        val next = changeDraftQuantity(state.cart, lineId, delta)
        state = if (next == null) state.copy(noticeMessage = "Máximo de 99 unidades por configuração. Revise a quantidade.") else state.copy(cart = next)
    }

    /**
     * A tap captures an exact, encrypted order intent before any network request.
     * OFFLINE never claims delivery; the next successful canonical read drains it.
     */
    fun confirmOrder(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.cart.isEmpty() || tab.state == "CLOSED" || state.submitting) return
        queueOrder(session, tab.id, state.cart.map { PendingOrderLine(it.product.id, it.quantity, it.customization) },
            clearCartOnConfirmation = true)
    }

    private fun queueOrder(session: StoredSession, tabId: String, lines: List<PendingOrderLine>,
                           clearCartOnConfirmation: Boolean) {
        if (lines.isEmpty() || state.submitting) return
        val existing = runCatching { pendingMutationIntentStore.orderQueue(session) }
            .getOrElse { showFailure(it, "Fila local ilegível. Não envie um novo pedido."); return }
            .firstOrNull { it.tabId == tabId }
        if (existing != null) {
            state = state.copy(orderIntentId = existing.idempotencyKey,
                noticeMessage = "Pedido já guardado. Sua intenção original será reconciliada, sem duplicar.")
            if (existing.state != RecoveryState.ACTION_REQUIRED && existing.state != RecoveryState.FAILED_TERMINAL) {
                revalidateConnection(session)
            }
            return
        }
        val key = state.orderIntentId ?: UUID.randomUUID().toString()
        val intent = RecoveryIntent.ConfirmOrder(
            id = key, staffId = session.staffId, venueId = session.venueId,
            deviceId = session.deviceId, idempotencyKey = key,
            createdAtMillis = System.currentTimeMillis(), state = RecoveryState.PENDING,
            tabId = tabId, lines = lines, clearCartOnConfirmation = clearCartOnConfirmation,
        )
        if (!preserveIntent(intent, session)) return
        runCatching { orderObservations.intentSaved(observationOrigin(session), intent.idempotencyKey) }
        loadOrderQueue(session)
        state = state.copy(orderIntentId = key, errorMessage = null,
            noticeMessage = if (state.connectivity == ConnectivityState.OFFLINE)
                "Pedido guardado neste aparelho. Ainda NÃO foi recebido pelo bar."
            else "Pedido guardado. Verificando confirmação no servidor.")
        // New order submission must not be misidentified as connection loss.
        if (state.connectivity != ConnectivityState.OFFLINE) resumePendingOrders(session)
    }

    /** Restores encrypted, original-session order records even before canonical HTTP succeeds. */
    private fun loadOrderQueue(session: StoredSession): Boolean {
        val orders = runCatching { pendingMutationIntentStore.orderQueue(session) }
            .getOrElse {
                state = state.copy(noticeMessage = pendingMutationIntentStore.reviewMessage(session)
                    ?: "Fila ilegível. Não repita pedidos sem revisão da gerência.")
                return false
            }
        state = state.copy(queuedOrders = orders)
        return true
    }

    /**
     * Only orders replay, oldest-first and one at a time. The backend owns availability,
     * limit, tab state and idempotency; any rejection parks the exact command for review.
     */
    private fun resumePendingOrders(session: StoredSession) {
        if (orderReplayJob?.isActive == true || state.submitting) return
        val queue = runCatching { pendingMutationIntentStore.orderQueue(session) }
            .getOrElse {
                state = state.copy(noticeMessage = "Fila local ilegível. Reenvio bloqueado para revisão.")
                return
            }
        if (OrderRecoveryPolicy.awaitingReconciliation(queue).isEmpty()) return
        orderReplayJob = viewModelScope.launch {
            for (intent in OrderRecoveryPolicy.awaitingReconciliation(queue)) {
                // Another operator may log in while a coroutine is suspended.
                val originatingKey = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"
                if (loadedSessionKey != originatingKey) break
                // Stop if a different staff/venue/device/session replaced the originating context.
                val currentQueue = try {
                    pendingMutationIntentStore.orderQueue(session)
                } catch (error: Exception) {
                    state = state.copy(errorMessage = "Falha na fila criptografada. Reenvio interrompido.")
                    break
                }
                val now = currentQueue.firstOrNull { it.id == intent.id } ?: continue
                if (!OrderRecoveryPolicy.canReplay(now, SessionBoundRecoveryIntent(now, session.sessionId), session)) {
                    break
                }
                state = state.copy(submitting = true,
                    noticeMessage = OrderSubmissionStatus.message(now.state))
                val observation = runCatching { orderObservations.begin(observationOrigin(session), now.idempotencyKey,
                    now.state != RecoveryState.PENDING) }.getOrNull()
                var commandStarted = false
                try {
                    // Revalidate authentication, Tab and Catalog before using the exact saved command.
                    repository.tabDetail(session, now.tabId)
                    val products = repository.products(session)
                    pendingMutationIntentStore.updateOrderState(now, session, RecoveryState.CHECKING)
                    commandStarted = true
                    val receipt = repository.confirmOrder(session, now.tabId, now.toCart(products), now.idempotencyKey)
                    val canonical = repository.tabDetail(session, now.tabId)
                    receipt.requireReadback(canonical)
                    observation?.finish(PassiveOrderObservations.Outcome.CONFIRMED)
                    pendingMutationIntentStore.remove(now.id)
                    loadOrderQueue(session)
                    if (state.selectedTab?.summary?.id == now.tabId) {
                        replaceDetail(canonical)
                        state = state.copy(cart = if (now.clearCartOnConfirmation) emptyList() else state.cart,
                            orderIntentId = null,
                            completedOrderTabId = if (now.clearCartOnConfirmation) now.tabId else null)
                    }
                    state = state.copy(noticeMessage = "Pedido confirmado pelo servidor.",
                        connectivity = ConnectivityState.ONLINE, lastSyncedAtMillis = System.currentTimeMillis())
                } catch (error: Exception) {
                    if (error is kotlinx.coroutines.CancellationException) throw error
                    observation?.finish(when {
                        !commandStarted && error is com.rodada.attendance.auth.AuthApiException -> PassiveOrderObservations.Outcome.AUTH_UNAVAILABLE
                        !commandStarted -> PassiveOrderObservations.Outcome.PREPARATION_FAILED
                        error is OperationsApiException && error.status in 400..499 -> PassiveOrderObservations.Outcome.REJECTED
                        else -> PassiveOrderObservations.Outcome.UNKNOWN
                    })
                    if (error is OperationsApiException && error.status in 400..499) {
                        // A stale price, disabled product, closed Tab or lost authority is not
                        // silently retried on reconnect. Preserve evidence for reconciliation.
                        runCatching {
                            pendingMutationIntentStore.updateOrderState(now, session, RecoveryState.ACTION_REQUIRED)
                        }.onFailure { state = state.copy(errorMessage = "Falha ao preservar conflito; confira a gerência.") }
                        loadOrderQueue(session)
                        showFailure(error, "Pedido guardado para revisão; nenhum novo pedido foi criado localmente.")
                    } else {
                        // Unknown outcome may have committed. Keep CHECKING and the same UUID.
                        loadOrderQueue(session)
                        showFailure(error, "Resultado do pedido desconhecido. A mesma chave será conferida após reconectar.")
                    }
                    break // Stop on first uncertainty; never reorder dependent commands.
                } finally {
                    state = state.copy(submitting = false)
                }
            }
        }
    }

    /** A suspended read may finish after a new operator has acquired this ViewModel. */
    private fun financialGuard(session: StoredSession, original: RecoveryIntent.StartPayment? = null): FinancialResponseFence.Guard {
        var expected = original
        return financialResponses.capture(
            current = {
                val pending = state.pendingPayment
                (loadedSessionKey == null || loadedSessionKey == "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}") &&
                pending == expected && (expected == null ||
                    (expected!!.staffId == session.staffId && expected!!.venueId == session.venueId &&
                        expected!!.deviceId == session.deviceId))
            },
            checkpoint = { updated -> expected = updated },
            verify = {
                check(expected == null || pendingMutationIntentStore.loadFor(session)
                    .filterIsInstance<RecoveryIntent.StartPayment>().any { it == expected }) {
                    "A intenção financeira durável mudou. Confira a recuperação original."
                }
            },
        )
    }

    private fun startTapSimulation(session: StoredSession, amountCents: Long, method: PaymentMethod) {
        val tab = state.selectedTab?.summary ?: return
        if (!state.tapSimulationEnabled || state.submitting || state.connectivity != ConnectivityState.ONLINE) return
        if (amountCents <= 0 || amountCents > tab.exposureCents || state.pendingPayment != null) return
        val key = UUID.randomUUID().toString()
        val intent = RecoveryIntent.StartPayment(key, session.staffId, session.venueId, session.deviceId,
            key, System.currentTimeMillis(), RecoveryState.CHECKING, tab.id, amountCents, method, null, tab.version)
        if (!preserveIntent(intent, session)) return
        state = state.copy(submitting = true, pendingPayment = intent, paymentIntentId = key,
            tapPhase = "SIMULAÇÃO — preparando tentativa no servidor")
        val guard = financialGuard(session, intent)
        viewModelScope.launch {
            runCatching {
                guard.check()
                val prepared = repository.integratedPayment(session, tab.id, amountCents, key, "TAP_TO_PAY", tab.version)
                require(prepared.simulated) // Never run fake capture against a real merchant.
                guard.check()
                state = state.copy(integratedPayment = prepared)
                val provider = com.rodada.attendance.payments.SumUpTapToPayProvider(
                    com.rodada.attendance.payments.TapDeviceCapabilities(30, true, true, true), true,
                    com.rodada.attendance.payments.DeterministicSumUpSdk(), simulated = true,
                    onEvent = { event -> if (guard.isCurrent()) state = state.copy(tapPhase = com.rodada.attendance.payments.tapEventMessage(event, true)) },
                )
                provider.cardProcessing = if (method == PaymentMethod.TAP_DEBIT) com.rodada.attendance.payments.CardProcessing.DEBIT else com.rodada.attendance.payments.CardProcessing.CREDIT
                provider.initialize()
                guard.check()
                provider.collect(com.rodada.attendance.payments.TapPaymentRequest(prepared.id, prepared.amountCents))
                provider.tearDown()
                guard.check()
                repository.reconcileIntegrated(session, prepared.id)
            }.mapCatching { acceptIntegrated(session, it, intent, guard) }.onFailure {
                if (!guard.isCurrent()) return@onFailure
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
            tab.id, amountCents, PaymentMethod.PIX, null, tab.version)
        if (!preserveIntent(intent, session)) return
        state = state.copy(submitting = true, pendingPayment = intent, paymentIntentId = key, errorMessage = null)
        val guard = financialGuard(session, intent)
        viewModelScope.launch {
            runCatching { guard.check(); repository.integratedPayment(session, tab.id, amountCents, key, expectedVersion = intent.expectedVersion) }
                .mapCatching { acceptIntegrated(session, it, intent, guard) }
                .onFailure {
                    if (!guard.isCurrent()) return@onFailure
                    state = state.copy(submitting = false)
                    showFailure(it, "Confirmando Pix. Verifique a mesma intenção; não cobre novamente.")
                }
        }
    }

    fun reconcilePix(session: StoredSession) {
        if (state.submitting) return
        val original = state.pendingPayment
        if (original != null) {
            if (original.method !in setOf(PaymentMethod.PIX, PaymentMethod.TAP_CREDIT, PaymentMethod.TAP_DEBIT)) return
            state = state.copy(submitting = true)
            val guard = financialGuard(session, original)
            viewModelScope.launch {
                runCatching {
                    recoverIntegratedIntent(original,
                        replay = { command -> guard.check(); repository.integratedPayment(session, command.tabId, command.amountCents,
                            command.idempotencyKey, command.method.apiValue, command.expectedVersion) },
                        reconcile = { guard.check(); repository.reconcileIntegrated(session, it) })
                }.mapCatching { acceptIntegrated(session, it, original, guard) }
                    .onFailure { if (guard.isCurrent()) { state = state.copy(submitting = false); showFailure(it) } }
            }
            return
        }
        val paymentId = state.integratedPayment?.id ?: state.selectedTab?.payments?.lastOrNull {
            it.method in setOf("PIX", "TAP_TO_PAY") && it.status !in setOf("FAILED", "CANCELLED", "EXPIRED")
        }?.id ?: return
        reconcilePixId(session, paymentId)
    }

    private fun reconcilePixId(session: StoredSession, id: String) {
        if (state.pendingPayment != null) { reconcilePix(session); return }
        state = state.copy(submitting = true, errorMessage = null)
        val guard = financialGuard(session)
        viewModelScope.launch {
            runCatching { guard.check(); repository.reconcileIntegrated(session, id).also { check(it.id == id) } }
                .mapCatching { acceptIntegrated(session, it, guard = guard) }
                .onFailure {
                    if (!guard.isCurrent()) return@onFailure
                    state = state.copy(submitting = false)
                    showFailure(it, "Pagamento ainda não verificado. Não cobre novamente.")
                }
        }
    }

    private suspend fun acceptIntegrated(session: StoredSession,
        payment: com.rodada.attendance.payments.IntegratedPayment,
        source: RecoveryIntent.StartPayment? = null,
        guard: FinancialResponseFence.Guard,
    ) {
        guard.check()
        val pending = state.pendingPayment
        if (pending != null) {
            check(source == pending) { "A resposta não pertence à intenção de pagamento original." }
            validateIntegratedIntent(pending, payment)
        }
        val detail = repository.tabDetail(session, payment.tabId)
        guard.check()
        check(detail.summary.id == payment.tabId)
        if (!payment.blocksNewCharge) {
            check(detail.payments.any { it.id == payment.id && it.amountCents == payment.amountCents &&
                it.method == payment.method && it.status == payment.status && it.simulated == payment.simulated }) {
                "Pagamento ainda não corresponde ao histórico canônico."
            }
            pending?.let { pendingMutationIntentStore.remove(it.id) }
        }
        replaceDetail(detail)
        state = state.copy(submitting = false, integratedPayment = payment, noticeMessage = payment.message,
            pendingPayment = if (payment.blocksNewCharge) pending else null,
            paymentIntentId = if (payment.blocksNewCharge) state.paymentIntentId else null)
    }

    fun collectPayment(
        session: StoredSession,
        amountCents: Long,
        method: PaymentMethod,
        cashPointId: String?,
        closeRequested: Boolean = false,
    ) {
        val currentTab = state.selectedTab?.summary ?: return
        if (state.blocksNewFullPayment(currentTab, amountCents)) {
            state = state.copy(errorMessage = "Resolva o pedido não enviado antes de receber todo o saldo. O recebimento integral encerra a comanda.")
            return
        }
        if (method == PaymentMethod.TAP_CREDIT || method == PaymentMethod.TAP_DEBIT) {
            startTapSimulation(session, amountCents, method)
            return
        }
        if (method == PaymentMethod.PIX) { startPix(session, amountCents); return }
        val tab = state.selectedTab?.summary ?: return
        if (state.submitting) return
        val existing = state.pendingPayment
        if (existing == null && (amountCents <= 0 || amountCents > tab.exposureCents)) return
        if (existing != null && (existing.tabId != tab.id || existing.amountCents != amountCents ||
            existing.method != method || existing.cashPointId != cashPointId)) {
            state = state.copy(errorMessage = "Reconcilie o recebimento original antes de iniciar outro.")
            return
        }
        val key = state.paymentIntentId ?: UUID.randomUUID().toString()
        val intent = existing ?: RecoveryIntent.StartPayment(key, session.staffId, session.venueId,
            session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING,
            tab.id, amountCents, method, cashPointId, tab.version, closeRequested)
        if (!preserveIntent(intent, session)) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null,
            paymentIntentId = intent.idempotencyKey, pendingPayment = intent)
        val guard = financialGuard(session, intent)
        viewModelScope.launch {
            runCatching {
                val detail = settleReceipt(intent,
                    collect = { command -> repository.collectPayment(session, command.tabId, command.amountCents,
                        command.method, command.idempotencyKey, command.cashPointId, command.expectedVersion).id },
                    persist = { confirmed ->
                        guard.check()
                        pendingMutationIntentStore.save(confirmed, session)
                        state = state.copy(pendingPayment = confirmed)
                        guard.checkpoint(confirmed)
                    },
                    read = { repository.tabDetail(session, it) },
                    close = { repository.closeTab(session, it) },
                    observed = ::replaceDetail,
                    checkCurrent = guard::check)
                guard.check()
                val remaining = pendingMutationIntentStore.loadFor(session).filterNot { it.id == intent.id }
                pendingMutationIntentStore.remove(intent.id)
                state = state.copy(contextRecoveryPending = remaining.any { it.targetsContext(detail) },
                    recoveryEvidence = remaining.map { it.evidence() }, paymentIntentId = null, pendingPayment = null, submitting = false,
                    noticeMessage = if (detail.summary.state == "CLOSED") "Comanda encerrada." else "Pagamento registrado.",
                    connectivity = ConnectivityState.ONLINE, lastSyncedAtMillis = System.currentTimeMillis())
            }.onFailure { error ->
                if (!guard.isCurrent()) return@onFailure
                showFailure(error, if (state.pendingPayment?.confirmedPaymentId != null)
                    "Recebido; encerramento pendente. Confira a comanda, sem cobrar novamente."
                    else "Verificando pagamento. Reconcilie somente a cobrança original.")
            }
            if (guard.isCurrent()) state = state.copy(submitting = false)
        }
    }

    fun recoverReceipt(session: StoredSession) {
        val original = state.pendingPayment ?: return
        if (original.method !in setOf(PaymentMethod.CASH, PaymentMethod.EXTERNAL_TERMINAL)) {
            reconcilePix(session)
            return
        }
        collectPayment(session, original.amountCents, original.method, original.cashPointId, original.closeRequested)
    }

    fun keepPaidTabOpen(session: StoredSession) {
        val original = state.pendingPayment ?: return
        if (original.confirmedPaymentId == null || state.submitting) return
        state = state.copy(submitting = true)
        val guard = financialGuard(session, original)
        viewModelScope.launch {
            runCatching {
                guard.check()
                val detail = repository.tabDetail(session, original.tabId)
                guard.check()
                check(detail.summary.id == original.tabId && detail.payments.any { receiptMatches(original, original.confirmedPaymentId, it) })
                replaceDetail(detail)
                val remaining = pendingMutationIntentStore.loadFor(session).filterNot { it.id == original.id }
                pendingMutationIntentStore.remove(original.id)
                state = state.copy(contextRecoveryPending = remaining.any { it.targetsContext(detail) },
                    recoveryEvidence = remaining.map { it.evidence() }, pendingPayment = null, paymentIntentId = null, submitting = false,
                    noticeMessage = "Recebimento confirmado; comanda mantida no estado canônico.")
            }.onFailure { if (guard.isCurrent()) showFailure(it) }
            if (guard.isCurrent()) state = state.copy(submitting = false)
        }
    }

    fun closeTab(session: StoredSession) {
        val tab = state.selectedTab?.summary ?: return
        if (state.submitting || state.pendingPayment != null || state.orderIntentId != null || state.cart.isNotEmpty()) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null, completedCorrectionItemId = null)
        val guard = financialGuard(session)
        viewModelScope.launch {
            runCatching {
                guard.check()
                val current = repository.tabDetail(session, tab.id)
                guard.check()
                check(current.summary.id == tab.id)
                check(current.summary.exposureCents == 0L) { "A conta possui saldo atualizado; confira antes de encerrar." }
                if (current.summary.state == "CLOSED") current else {
                    check(current.summary.exposureCents == 0L) { "A conta possui saldo atualizado; confira antes de encerrar." }
                    repository.closeTab(session, tab.id)
                    repository.tabDetail(session, tab.id).also {
                        check(it.summary.id == tab.id && it.summary.state == "CLOSED" && it.summary.exposureCents == 0L) { "Encerramento ainda não confirmado." }
                    }
                }
            }.onSuccess { detail ->
                if (!guard.isCurrent()) return@onSuccess
                replaceDetail(detail)
                state = state.copy(submitting = false, noticeMessage = "Comanda fechada.")
            }.onFailure { error ->
                if (!guard.isCurrent()) return@onFailure
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
            quantity = command.quantity,
        )
        val original = runCatching { pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.Correction>().firstOrNull { it.orderItemId == command.itemId } }
            .getOrElse { showFailure(it, "Confira a correção guardada antes de continuar."); return }
        if (original != null && original.copy(createdAtMillis = intent.createdAtMillis, state = intent.state) != intent) {
            showFailure(IllegalStateException("Correction intent pending"), "Há uma correção sem confirmação. Confira a intenção original antes de enviar outra.")
            return
        }
        if (!preserveIntent(original ?: intent, session)) return
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
        if (!preserveIntent(intent, session)) return
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
        if (state.submitting || loadedSessionKey != "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}") return
        val retained = runCatching { pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.CompleteDelivery>().firstOrNull { it.deliveryTaskId == taskId } }
            .getOrElse { state = state.copy(errorMessage = "Registro de entrega ilegível. Preserve a evidência para revisão."); return }
        val key = retained?.idempotencyKey ?: UUID.randomUUID().toString()
        val intent = retained ?: RecoveryIntent.CompleteDelivery(
            key, session.staffId, session.venueId, session.deviceId, key,
            System.currentTimeMillis(), RecoveryState.CHECKING, taskId,
        )
        if (!preserveIntent(intent, session)) return
        recoverDelivery(session, intent, allowSubmit = true)
    }

    private fun recoverDelivery(session: StoredSession, intent: RecoveryIntent.CompleteDelivery, allowSubmit: Boolean) {
        if (state.submitting) return
        val expectedSession = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"
        val guard = financialResponses.capture(
            current = { loadedSessionKey == expectedSession },
            verify = { check(pendingMutationIntentStore.loadFor(session).any { it == intent }) { "A intenção original de entrega mudou." } },
        )
        if (!guard.isCurrent()) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runCatching {
                val read = reconcileDelivery(intent.deliveryTaskId, allowSubmit,
                    read = { repository.deliveryRecoveryRead(session, intent.deliveryTaskId) },
                    submit = { repository.completeDelivery(session, intent.deliveryTaskId) }, checkCurrent = guard::check)
                guard.check()
                val deliveryRead = runCatching { repository.deliveryTasks(session) }
                val deliveries = deliveryRead.getOrElse {
                    state.deliveryTasks.filterNot { task -> read.confirmed && task.id == intent.deliveryTaskId }
                }
                guard.check()
                if (read.confirmed) {
                    pendingMutationIntentStore.remove(intent.id)
                    state = state.copy(submitting = false, deliveryTasks = deliveries,
                        deliveryTasksFresh = deliveryRead.isSuccess,
                        deliveryTasksError = if (deliveryRead.isSuccess) null else "Entregas desatualizadas. Atualize para conferir.",
                        recoveryEvidence = state.recoveryEvidence.filterNot { it.id == intent.id },
                        recoveryDeliveryTaskId = null, noticeMessage = "Entrega concluída.")
                } else {
                    state = state.copy(submitting = false, deliveryTasks = deliveries,
                        deliveryTasksFresh = deliveryRead.isSuccess,
                        deliveryTasksError = if (deliveryRead.isSuccess) null else "Entregas desatualizadas. Atualize para conferir.",
                        recoveryDeliveryTaskId = intent.deliveryTaskId,
                        noticeMessage = "Entrega consultada. A intenção original continua pendente; confira o estado antes de agir.")
                }
            }.onFailure { error ->
                if (!guard.isCurrent()) return@onFailure
                state = state.copy(submitting = false)
                showFailure(error, "Entrega sem confirmação. Consulte a mesma intenção original nas pendências.")
            }
        }
    }

    fun startTableService(session: StoredSession, tableId: String) = tableServiceCommand(session,
        "/hospitality/tables/$tableId/service/start/", org.json.JSONObject())

    fun openFirstTableTab(session: StoredSession, tableId: String, label: String) = tableServiceCommand(session,
        "/hospitality/tables/$tableId/service/open-tab/", org.json.JSONObject().put("display_label", label))

    fun openTableTab(session: StoredSession, occupancy: TableOccupancy, label: String) = tableServiceCommand(session,
        "/hospitality/occupancies/${occupancy.id}/tabs/open/", org.json.JSONObject()
            .put("display_label", label).put("expected_generation", occupancy.generation))

    fun claimTableService(session: StoredSession, occupancy: TableOccupancy) = tableServiceCommand(session,
        "/hospitality/occupancies/${occupancy.id}/responsibility/claim/", org.json.JSONObject()
            .put("expected_responsibility_version", occupancy.responsibilityVersion)
            .put("mode", if (occupancy.responsibleStaffId == null) "CLAIM_UNASSIGNED" else "TAKE_OVER"))

    fun moveTableTab(session: StoredSession, occupancyId: String, tab: TabSummary) = tableServiceCommand(session,
        "/tabs/${tab.id}/operations/", org.json.JSONObject().put("kind", "MOVE_LOCATION")
            .put("expected_version", tab.version).put("occupancy_id", occupancyId))

    fun retryTableService(session: StoredSession) = tableServiceCommand(session, "", org.json.JSONObject())

    private fun tableServiceCommand(session: StoredSession, path: String, payload: org.json.JSONObject) = action(session) {
        check(state.cart.isEmpty() && state.orderIntentId == null) { "Conclua o rascunho antes de alterar a mesa." }
        val pending = pendingMutationIntentStore.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().firstOrNull()
        val key = pending?.idempotencyKey ?: UUID.randomUUID().toString()
        val intent = pending ?: RecoveryIntent.TableService(key, session.staffId, session.venueId,
            session.deviceId, key, System.currentTimeMillis(), RecoveryState.CHECKING, path,
            payload.put("idempotency_key", key).toString())
        if (!preserveIntent(intent, session)) return@action
        state = state.copy(pendingTableService = intent, noticeMessage = null)
        val result = try {
            awaitCurrent { repository.tableService(session, intent.path, org.json.JSONObject(intent.commandJson)) }
        } catch (error: OperationsApiException) {
            check()
            if (error.status in setOf(400, 404, 409, 422)) {
                pendingMutationIntentStore.remove(intent.id)
                state = state.copy(pendingTableService = null, tables = awaitCurrent { repository.tables(session) })
            }
            throw error
        }
        pendingMutationIntentStore.remove(intent.id)
        state = state.copy(pendingTableService = null, tables = awaitCurrent { repository.tables(session) },
            tabs = awaitCurrent { repository.tabs(session) }, noticeMessage = null)
        result.optString("tab_id").takeIf { it.isNotBlank() }?.let { id ->
            state = state.copy(selectedTab = awaitCurrent { repository.tabDetail(session, id) }, cart = emptyList())
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

    fun releaseTable(session: StoredSession, target: TableReleaseCommand) = tableAction(session, showNotice = false) {
        check(state.deliveryTasksFresh && state.connectivity == ConnectivityState.ONLINE) { "Atualize as entregas antes de liberar a mesa." }
        repository.releaseTable(session, target)
        "Mesa liberada para limpeza."
    }

    fun startTableCleaning(session: StoredSession, tableId: String) = tableAction(session) {
        repository.startTableCleaning(session, tableId)
        "Limpeza iniciada."
    }

    fun completeTableCleaning(session: StoredSession, tableId: String) = tableAction(session, showNotice = false) {
        repository.completeTableCleaning(session, tableId)
        "Mesa disponível."
    }

    fun dismissMessage() {
        state = state.copy(errorMessage = null, noticeMessage = null)
    }

    fun resolveLimit(session: StoredSession, limitCents: Long?, reason: String, pin: String,
                     expiresAt: String, key: String) = action(session) {
        val tabId = state.selectedTab?.summary?.id ?: return@action
        if (limitCents == null) awaitCurrent { repository.requestApproval(session, tabId, reason, key) }
        else {
            awaitCurrent { authRepository.reauthenticate(session, pin) }
            awaitCurrent { repository.approveLimit(session, tabId, limitCents, reason, expiresAt, key) }
        }
        replaceDetail(awaitCurrent { repository.tabDetail(session, tabId) })
        state = state.copy(noticeMessage = if (limitCents == null) "Solicitação enviada à gerência." else "Limite temporário aprovado.")
    }

    private fun preserveIntent(intent: RecoveryIntent, session: StoredSession): Boolean =
        runCatching { pendingMutationIntentStore.save(intent, session) }
            .onFailure { showFailure(it, "A intenção não foi enviada; confira o histórico canônico.") }
            .isSuccess

    private fun replaceDetail(detail: TabDetail) {
        state = state.copy(
            selectedTab = detail,
            tabs = listOf(detail.summary) + state.tabs.filterNot { it.id == detail.summary.id },
        )
    }

    private fun sessionKey(session: StoredSession) = "${session.staffId}:${session.venueId}:${session.deviceId}:${session.sessionId}"

    private fun sessionActionGuard(session: StoredSession) = financialResponses.capture(
        current = { loadedSessionKey == sessionKey(session) },
    )

    private fun action(session: StoredSession, block: suspend FinancialResponseFence.Guard.() -> Unit) {
        val guard = sessionActionGuard(session)
        if (state.submitting || !guard.isCurrent()) return
        state = state.copy(submitting = true, errorMessage = null, noticeMessage = null)
        viewModelScope.launch {
            runSessionAction(guard, block,
                onSuccess = { state = state.copy(submitting = false) },
                onFailure = { state = state.copy(submitting = false); showFailure(it) })
        }
    }

    private fun tableAction(session: StoredSession, showNotice: Boolean = true, block: suspend () -> String) = action(session) {
        check(state.pendingTableService == null) { "Verifique o atendimento pendente antes de alterar a mesa." }
        val notice = awaitCurrent { block() }
        state = state.copy(tables = awaitCurrent { repository.tables(session) }, noticeMessage = if (showNotice) notice else null)
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
            serviceRequestsFresh = state.serviceRequestsFresh && error !is IOException,
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
