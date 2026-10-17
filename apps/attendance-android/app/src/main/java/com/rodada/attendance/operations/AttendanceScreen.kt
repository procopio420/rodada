package com.rodada.attendance.operations

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.platform.testTag
import androidx.compose.foundation.background
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.HorizontalDivider
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import com.rodada.attendance.ui.RodadaVisual
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import com.rodada.attendance.ui.RodadaButton as Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import com.rodada.attendance.ui.RodadaOutlinedButton as OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.DisposableEffect
import androidx.activity.compose.LocalActivity
import androidx.activity.ComponentActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.LifecycleOwner
import android.net.ConnectivityManager
import android.net.Network
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.cash.CashShiftScreen
import com.rodada.attendance.cash.CashShiftViewModel
import com.rodada.attendance.cash.CashRecoveryScreen
import com.rodada.attendance.corrections.CorrectionAction
import com.rodada.attendance.corrections.CorrectionCommand
import com.rodada.attendance.corrections.correctionActionsFor
import com.rodada.attendance.corrections.requiresPostProductionEndpoint
import com.rodada.attendance.refunds.DirectRefundCommand
import com.rodada.attendance.refunds.RefundCommand
import com.rodada.attendance.refunds.SettleCorrectionRefundCommand
import java.util.UUID
import java.time.Instant
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.CancellationException

@Composable
fun AttendanceScreen(
    session: StoredSession,
    viewModel: OperationsViewModel,
    cashShiftViewModel: CashShiftViewModel,
    onOpenAccount: () -> Unit,
) {
    val state = viewModel.state
    val context = LocalContext.current
    val lifecycleOwner = LocalActivity.current as? LifecycleOwner
    DisposableEffect(lifecycleOwner, session.staffId, session.venueId, session.deviceId, session.sessionId) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) viewModel.revalidateConnection(session)
        }
        lifecycleOwner?.lifecycle?.addObserver(observer)
        val connectivity = context.getSystemService(ConnectivityManager::class.java)
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) { viewModel.revalidateConnection(session) }
            override fun onLost(network: Network) { viewModel.markConnectionStale() }
        }
        connectivity.registerDefaultNetworkCallback(callback)
        onDispose {
            lifecycleOwner?.lifecycle?.removeObserver(observer)
            connectivity.unregisterNetworkCallback(callback)
        }
    }
    var operatingTab by remember { mutableStateOf(false) }
    LaunchedEffect(state.operationCompleted) { if (state.operationCompleted) operatingTab = false }
    var openingTab by rememberSaveable { mutableStateOf(false) }
    var choosingOrderDestination by rememberSaveable { mutableStateOf(false) }
    var adjustingPricing by rememberSaveable { mutableStateOf(false) }
    var takingPayment by rememberSaveable { mutableStateOf(false) }
    var viewingIntegrated by rememberSaveable { mutableStateOf(false) }
    LaunchedEffect(state.integratedPayment?.id, state.integratedPayment?.status) {
        val payment = state.integratedPayment
        if (payment != null) viewingIntegrated = true
        while (payment?.blocksNewCharge == true) {
            delay(5000)
            viewModel.reconcilePix(session)
        }
    }
    var resolvingLimit by rememberSaveable { mutableStateOf(false) }
    var section by rememberSaveable { mutableStateOf(FrontlineSection.NOW) }
    val contextStates = rememberSaveableStateHolder()
    var peak by rememberSaveable { mutableStateOf(false) }
    var showingRecovery by rememberSaveable { mutableStateOf(false) }
    var serviceTaskId by rememberSaveable { mutableStateOf<String?>(null) }
    var deliveryTaskId by rememberSaveable { mutableStateOf<String?>(null) }
    var targetTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var targetOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var targetGeneration by rememberSaveable { mutableStateOf<Int?>(null) }
    var taskNotice by rememberSaveable { mutableStateOf<String?>(null) }
    var requestedWorkspaceSection by rememberSaveable { mutableStateOf<String?>(null) }
    var serviceContextTabId by rememberSaveable { mutableStateOf<String?>(null) }
    var serviceTableTarget by rememberSaveable(stateSaver = listSaver<StaffTaskTarget.Table?, Any>(
        save = { it?.let { target -> listOf(target.tableId, target.occupancyId, target.generation) } ?: emptyList() },
        restore = { if (it.isEmpty()) null else StaffTaskTarget.Table(it[0] as String, it[1] as String, it[2] as Int) },
    )) { mutableStateOf<StaffTaskTarget.Table?>(null) }
    var readingTask by remember { mutableStateOf(false) }
    val taskScope = rememberCoroutineScope()
    val canUseCash = session.capabilities.any { it in setOf("cash.shift.open", "cash.adjustment.create", "cash.review") }
    fun leaveTaskWorkspace() {
        viewModel.clearSelection(session)
        if (viewModel.state.selectedTab == null) {
            serviceTaskId = null
            serviceContextTabId = null
            serviceTableTarget = null
            requestedWorkspaceSection = null
            targetTableId = null
            targetOccupancyId = null
            targetGeneration = null
        }
    }
    fun openService(task: ServiceRequest) {
        if (readingTask) return
        readingTask = true
        taskScope.launch { try {
        val current = viewModel.readOperationalTask(session, task.id, task.type).service
        serviceTaskId = current.id
        serviceContextTabId = null
        serviceTableTarget = null
        when (val target = current.target) {
            is StaffTaskTarget.Tab -> {
                serviceContextTabId = target.tabId
                requestedWorkspaceSection = if (current.type == "BILL_REQUEST") "Conta" else null
                viewModel.selectTab(session, target.tabId)
            }
            is StaffTaskTarget.Table -> {
                val table = target.currentTable(viewModel.state.tables)
                if (table == null || state.loading || state.connectivity != ConnectivityState.ONLINE) {
                    taskNotice = "Vínculo desatualizado. Atualize a fila e confira a ocupação; nenhuma comanda foi escolhida."
                    viewModel.refresh(session)
                } else {
                    serviceTableTarget = target
                    targetTableId = table.id; targetOccupancyId = target.occupancyId; targetGeneration = target.generation
                    section = FrontlineSection.TABLES
                }
            }
            StaffTaskTarget.Unavailable -> taskNotice = "Destino autorizado indisponível. Atualize a fila; não escolha uma comanda pelo texto da mesa."
        }
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            taskNotice = "Não foi possível revalidar esta tarefa. Atualize a fila antes de abrir o contexto."
        } finally { readingTask = false } }
    }
    fun openTableTab(tabId: String) {
        val originalTable = serviceTableTarget
        val id = serviceTaskId
        if (originalTable == null || id == null) { viewModel.selectTab(session, tabId); return }
        if (readingTask) return
        readingTask = true
        taskScope.launch { try {
            val task = viewModel.readOperationalTask(session, id,
                viewModel.state.serviceRequests.firstOrNull { it.id == id }?.type ?: error("Chamada indisponível")).service
            check(task.target == originalTable && originalTable.currentTable(viewModel.state.tables)?.activeOccupancy?.tabs?.any { it.id == tabId } == true)
            serviceContextTabId = tabId
            requestedWorkspaceSection = if (task.type == "BILL_REQUEST") "Conta" else null
            viewModel.selectTab(session, tabId)
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            taskNotice = "A chamada ou ocupação mudou. Atualize e selecione novamente; nenhuma comanda foi aberta."
        } finally { readingTask = false } }
    }
    fun openDelivery(task: DeliveryTask, openTab: Boolean = false) {
        if (readingTask) return
        readingTask = true
        taskScope.launch { try {
            val current = viewModel.readOperationalTask(session, task.id, "DELIVERY")
            if (openTab) {
                val target = current.service.target as? StaffTaskTarget.Tab ?: error("Destino indisponível")
                deliveryTaskId = null; serviceTaskId = null; serviceContextTabId = null; serviceTableTarget = null
                requestedWorkspaceSection = null
                viewModel.selectTab(session, target.tabId)
            } else deliveryTaskId = task.id
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            taskNotice = "A entrega mudou ou não pôde ser revalidada. Atualize antes de abrir."
        } finally { readingTask = false } }
    }
    var correctionItemId by remember { mutableStateOf<String?>(null) }
    var refundTarget by remember { mutableStateOf<RefundTarget?>(null) }
    val correctionItem = correctionItemId?.let { itemId ->
        state.selectedTab?.orders?.asSequence()?.flatMap { it.items.asSequence() }?.firstOrNull { it.id == itemId }
    }

    LaunchedEffect(state.completedCorrectionItemId) {
        if (state.completedCorrectionItemId == correctionItemId) correctionItemId = null
    }
    LaunchedEffect(correctionItemId, correctionItem) {
        if (correctionItemId != null && correctionItem == null) correctionItemId = null
    }

    LaunchedEffect(session.staffId, session.venueId, session.deviceId, session.sessionId) { cashShiftViewModel.clearRecoveryContext(); viewModel.ensureLoaded(session) }
    val activity = LocalActivity.current as? ComponentActivity
    DisposableEffect(session.staffId, session.venueId, session.deviceId, session.sessionId, activity) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> { viewModel.refresh(session); viewModel.startRealtime(session) }
                Lifecycle.Event.ON_STOP -> { viewModel.stopRealtime(); viewModel.pauseOrderRecovery() }
                else -> Unit
            }
        }
        activity?.lifecycle?.addObserver(observer)
        if (activity == null || activity.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) viewModel.startRealtime(session)
        onDispose {
            activity?.lifecycle?.removeObserver(observer)
            viewModel.stopRealtime()
            viewModel.pauseOrderRecovery()
        }
    }

    Surface(modifier = Modifier.fillMaxSize(), color = com.rodada.attendance.ui.RodadaVisual.Ground) {
        Column(modifier = Modifier.fillMaxSize()) {
            com.rodada.attendance.ui.AttendanceHeader(
                venueName = session.venueName,
                staffName = session.staffDisplayName,
                connectivity = state.connectivity,
                busy = state.loading || state.submitting || readingTask,
                peak = peak,
                onTogglePeak = { peak = !peak },
                onOpenAccount = onOpenAccount,
                onRefresh = { viewModel.refresh(session) },
                canUseCash = canUseCash,
                onOpenCash = { section = FrontlineSection.CASH },
                onOpenRecovery = { showingRecovery = true },
                pendingCount = state.pendingEvidence().size,
            )
            state.pendingTableService?.let {
                Text("Verificando atendimento. Intenção original preservada.")
                OutlinedButton(enabled = !state.submitting && !state.loading, onClick = { viewModel.retryTableService(session) }) { Text("Verificar mesma intenção") }
            }
            Box(modifier = Modifier.weight(1f)) {
            when (val selected = state.selectedTab) {
                null -> {
                    when (section) {
                        FrontlineSection.NOW -> contextStates.SaveableStateProvider("now:${session.sessionId}") {
                            AttendanceNowScreen(state, onOpenService = ::openService, onOpenDelivery = { openDelivery(it) })
                        }
                        FrontlineSection.TABS, FrontlineSection.TABLES -> contextStates.SaveableStateProvider("tables:${session.sessionId}") { TablesScreen(
                            state = state,
                            requestedTarget = targetTableId?.let { tableId -> targetOccupancyId?.let { occupancyId -> targetGeneration?.let { generation -> StaffTaskTarget.Table(tableId, occupancyId, generation) } } },
                            onTargetConsumed = { targetTableId = null; targetOccupancyId = null; targetGeneration = null },
                            canManageTables = "table.manage" in session.capabilities,
                            staffId = session.staffId,
                            canOpenTabs = "tab.open" in session.capabilities,
                            onOccupy = { tableId, tabId -> viewModel.occupyTable(session, tableId, tabId) },
                            onStartService = { id -> if (state.tables.firstOrNull { it.id == id }?.tableServiceEnabled == true) viewModel.startTableService(session, id) else viewModel.occupyTable(session, id, null) },
                            onOpenTableTab = { occupancy, label -> viewModel.openTableTab(session, occupancy, label) },
                            onClaim = { viewModel.claimTableService(session, it) },
                            onSelectTab = ::openTableTab,
                            canMoveTabs = "tab.move" in session.capabilities,
                            onMoveTab = { occupancyId, tab -> viewModel.moveTableTab(session, occupancyId, tab) },
                            onAttachTab = { occupancyId, tabId -> viewModel.attachTabToOccupancy(session, occupancyId, tabId) },
                            onRelease = { viewModel.releaseTable(session, it) },
                            onStartCleaning = { viewModel.startTableCleaning(session, it) },
                            onCompleteCleaning = { viewModel.completeTableCleaning(session, it) },
                            onOpenStandaloneTab = { openingTab = true },
                            onOpenFirstTab = { tableId, label -> viewModel.openFirstTableTab(session, tableId, label) },
                            onLoadHistory = { viewModel.loadTabHistory(session) },
                            partySizeEditor = { occupancyId -> PartySizeEditor(load = { viewModel.readPartySize(session, occupancyId) }, save = { viewModel.recordPartySize(session, occupancyId, it) }) },
                        )
                        }
                        FrontlineSection.CASH -> CashShiftScreen(session, cashShiftViewModel)
                    }
                }
                else -> Dialog(
                    onDismissRequest = ::leaveTaskWorkspace,
                    properties = DialogProperties(usePlatformDefaultWidth = false, dismissOnClickOutside = false),
                ) { Surface(Modifier.fillMaxSize().safeDrawingPadding()) {
                    val recovery = state.exceptionalRecoveryContext
                    if (recovery != null) ExceptionalRecoveryScreen(recovery, state.submitting,
                        onRefresh = { viewModel.openRecovery(session, recovery.original.id) },
                        onBack = { viewModel.leaveForExceptionalRecovery(session); section = FrontlineSection.NOW })
                    else Column {
                    state.tables.firstOrNull { table -> table.activeOccupancy?.tabs?.any { it.id == selected.summary.id } == true }?.let { Text("Mesa ${it.label} · ${selected.summary.displayLabel}") }
                    if (state.orderIntentId != null) Text("Pedido pendente. Verifique a intenção original antes de sair.")
                    if (state.contextRecoveryPending && state.orderIntentId == null && state.paymentIntentId == null) {
                        OutlinedButton(onClick = { viewModel.leaveForExceptionalRecovery(session); if (viewModel.state.selectedTab == null) section = FrontlineSection.NOW }, enabled = !state.submitting && !state.loading) { Text("Conferir pendências") }
                    }
                    serviceTaskId?.let { id -> state.serviceRequests.firstOrNull { it.id == id && serviceContextTabId == selected.summary.id } }?.let { task ->
                        ServiceTaskContext(task, session.staffId, state,
                            onAction = { complete -> viewModel.updateServiceRequest(session, task.id, complete) })
                    }
                    contextStates.SaveableStateProvider("tab:${session.sessionId}:${selected.summary.id}") { TabWorkspace(
                    requestedSection = requestedWorkspaceSection,
                    onRequestedSectionConsumed = { requestedWorkspaceSection = null },
                    state = state,
                    tab = selected,
                    onBack = ::leaveTaskWorkspace,
                    onAdd = { product, selection -> viewModel.addProduct(product, selection) },
                    onAddQuantity = { product, selection, quantity -> viewModel.addProduct(product, selection, quantity) },
                    onEdit = viewModel::editCartLine,
                    onQuantity = viewModel::changeCartQuantity,
                    onConfirmOrder = { viewModel.confirmOrder(session) },
                    onAdjustPricing = { adjustingPricing = true },
                    onPay = { takingPayment = true },
                    onClose = { viewModel.closeTab(session) },
                    onOperations = { operatingTab = true; viewModel.loadTabOperations(session) },
                    onResolveLimit = { resolvingLimit = true },
                    onCorrectItem = { correctionItemId = it.id },
                    onRefundPayment = { refundTarget = RefundTarget.Payment(it) },
                    onSettleCorrection = { refundTarget = RefundTarget.Correction(it) },
                    onRepeatOrder = { review, quantities -> viewModel.repeatOrder(session, selected.summary.id, review, quantities) },
                ) }
                } } }
            }
            if (cashShiftViewModel.recoveryContext.intentId != null) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    CashRecoveryScreen(cashShiftViewModel.recoveryContext,
                        onRefresh = { cashShiftViewModel.recoveryContext.intentId?.let { cashShiftViewModel.openRecovery(session, it) } },
                        onBack = { cashShiftViewModel.clearRecoveryContext() })
                }
            }
            state.exceptionalRecoveryContext?.let { context ->
                Surface(modifier = Modifier.fillMaxSize()) {
                    ExceptionalRecoveryScreen(context, state.submitting,
                        onRefresh = { viewModel.openRecovery(session, context.original.id) },
                        onBack = viewModel::clearExceptionalRecoveryContext)
                }
            }
            }
            if (state.selectedTab == null && cashShiftViewModel.recoveryContext.intentId == null && state.exceptionalRecoveryContext == null) {
                FrontlineNavigation(section = section, onSelect = { section = it; choosingOrderDestination = false; targetTableId = null; targetOccupancyId = null; targetGeneration = null; serviceTaskId = null; serviceContextTabId = null; serviceTableTarget = null },
                    onOrder = { serviceTaskId = null; serviceContextTabId = null; serviceTableTarget = null; choosingOrderDestination = true }, busy = state.loading || state.submitting || readingTask || state.pendingTableService != null)
            }

        }
    }

    if (showingRecovery) Dialog(onDismissRequest = { showingRecovery = false }, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.fillMaxSize().safeDrawingPadding()) {
            Column {
                TextButton(onClick = { showingRecovery = false }) { Text("← Voltar ao atendimento") }
                Box(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                    RecoveryPanel(state, onOpen = { id ->
                        showingRecovery = false
                        if (state.pendingEvidence().any { it.id == id && it.shiftId != null && it.canOpenContext }) cashShiftViewModel.openRecovery(session, id)
                        else viewModel.openRecovery(session, id)
                    }, onCheckOrders = { viewModel.revalidateConnection(session) })
                }
            }
        }
    }
    taskNotice?.let { MessageDialog("Destino indisponível", it) { taskNotice = null } }
    deliveryTaskId?.let { id ->
        DeliveryTaskDetail(state.deliveryTasks.firstOrNull { it.id == id }, busy = state.loading || state.submitting || readingTask || state.connectivity != ConnectivityState.ONLINE, staffId = session.staffId,
            onDismiss = { deliveryTaskId = null }, onOpenTab = { state.deliveryTasks.firstOrNull { it.id == id }?.let { openDelivery(it, openTab = true) } },
            onComplete = { viewModel.completeDelivery(session, id) })
    }

    if (choosingOrderDestination && state.selectedTab == null) {
        QuickOrderDestinationDialog(
            tabs = state.tabs,
            canOpenTabs = "tab.open" in session.capabilities,
            busy = state.loading || state.submitting || state.pendingTableService != null,
            onSelect = { tabId -> choosingOrderDestination = false; viewModel.selectTab(session, tabId) },
            onNewTab = { choosingOrderDestination = false; openingTab = true },
            onDismiss = { choosingOrderDestination = false },
        )
    }

    if (adjustingPricing) state.selectedTab?.let { selectedTab ->
        PricingDialog(session, selectedTab.summary, viewModel,
            onDismiss = { adjustingPricing = false })
    }

    if (operatingTab) TabOperationsDialog(session, state,
        onDismiss = { operatingTab = false },
        onPreview = { viewModel.previewTabOperation(session, it) },
        onCommit = { viewModel.commitTabOperation(session, it) },
        onEdit = viewModel::clearOperationPreview,
        onRefresh = { viewModel.loadTabOperations(session) })

    if (openingTab) {
        OpenTabDialog(
            busy = state.submitting,
            customers = state.customers,
            message = state.errorMessage,
            onSearch = { viewModel.searchCustomers(session, it) },
            onDismiss = { openingTab = false },
            onOpen = { label, customerId ->
                viewModel.openTab(session, label, customerId)
                openingTab = false
            },
        )
    }
    if (takingPayment && state.selectedTab != null) {
        PaymentDialog(
            tab = state.selectedTab.summary,
            cashPoints = state.cashPoints,
            busy = state.submitting,
            pixEnabled = state.pixEnabled,
            tapSimulationEnabled = state.tapSimulationEnabled,
            onCheckPix = {
                viewModel.reconcilePix(session)
                viewingIntegrated = true
                takingPayment = false
            },
            onDismiss = { takingPayment = false },
            onPay = { amount, method, cashPointId ->
                viewModel.collectPayment(session, amount, method, cashPointId)
                takingPayment = false
            },
        )
    }
    if (viewingIntegrated && !state.submitting && state.integratedPayment != null) {
        com.rodada.attendance.payments.IntegratedPaymentPanel(
            state.integratedPayment, state.submitting,
            onCheck = { viewModel.reconcilePix(session) },
            onDismiss = { viewingIntegrated = false },
        )
    }
    if (resolvingLimit && state.selectedTab != null) {
        LimitResolutionDialog(
            tab = state.selectedTab.summary,
            canApprove = "tab.limit.override" in session.capabilities,
            busy = state.submitting || state.connectivity != ConnectivityState.ONLINE,
            message = state.errorMessage ?: state.noticeMessage,
            onDismiss = { resolvingLimit = false },
            onSubmit = { amount, reason, pin, expiry, key ->
                viewModel.resolveLimit(session, amount, reason, pin, expiry, key)
            },
        )
    }
    correctionItem?.let { item ->
        CorrectionDialog(
            item = item,
            products = state.products,
            busy = state.submitting,
            onDismiss = { correctionItemId = null },
            onSubmit = { command, pin -> viewModel.submitCorrection(session, command, pin) },
        )
    }
    refundTarget?.let { target ->
        val tab = state.selectedTab
        if (tab != null) {
            RefundDialog(
                target = target,
                payments = tab.payments,
                cashPoints = state.cashPoints,
                busy = state.submitting,
                onDismiss = { refundTarget = null },
                onSubmit = { command, pin -> viewModel.submitRefund(session, command, pin) },
            )
        }
    }
    state.errorMessage?.let { MessageDialog("Atenção", it, viewModel::dismissMessage) }
    state.tapPhase?.takeIf { state.submitting }?.let { MessageDialog("Simulação de aproximação", it) {} }
    state.noticeMessage?.let { MessageDialog("Rodada", it, viewModel::dismissMessage) }
}

/**
 * The central Pedir action picks an existing operational Tab before any order mutation.
 * Opening a new Tab remains an explicit, separate action.
 */
@Composable
internal fun QuickOrderDestinationDialog(
    tabs: List<TabSummary>,
    canOpenTabs: Boolean,
    busy: Boolean,
    onSelect: (String) -> Unit,
    onNewTab: () -> Unit,
    onDismiss: () -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }
    val choices = tabs.filter { it.state in setOf("OPEN", "REQUIRES_ACTION") && it.matchesOperationalQuery(query.trim()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Pedir · escolha a comanda") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(query, { query = it }, label = { Text("Buscar comanda ou mesa") },
                    modifier = Modifier.fillMaxWidth(), singleLine = true)
                Column(Modifier.heightIn(max = 360.dp).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (choices.isEmpty()) Text("Nenhuma comanda aberta corresponde à busca.")
                    choices.forEach { tab ->
                        OutlinedButton(onClick = { onSelect(tab.id) }, enabled = !busy,
                            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("quick-order-tab-${tab.id}")) {
                            Text("${tab.operationalLabel()} · ${tab.operationalSubtitle()}")
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (canOpenTabs) Button(onClick = onNewTab, enabled = !busy) { Text("Nova comanda sem mesa") }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

private enum class FrontlineSection(val label: String) { NOW("Agora"), TABS("Comandas"), TABLES("Mesas"), CASH("Caixa") }

@Composable
private fun FrontlineNavigation(section: FrontlineSection, onSelect: (FrontlineSection) -> Unit, onOrder: () -> Unit, busy: Boolean) {
    com.rodada.attendance.ui.AttendanceNavigation(
        selected = com.rodada.attendance.ui.AttendanceDestination.valueOf(section.name),
        busy = busy,
        onSelect = { onSelect(FrontlineSection.valueOf(it.name)) },
        onOrder = onOrder,
    )
}

@Composable
private fun Header(
    session: StoredSession,
    connectivity: ConnectivityState,
    busy: Boolean,
    peak: Boolean,
    onTogglePeak: () -> Unit,
    onOpenAccount: () -> Unit,
    onRefresh: () -> Unit,
) {
    com.rodada.attendance.ui.AttendanceHeader(
        venueName = session.venueName, staffName = session.staffDisplayName, connectivity = connectivity, busy = busy, peak = peak,
        onTogglePeak = onTogglePeak, onOpenAccount = onOpenAccount, onRefresh = onRefresh,
    )
}

@Composable
internal fun TabList(
    state: OperationsUiState,
    showDeliveries: Boolean,
    peak: Boolean = false,
    choosingOrderDestination: Boolean = false,
    onOpenTab: () -> Unit,
    onSelect: (String) -> Unit,
    onCompleteDelivery: (String) -> Unit,
    staffId: String = "",
    onViewTable: (String) -> Unit = {},
    onClaimTable: (TableOccupancy) -> Unit = {},
    canClaimTable: Boolean = false,
    onServiceAction: (String, Boolean) -> Unit = { _, _ -> },
    onOpenRecovery: (String) -> Unit = {},
    onCheckOrders: () -> Unit = {},
) {
    val visibleTabs = tabsForSurface(state.tabs, showDeliveries).filter { !choosingOrderDestination || it.state != "CLOSED" }
    var queue by rememberSaveable { mutableStateOf(NowQueue.READY) }
    val listState = rememberLazyListState()
    LaunchedEffect(peak, state.recoveryDeliveryTaskId) { if (peak || state.recoveryDeliveryTaskId != null) queue = NowQueue.READY }
    LaunchedEffect(queue) { listState.scrollToItem(0) }
    LazyColumn(state = listState, modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(0.dp)) {
        if (showDeliveries) {
            val attention = state.tables.filter { it.activeOccupancy?.serviceAttention in setOf("UNASSIGNED_GUEST_ORDER", "UNASSIGNED_READY") }
                .sortedWith(compareByDescending<TableSummary> { it.activeOccupancy?.serviceAttention == "UNASSIGNED_READY" }.thenBy { it.activeOccupancy?.oldestGuestOrderAt })
            items(attention, key = { "attention-${it.activeOccupancy!!.id}" }) { table ->
                Column(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    val occupancy = table.activeOccupancy!!
                    Text("Mesa ${table.label} · ${table.zone?.label.orEmpty()}", style = MaterialTheme.typography.titleMedium)
                    Text("Pedido via QR · Sem responsável", fontWeight = FontWeight.Bold, color = RodadaVisual.Amber)
                    Text("${occupancy.guestOrderCount} pedido(s) · ${if (occupancy.serviceAttention == "UNASSIGNED_READY") "Pedido pronto" else "Confirmado"}")
                    Text(serviceOrderAgeLabel(occupancy.oldestGuestOrderAt))
                    OutlinedButton(onClick = { onViewTable(table.id) }, enabled = !state.submitting && state.pendingTableService == null, modifier = Modifier.fillMaxWidth()) { Text("Ver mesa ${table.label}") }
                    if (canClaimTable && table.tableServiceEnabled) Button(onClick = { onClaimTable(occupancy) }, enabled = !state.submitting && state.pendingTableService == null, modifier = Modifier.fillMaxWidth()) { Text("Assumir atendimento") }
                }
            }
        }
        if (!showDeliveries) item {
            Column(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (choosingOrderDestination) Text("Escolha a comanda para pedir", style = MaterialTheme.typography.titleLarge)
                OutlinedButton(onClick = onOpenTab, enabled = !state.loading && !state.submitting, modifier = Modifier.fillMaxWidth()) { Text("Nova comanda") }
            }
        }
        if (showDeliveries) item {
            Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
                Text(if (peak) "MODO PICO" else "AGORA", style = MaterialTheme.typography.headlineLarge)
                if (peak) Text("Prontos primeiro · chamadas e pendências nos filtros", color = RodadaVisual.Amber)
                Text("Escolha a fila de trabalho.", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
            }
            NowQueueNavigation(queue, nowQueueCounts(state), onSelect = { queue = it })
            HorizontalDivider(color = RodadaVisual.Border)
        }
        if (showDeliveries && queue == NowQueue.PENDING) item { RecoveryPanel(state, onOpenRecovery, onCheckOrders) }
        if (showDeliveries && queue == NowQueue.CALLS) item {
            Column(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("CHAMADAS DE ATENDIMENTO", style = MaterialTheme.typography.titleMedium)
                state.serviceRequestsError?.let { Text(it, color = RodadaVisual.Amber) }
                if (!state.serviceRequestsFresh && state.serviceRequestsError == null) Text("Chamadas ainda não consultadas.")
                if (state.serviceRequestsFresh && state.serviceRequests.isEmpty()) Text("Nenhuma chamada aberta.")
                state.pendingServiceAction?.let { pending ->
                    Text("Resultado não confirmado. Verifique a mesma ação.", color = RodadaVisual.Amber)
                    OutlinedButton(onClick = { onServiceAction(pending.taskId, pending.complete) }, enabled = !state.loading && !state.submitting && state.serviceRequestsFresh) { Text("Verificar mesma chamada") }
                }
            }
        }
        if (showDeliveries && queue == NowQueue.CALLS) items(state.serviceRequests, key = { "service-${it.id}" }) { task ->
            Column(modifier = Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${task.title} · ${task.destination}", style = MaterialTheme.typography.titleLarge)
                Text(task.ageLabel, color = RodadaVisual.Muted)
                Text(task.responsibility(staffId))
                val enabled = !state.loading && !state.submitting && state.serviceRequestsFresh && !task.belongsToOther(staffId) && state.pendingServiceAction == null
                if (task.claimedById != staffId) OutlinedButton(onClick = { onServiceAction(task.id, false) }, enabled = enabled, modifier = Modifier.fillMaxWidth()) { Text("Assumir chamada") }
                Button(onClick = { onServiceAction(task.id, true) }, enabled = enabled, modifier = Modifier.fillMaxWidth()) { Text("Concluir chamada") }
            }
            HorizontalDivider(color = RodadaVisual.Border)
        }
        if (showDeliveries && queue == NowQueue.READY && !state.loading && state.lastSyncedAtMillis != null && state.deliveryTasks.isEmpty()) item { Text("Nenhuma entrega aguardando no último estado consultado.", modifier = Modifier.padding(20.dp)) }
        if (showDeliveries && queue == NowQueue.READY) items(state.deliveryTasks.sortedByDescending { it.ageSeconds }, key = { it.id }) { task ->
            Column(modifier = Modifier.fillMaxWidth().heightIn(min = 112.dp)) {
                Column(modifier = Modifier.background(RodadaVisual.Control).padding(horizontal = 10.dp, vertical = 20.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("PRONTO", color = RodadaVisual.Success, style = MaterialTheme.typography.labelSmall)
                    Text(deliveryAge(task.ageSeconds), fontFamily = RodadaVisual.Number, fontWeight = FontWeight.ExtraBold, color = RodadaVisual.Success)
                }
                Column(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    if (state.recoveryDeliveryTaskId == task.id) Text("Entrega pendente · operação original", color = RodadaVisual.Amber)
                    Text("${task.quantity} ${task.productName}", style = MaterialTheme.typography.titleLarge)
                    Text(task.destinationLabel.ifBlank { "Destino não informado" }, style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                    if (task.tabLabel.isNotBlank()) Text(task.tabLabel, color = RodadaVisual.Muted, style = MaterialTheme.typography.bodySmall)
                }
                Button(onClick = { onCompleteDelivery(task.id) }, enabled = !state.submitting, modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp).heightIn(min = 48.dp)) { Text("ENTREGUE") }
            }
            HorizontalDivider(color = RodadaVisual.Border)
        }
        if (!peak && (!showDeliveries || queue == NowQueue.READY)) item { Text(if (showDeliveries) "CONTAS ABERTAS" else "CONTAS", modifier = Modifier.padding(20.dp), style = MaterialTheme.typography.labelLarge, color = RodadaVisual.Muted) }
        if (state.loading && visibleTabs.isEmpty()) item { LoadingRow() }
        if (!peak && (!showDeliveries || queue == NowQueue.READY) && !state.loading && visibleTabs.isEmpty()) item { Text("Nenhuma comanda aberta neste dispositivo.", modifier = Modifier.padding(20.dp)) }
        if (!peak && (!showDeliveries || queue == NowQueue.READY)) items(visibleTabs, key = { it.id }) { tab ->
            TextButton(onClick = { onSelect(tab.id) }, modifier = Modifier.fillMaxWidth().heightIn(min = 88.dp), enabled = !state.loading && !state.submitting) {
                Column(modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(tab.operationalLabel(), style = MaterialTheme.typography.headlineSmall, color = RodadaVisual.Paper)
                    Text(tab.operationalSubtitle(), style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                    Text("Comanda ${tab.id.take(8)}", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                    Text("${tab.stateLabel()} · ${formatCents(tab.exposureCents)} em aberto", fontFamily = RodadaVisual.Number, color = if (tab.consumptionBlocked) RodadaVisual.Danger else RodadaVisual.Money)
                }
            }
            HorizontalDivider(color = RodadaVisual.Border)
        }
        item { Spacer(Modifier.height(20.dp)) }
    }
}

private fun deliveryAge(seconds: Long): String =
    if (seconds < 60) "agora" else "${seconds / 60} min"

@Composable
internal fun TabWorkspace(
    state: OperationsUiState,
    tab: TabDetail,
    onBack: () -> Unit,
    onAdd: (Product, Customization) -> Unit,
    onEdit: (String, Customization) -> Unit,
    onQuantity: (String, Int) -> Unit,
    onConfirmOrder: () -> Unit,
    onPay: () -> Unit,
    onClose: () -> Unit,
    onAdjustPricing: () -> Unit,
    onOperations: () -> Unit,
    onResolveLimit: () -> Unit,
    onCorrectItem: (OrderItem) -> Unit,
    onRefundPayment: (TabPayment) -> Unit,
    onSettleCorrection: (RefundRequiredCorrection) -> Unit,
    onRepeatOrder: (RepeatOrderReview, Map<String, Int>) -> Unit = { _, _ -> },
    requestedSection: String? = null,
    onRequestedSectionConsumed: () -> Unit = {},
    onAddQuantity: (Product, Customization, Int) -> Unit = { product, selection, quantity -> repeat(quantity) { onAdd(product, selection) } },
) {
    var workspaceSection by rememberSaveable(tab.summary.id) { mutableStateOf(if (tab.summary.state == "CLOSED") "Conta" else "Cardápio") }
    LaunchedEffect(requestedSection) {
        if (requestedSection != null) {
            workspaceSection = requestedSection
            onRequestedSectionConsumed()
        }
    }
    val reviewingCart = workspaceSection == "Pedido atual"
    val viewingAccount = workspaceSection == "Conta"
    var repeatReview by remember(tab.summary.id) { mutableStateOf<RepeatOrderReview?>(null) }
    val repeatEnabled = !state.loading && !state.submitting && state.orderIntentId == null &&
        state.queuedOrders.none { it.tabId == tab.summary.id } && tab.summary.state != "CLOSED" && state.connectivity == ConnectivityState.ONLINE
    repeatReview?.let { review ->
        val unchanged = tab.orders.firstOrNull { it.id == review.orderId }?.let { reviewRepeatedOrder(it, state.products) == review } == true
        RepeatOrderDialog(review, repeatEnabled && unchanged, { repeatReview = null }) { quantities ->
            repeatReview = null
            onRepeatOrder(review, quantities)
        }
    }
    val catalogScroll = rememberLazyListState()
    val cartScroll = rememberLazyListState()
    var catalogIndex by rememberSaveable(tab.summary.id) { mutableStateOf(0) }
    var catalogOffset by rememberSaveable(tab.summary.id) { mutableStateOf(0) }
    LaunchedEffect(tab.summary.id, reviewingCart) {
        if (!reviewingCart) catalogScroll.scrollToItem(catalogIndex, catalogOffset)
    }
    var configuring by remember(tab.summary.id) { mutableStateOf<Product?>(null) }
    var editing by remember(tab.summary.id) { mutableStateOf<CartLine?>(null) }
    var previous by remember(tab.summary.id) { mutableStateOf<Map<String, Customization>>(emptyMap()) }
    configuring?.let { selected ->
        val current = state.products.firstOrNull { it.id == selected.id } ?: selected
        ProductCustomizationSheet(current, editing?.customization ?: previous[current.id] ?: current.defaults(), onDismiss = { configuring = null; editing = null },
            validationQuantity = editing?.quantity,
            capacity = { selection -> draftQuantityCapacity(state.cart.filterNot { it.lineId == editing?.lineId }, current.id, selection) },
            locked = !state.canLeaveTabContext()) { selection ->
            if (editing != null) onEdit(editing!!.lineId, selection) else onAdd(current, selection)
            previous = previous + (current.id to selection); configuring = null; editing = null
        }
    }
    val currentCart = state.cart.map { line -> line.copy(product = state.products.firstOrNull { it.id == line.product.id } ?: line.product.copy(active = false)) }
    val cartTotal = currentCart.sumOf { it.unitPriceCents * it.quantity }

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
        TextButton(onClick = onBack, enabled = state.canLeaveTabContext(), modifier = Modifier.heightIn(min = 48.dp)) { Text("← Mesas e comandas") }
        Text(tab.summary.operationalLabel(), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        Text(tab.summary.operationalSubtitle(), style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
        Text(state.connectivity.label(), style = MaterialTheme.typography.labelSmall)
        val taskRows = if (androidx.compose.ui.platform.LocalDensity.current.fontScale > 1.3f) listOf(listOf("Cardápio", "Conta"), listOf("Pedido atual")) else listOf(listOf("Cardápio", "Pedido atual", "Conta"))
        taskRows.forEach { destinations ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                destinations.forEach { destination ->
                    OutlinedButton(onClick = { workspaceSection = destination }, modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("workspace-$destination"),
                        enabled = !state.loading && !state.submitting) { Text(if (workspaceSection == destination) "• $destination" else destination, style = MaterialTheme.typography.bodySmall, textAlign = androidx.compose.ui.text.style.TextAlign.Center) }
                }
            }
        }
        key(tab.summary.id, workspaceSection) {
            LazyColumn(
                modifier = Modifier.weight(1f).fillMaxWidth().testTag("workspace-list"),
                state = if (reviewingCart) cartScroll else catalogScroll,
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                if (reviewingCart) {
                    item {
                        Text(tab.summary.displayLabel, style = MaterialTheme.typography.titleLarge)
                        if (tab.summary.consumptionBlocked || tab.summary.limitWarning) {
                            Text(if (tab.summary.consumptionBlocked) "Limite atingido. Receba um parcial ou solicite aprovação para continuar." else "Comanda próxima do limite.", color = MaterialTheme.colorScheme.error)
                        }
                        if (tab.summary.serviceAssessmentStale) Text("Atualize a taxa de serviço no caixa antes de receber.")
                        OrderCart(currentCart, cartTotal, state.submitting, state.orderIntentId != null, onQuantity, onConfirmOrder) { line -> editing = line; configuring = line.product }
                    }
                }
                if (viewingAccount) {
                    item {
                        BalanceCard(tab.summary, onPay, onClose, state.submitting, state.connectivity == ConnectivityState.ONLINE)
                        OutlinedButton(onClick = onAdjustPricing, enabled = !state.submitting && state.connectivity == ConnectivityState.ONLINE, modifier = Modifier.fillMaxWidth()) { Text("Ajustar conta / serviço") }
                        OutlinedButton(onClick = onOperations, enabled = !state.submitting) { Text("Operações da comanda") }
                        if (tab.summary.consumptionBlocked || tab.summary.limitWarning) Text(if (tab.summary.consumptionBlocked) "Limite atingido. Receba um parcial ou solicite aprovação para continuar." else "Comanda próxima do limite.", color = MaterialTheme.colorScheme.error)
                        if (tab.summary.state != "CLOSED") OutlinedButton(onClick = onResolveLimit, enabled = !state.submitting && state.connectivity == ConnectivityState.ONLINE) { Text("Solicitar / aprovar limite") }
                    }
                }
                if (!reviewingCart && !viewingAccount) {
                    item {
                        CategoryCatalog(state, tab.summary.id, tab.summary.state in setOf("CLOSED", "CANCELLED"),
                            onAddQuantity, onReview = { workspaceSection = "Pedido atual" })
                    }
                }
                if (viewingAccount && tab.orders.isNotEmpty()) {
                    item { Text("Pedidos confirmados", style = MaterialTheme.typography.titleLarge) }
                    items(tab.orders, key = { it.id }) { order ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text("Pedido", fontWeight = FontWeight.Bold)
                                OutlinedButton(onClick = { repeatReview = reviewRepeatedOrder(order, state.products) }, enabled = repeatEnabled) { Text("Mais uma rodada") }
                                order.items.forEach { item ->
                                    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text("${item.quantity}× ${item.productName} · ${formatCents(item.lineTotalCents)}")
                                            if (item.customizationText.isNotBlank()) Text(item.customizationText)
                                            Text(itemStateLabel(item.state), style = MaterialTheme.typography.bodySmall)
                                        }
                                        // A cancelled line is retained as operational history, not an
                                        // actionable item.  Keeping a disabled "Corrigir" beside it made
                                        // the next valid action ambiguous during a live shift.
                                        if (item.state != "CANCELLED") {
                                            OutlinedButton(
                                                onClick = { onCorrectItem(item) },
                                                enabled = !state.submitting && tab.summary.state != "CLOSED",
                                            ) { Text("Corrigir") }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if (viewingAccount && tab.payments.isNotEmpty()) {
                    item { Text("Pagamentos", style = MaterialTheme.typography.titleLarge) }
                    items(tab.payments, key = { it.id }) { payment ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                Text((if (payment.simulated) "SIMULAÇÃO · " else "") + paymentMethodLabel(payment.method), fontWeight = FontWeight.Bold)
                                Text("${formatCents(payment.amountCents)} · ${paymentStatusLabel(payment.status)}")
                                if (payment.refundedCents > 0) Text("Já estornado: ${formatCents(payment.refundedCents)}")
                                val available = (payment.amountCents - payment.refundedCents).coerceAtLeast(0)
                                if (available > 0) {
                                    OutlinedButton(
                                        onClick = { onRefundPayment(payment) },
                                        enabled = !state.submitting,
                                        modifier = Modifier.fillMaxWidth(),
                                    ) { Text("Estornar ${formatCents(available)}") }
                                }
                            }
                        }
                    }
                }
                if (viewingAccount && tab.refundRequiredCorrections.isNotEmpty()) {
                    item { Text("Estorno necessário", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.error) }
                    items(tab.refundRequiredCorrections, key = { it.id }) { correction ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                Text(correction.itemName, fontWeight = FontWeight.Bold)
                                Text("A correção ainda precisa de ${formatCents(correction.refundRequiredCents)} em estorno.")
                                OutlinedButton(
                                    onClick = { onSettleCorrection(correction) },
                                    enabled = tab.payments.any { it.amountCents > it.refundedCents } && !state.submitting,
                                    modifier = Modifier.fillMaxWidth(),
                                ) { Text("Resolver estorno") }
                            }
                        }
                    }
                }
                item { Spacer(Modifier.height(24.dp)) }
            }
        }
        OutlinedButton(
            onClick = {
                if (!reviewingCart) {
                    catalogIndex = catalogScroll.firstVisibleItemIndex
                    catalogOffset = catalogScroll.firstVisibleItemScrollOffset
                }
                workspaceSection = if (reviewingCart) "Cardápio" else "Pedido atual"
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            val count = currentCart.sumOf { it.quantity }
            Text(if (reviewingCart) "Voltar ao catálogo" else "Ver pedido atual · $count ${if (count == 1) "item" else "itens"} · ${formatCents(cartTotal)}")
        }
    }
}

@Composable
internal fun BalanceCard(
    tab: TabSummary,
    onPay: () -> Unit,
    onClose: () -> Unit,
    busy: Boolean,
    canInitiatePayment: Boolean,
) {
    var expanded by rememberSaveable(tab.id) { mutableStateOf(false) }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Saldo em aberto", style = MaterialTheme.typography.labelLarge)
            Text(formatCents(tab.exposureCents), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            TextButton(onClick = { expanded = !expanded }) {
                Text(if (expanded) "Recolher detalhes da conta" else "Ver detalhes da conta")
            }
            if (expanded) {
                Text("Subtotal original ${formatCents(tab.originalSubtotalCents)}")
                Text("Descontos ${formatCents(tab.discountsCents)} · cortesias ${formatCents(tab.courtesyCents)}")
                if (tab.correctionsCents != 0L) Text("Correções ${formatCents(tab.correctionsCents)}")
                Text("Taxa de serviço ${formatCents(tab.serviceChargeCents)}")
                Text("Total a pagar ${formatCents(tab.payableCents)}")
                Text("Pagamentos recebidos ${formatCents(tab.paymentsCents)} · estornos ${formatCents(tab.refundsCents)}")
                if (tab.transfersCents != 0L) Text("Responsabilidade transferida: ${formatCents(tab.transfersCents)}")
                Text("Limite ${formatCents(tab.effectiveLimitCents)} · disponível ${formatCents(tab.remainingCapacityCents)}")
                tab.percentageUsed?.let { Text("$it% do limite utilizado") }
            }
            if (tab.serviceAssessmentStale) Text("Atualize a taxa de serviço no caixa antes de receber.")
            if (tab.actionReasons.any { it != "SPENDING_LIMIT" }) Text("Há outras ações pendentes na comanda.")
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = onPay, enabled = !tab.serviceAssessmentStale && tab.exposureCents > 0 && tab.state != "CLOSED" && !busy && canInitiatePayment, modifier = Modifier.weight(1f)) {
                    Text("Pagar")
                }
                OutlinedButton(onClick = onClose, enabled = !tab.serviceAssessmentStale && tab.exposureCents == 0L && tab.state != "CLOSED" && !busy, modifier = Modifier.weight(1f)) {
                    Text(if (tab.state == "CLOSED") "Fechada" else "Fechar")
                }
            }
        }
    }
}

@Composable
internal fun LimitResolutionDialog(
    tab: TabSummary,
    canApprove: Boolean,
    busy: Boolean,
    message: String?,
    onDismiss: () -> Unit,
    onSubmit: (Long?, String, String, String, String) -> Unit,
) {
    var amount by rememberSaveable(tab.id) { mutableStateOf("") }
    var reason by rememberSaveable(tab.id) { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    val key = rememberSaveable(tab.id) { UUID.randomUUID().toString() }
    val expiry = rememberSaveable(tab.id) { Instant.now().plusSeconds(3600).toString() }
    var submitted by rememberSaveable(tab.id) { mutableStateOf(false) }
    val cents = parseCents(amount)
    AlertDialog(
        onDismissRequest = { if (!busy) onDismiss() },
        title = { Text(if (canApprove) "Aprovar limite temporário" else "Solicitar aprovação") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Em aberto ${formatCents(tab.exposureCents)} · limite ${formatCents(tab.effectiveLimitCents)}")
                message?.let { Text(it) }
                if (canApprove) {
                    Text("Aprovação operacional válida por uma hora. Não registra pagamento ou garantia financeira.")
                    OutlinedTextField(value = amount, onValueChange = { amount = it }, enabled = !busy && !submitted, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), label = { Text("Novo limite total (R$)") })
                    if (amount.isNotBlank() && (cents == null || cents <= tab.effectiveLimitCents)) Text("Informe um limite válido maior que ${formatCents(tab.effectiveLimitCents)}.", color = MaterialTheme.colorScheme.error)
                    OutlinedTextField(value = pin, onValueChange = { pin = it }, enabled = !busy, label = { Text("Seu PIN") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword), visualTransformation = PasswordVisualTransformation())
                } else Text("A gerência receberá a solicitação. Para pagar, volte à comanda e toque em Pagar; um operador autorizado confirma o recebimento.")
                OutlinedTextField(value = reason, onValueChange = { reason = it.take(240) }, enabled = !busy && !submitted, label = { Text("Motivo") })
                if (submitted) Text("Confira a mensagem na comanda. Em caso de perda de conexão, repita esta mesma solicitação após atualizar.")
            }
        },
        confirmButton = {
            TextButton(enabled = !busy && reason.isNotBlank() && (!canApprove || (pin.isNotBlank() && cents != null && cents > tab.effectiveLimitCents)), onClick = {
                submitted = true
                onSubmit(if (canApprove) cents else null, reason, pin, expiry, key)
                pin = ""
            }) { Text(if (busy) "Confirmando…" else if (canApprove) "Aprovar" else "Solicitar") }
        },
        dismissButton = { TextButton(enabled = !busy, onClick = onDismiss) { Text("Voltar à comanda") } },
    )
}

@Composable
private fun OrderCart(
    cart: List<CartLine>,
    total: Long,
    busy: Boolean,
    locked: Boolean,
    onQuantity: (String, Int) -> Unit,
    onConfirm: () -> Unit,
    onEdit: (CartLine) -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Carrinho", style = MaterialTheme.typography.titleLarge)
            if (cart.isEmpty()) Text("Toque em um produto para adicionar.")
            if (locked) Text("Este pedido está aguardando reconciliação; confirme novamente para repetir a mesma intenção.")
            cart.forEach { line ->
                Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(line.product.name, fontWeight = FontWeight.SemiBold)
                        Text("${formatCents(line.unitPriceCents)} cada")
                        Text(line.product.configurationText(line.customization))
                        if (!line.product.active || line.product.availability != "AVAILABLE" || line.product.customizationError(line.customization) != null) Text("Item desatualizado. Remova e selecione novamente.", color = MaterialTheme.colorScheme.error)
                    }
                    Column {
                        TextButton(onClick = { onEdit(line) }, enabled = !busy && !locked) { Text("Editar") }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            TextButton(onClick = { onQuantity(line.lineId, -1) }, enabled = !busy && !locked) { Text("−") }
                            Text("${line.quantity}")
                            TextButton(onClick = { onQuantity(line.lineId, 1) }, enabled = !busy && !locked && line.product.active && line.product.availability == "AVAILABLE" && draftQuantityCapacity(cart, line.product.id, line.customization) > 0) { Text("+") }
                        }
                    }
                }
            }
            if (cart.isNotEmpty()) {
                Text("Total: ${formatCents(total)}", fontWeight = FontWeight.Bold)
                Button(onClick = onConfirm, enabled = !busy && (locked || cart.all { it.product.active && it.product.availability == "AVAILABLE" && it.product.customizationError(it.customization) == null }), modifier = Modifier.fillMaxWidth()) { Text("Confirmar pedido") }
            }
        }
    }
}

@Composable
internal fun OpenTabDialog(busy: Boolean, customers: List<CustomerSummary>, message: String?, onSearch: (String) -> Unit,
                          onDismiss: () -> Unit, onOpen: (String, String?) -> Unit) {
    var label by rememberSaveable { mutableStateOf("") }
    var customerId by rememberSaveable { mutableStateOf<String?>(null) }
    var searched by rememberSaveable { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Nova comanda · Sem mesa") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = label, onValueChange = { label = it.take(120); customerId = null; searched = false }, enabled = !busy, label = { Text("Nome ou apelido") }, modifier = Modifier.fillMaxWidth())
                TextButton(enabled = !busy && label.isNotBlank(), onClick = { searched = true; onSearch(label) }) { Text(if (busy) "Buscando…" else "Buscar cliente existente") }
                if (searched && !busy) {
                    if (customers.isEmpty()) Text("Nenhum cliente encontrado. Você pode abrir sem cadastro.")
                    customers.take(5).forEach { customer ->
                        OutlinedButton(enabled = !busy, onClick = { customerId = customer.id; label = customer.displayName.take(120) }) {
                            Text("${customer.displayName} · ${customer.kind}${if (customerId == customer.id) " ✓" else ""}")
                        }
                    }
                }
                message?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = { Button(onClick = { onOpen(label.trim(), customerId) }, enabled = !busy && label.isNotBlank()) { Text("Abrir") } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
internal fun PaymentDialog(
    tab: TabSummary,
    cashPoints: List<CashPoint>,
    busy: Boolean,
    pixEnabled: Boolean,
    tapSimulationEnabled: Boolean,
    onCheckPix: () -> Unit,
    onDismiss: () -> Unit,
    onPay: (Long, PaymentMethod, String?) -> Unit,
) {
    var rawAmount by rememberSaveable(tab.id) { mutableStateOf("${tab.exposureCents / 100},${(tab.exposureCents % 100).toString().padStart(2, '0')}") }
    var method by rememberSaveable(tab.id) { mutableStateOf(PaymentMethod.CASH) }
    var cashPointId by rememberSaveable(tab.id) {
        mutableStateOf(cashPoints.firstOrNull { it.activeShiftId != null }?.id.orEmpty())
    }
    val amount = parseCents(rawAmount)
    val valid = amount != null && amount > 0 && amount <= tab.exposureCents
    val expanded = LocalConfiguration.current.fontScale > 1.3f
    @Composable fun ConfirmPayment(modifier: Modifier = Modifier) {
        Button(
            onClick = { onPay(amount ?: 0, method, cashPointId.ifBlank { null }) },
            enabled = valid && !busy && (method != PaymentMethod.CASH || cashPointId.isNotBlank()),
            modifier = modifier,
        ) { Text(if (method == PaymentMethod.PIX) "Gerar cobrança Pix" else "Confirmar pagamento") }
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Pagar comanda") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Subtotal original: ${formatCents(tab.originalSubtotalCents)}")
                Text("Descontos: ${formatCents(tab.discountsCents)} · Cortesias: ${formatCents(tab.courtesyCents)}")
                Text("Serviço: ${formatCents(tab.serviceChargeCents)} · Total: ${formatCents(tab.payableCents)}")
                Text("Recebido: ${formatCents(tab.paymentsCents)} · Estornado: ${formatCents(tab.refundsCents)}")
                Text("Saldo restante: ${formatCents(tab.exposureCents)}")
                OutlinedTextField(value = rawAmount, onValueChange = { rawAmount = it }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), label = { Text("Valor") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                PaymentMethod.entries.filter { (it != PaymentMethod.PIX || pixEnabled) && (it !in setOf(PaymentMethod.TAP_CREDIT, PaymentMethod.TAP_DEBIT) || tapSimulationEnabled) }.forEach { candidate ->
                    OutlinedButton(onClick = { method = candidate }, modifier = Modifier.fillMaxWidth(), enabled = !busy) {
                        Text(if (method == candidate) "✓ ${candidate.label}" else candidate.label)
                    }
                }
                if (method == PaymentMethod.CASH) {
                    Text("Caixa aberto", style = MaterialTheme.typography.labelLarge)
                    cashPoints.filter { it.activeShiftId != null }.forEach { point ->
                        OutlinedButton(onClick = { cashPointId = point.id }, modifier = Modifier.fillMaxWidth(), enabled = !busy) {
                            Text(if (cashPointId == point.id) "✓ ${point.label}" else point.label)
                        }
                    }
                    if (cashPoints.none { it.activeShiftId != null }) {
                        Text("Abra ou selecione um caixa com turno ativo antes de receber dinheiro.", color = MaterialTheme.colorScheme.error)
                    }
                }
                if (pixEnabled || tapSimulationEnabled) TextButton(onClick = onCheckPix, enabled = !busy) { Text("Verificar pagamento existente") }
                Text(if (tapSimulationEnabled) "SIMULAÇÃO de aproximação. Não recebe dinheiro e não exige cartão." else "Aproximação SumUp aguarda SDK e ativação. Terminal externo disponível.")
                if (!valid) Text("Informe um valor entre R$ 0,01 e o saldo em aberto.", color = MaterialTheme.colorScheme.error)
                if (method == PaymentMethod.EXTERNAL_TERMINAL) Text("Registre somente após confirmação no terminal/provedor. O app não confirma pagamentos externos sozinho.")
            }
        },
        confirmButton = {
            if (expanded) Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ConfirmPayment(Modifier.fillMaxWidth())
                TextButton(onClick = onDismiss, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp)) { Text("Cancelar") }
            } else ConfirmPayment()
        },
        dismissButton = { if (!expanded) TextButton(onClick = onDismiss, enabled = !busy, modifier = Modifier.heightIn(min = 44.dp)) { Text("Cancelar") } },
    )
}

/** A correction dialog deliberately collects an operational reason but leaves policy to the API. */
@Composable
private fun CorrectionDialog(
    item: OrderItem,
    products: List<Product>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (CorrectionCommand, String?) -> Unit,
) {
    val availableActions = correctionActionsFor(item.state)
    var action by remember(item.id, item.state) { mutableStateOf(availableActions.firstOrNull() ?: CorrectionAction.CANCEL) }
    var reason by remember(item.id) { mutableStateOf("") }
    var pin by remember(item.id) { mutableStateOf("") }
    var replacementId by remember(item.id) { mutableStateOf("") }
    // Retain this key while the dialog remains open. A timeout retry is therefore the same command.
    val idempotencyKey = remember(item.id, action, replacementId) { UUID.randomUUID().toString() }
    // The canonical post-production command intentionally rejects remake and
    // replacement before work begins. Do not offer an action that the server
    // can never accept for a NEW/ACCEPTED item.
    val replacementProducts = products.filter { it.active && it.availability == "AVAILABLE" && it.id != replacementId }
    val requiresReauth = CorrectionCommand(item.id, item.state, action, "OPERATIONAL", reason, idempotencyKey, replacementId.ifBlank { null }).requiresPostProductionEndpoint()
    val replacementValid = action != CorrectionAction.REPLACEMENT || replacementId.isNotBlank()
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Corrigir ${item.productName}") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${item.quantity}× ${formatCents(item.lineTotalCents)} · ${itemStateLabel(item.state)}")
                availableActions.forEach { candidate ->
                    OutlinedButton(onClick = { action = candidate }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                        Text(if (action == candidate) "✓ ${candidate.label}" else candidate.label)
                    }
                }
                if (action == CorrectionAction.REPLACEMENT) {
                    Text("Novo item", style = MaterialTheme.typography.labelLarge)
                    replacementProducts.forEach { product ->
                        OutlinedButton(onClick = { replacementId = product.id }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text(if (replacementId == product.id) "✓ ${product.name} · ${formatCents(product.priceCents)}" else "${product.name} · ${formatCents(product.priceCents)}")
                        }
                    }
                    if (replacementProducts.isEmpty()) Text("Não há item disponível para troca.", color = MaterialTheme.colorScheme.error)
                }
                OutlinedTextField(
                    value = reason,
                    onValueChange = { reason = it },
                    label = { Text("Motivo") },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !busy,
                )
                if (requiresReauth) {
                    Text("Esta ação preserva o histórico de produção e requer a confirmação do operador autorizado.", color = MaterialTheme.colorScheme.error)
                    OutlinedTextField(
                        value = pin,
                        onValueChange = { pin = it },
                        label = { Text("Seu PIN") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        enabled = !busy,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword), visualTransformation = PasswordVisualTransformation(),
                    )
                } else {
                    Text("O valor será atualizado pela comanda canônica.", style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    onSubmit(
                        CorrectionCommand(
                            itemId = item.id,
                            itemState = item.state,
                            action = action,
                            reasonCode = "OPERATIONAL_CORRECTION",
                            reasonText = reason.trim(),
                            idempotencyKey = idempotencyKey,
                            replacementProductId = replacementId.ifBlank { null },
                        ),
                        pin.takeIf { requiresReauth },
                    )
                    pin = ""
                },
                enabled = !busy && action in availableActions && reason.isNotBlank() && replacementValid && (!requiresReauth || pin.isNotBlank()),
            ) { Text(action.label) }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Voltar") } },
    )
}

internal sealed interface RefundTarget {
    data class Payment(val payment: TabPayment) : RefundTarget
    data class Correction(val correction: RefundRequiredCorrection) : RefundTarget
}

@Composable
internal fun RefundDialog(
    target: RefundTarget,
    payments: List<TabPayment>,
    cashPoints: List<CashPoint>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (RefundCommand, String) -> Unit,
) {
    val eligiblePayments = payments.filter { it.amountCents > it.refundedCents }
    val correctionRequired = (target as? RefundTarget.Correction)?.correction?.refundRequiredCents
    var paymentId by remember(target) {
        mutableStateOf(
            (target as? RefundTarget.Payment)?.payment?.id
                ?: eligiblePayments.firstOrNull { payment ->
                    correctionRequired == null || payment.amountCents - payment.refundedCents >= correctionRequired
                }?.id
                ?: eligiblePayments.firstOrNull()?.id.orEmpty(),
        )
    }
    val selectedPayment = eligiblePayments.firstOrNull { it.id == paymentId }
    val selectedPaymentAvailable = selectedPayment?.let { it.amountCents - it.refundedCents } ?: 0
    val maximum = when (target) {
        is RefundTarget.Payment -> target.payment.amountCents - target.payment.refundedCents
        is RefundTarget.Correction -> target.correction.refundRequiredCents
    }.coerceAtLeast(0)
    var rawAmount by remember(target) { mutableStateOf("${maximum / 100},${(maximum % 100).toString().padStart(2, '0')}") }
    var reason by remember(target) { mutableStateOf("") }
    var pin by remember(target) { mutableStateOf("") }
    var cashPointId by remember(target) { mutableStateOf(cashPoints.firstOrNull { it.activeShiftId != null }?.id.orEmpty()) }
    val key = remember(target, paymentId) { UUID.randomUUID().toString() }
    val amount = parseCents(rawAmount)
    val valid = amount != null && amount > 0 && amount <= maximum && amount <= selectedPaymentAvailable && selectedPayment != null
    val expanded = LocalConfiguration.current.fontScale > 1.3f
    @Composable fun ConfirmRefund(modifier: Modifier = Modifier) {
        Button(
                onClick = {
                    val command = when (target) {
                        is RefundTarget.Payment -> DirectRefundCommand(paymentId, amount ?: 0, reason.trim(), key, cashPointId.ifBlank { null })
                        is RefundTarget.Correction -> SettleCorrectionRefundCommand(target.correction.id, paymentId, amount ?: 0, key, cashPointId.ifBlank { null })
                    }
                    onSubmit(command, pin)
                    pin = ""
                },
                modifier = modifier,
                enabled = !busy && valid && pin.isNotBlank() && (target is RefundTarget.Correction || reason.isNotBlank()),
            ) { Text("Confirmar estorno") }
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (target is RefundTarget.Correction) "Resolver estorno" else "Estornar pagamento") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Disponível para estorno: ${formatCents(maximum)}")
                if (target is RefundTarget.Correction) {
                    Text("Correção: ${target.correction.itemName}")
                    Text("Escolha o pagamento original.", style = MaterialTheme.typography.bodySmall)
                    eligiblePayments.forEach { payment ->
                        OutlinedButton(onClick = { paymentId = payment.id }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text(if (payment.id == paymentId) "✓ ${formatCents(payment.amountCents - payment.refundedCents)} · ${paymentMethodLabel(payment.method)}" else "${formatCents(payment.amountCents - payment.refundedCents)} · ${paymentMethodLabel(payment.method)}")
                        }
                    }
                } else selectedPayment?.let { Text("Pagamento: ${paymentMethodLabel(it.method)}") }
                OutlinedTextField(value = rawAmount, onValueChange = { rawAmount = it }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), label = { Text("Valor do estorno") }, modifier = Modifier.fillMaxWidth(), singleLine = true, enabled = !busy)
                if (target is RefundTarget.Payment) {
                    OutlinedTextField(value = reason, onValueChange = { reason = it }, label = { Text("Motivo") }, modifier = Modifier.fillMaxWidth(), enabled = !busy)
                }
                if (cashPoints.any { it.activeShiftId != null }) {
                    Text("Caixa para devolução em dinheiro", style = MaterialTheme.typography.labelLarge)
                    cashPoints.filter { it.activeShiftId != null }.forEach { point ->
                        OutlinedButton(onClick = { cashPointId = point.id }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text(if (point.id == cashPointId) "✓ ${point.label}" else point.label)
                        }
                    }
                }
                Text("Confirme sua identidade como operador autorizado; o PIN não é salvo.", color = MaterialTheme.colorScheme.error)
                OutlinedTextField(value = pin, onValueChange = { pin = it }, label = { Text("Seu PIN") }, modifier = Modifier.fillMaxWidth(), singleLine = true, enabled = !busy, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword), visualTransformation = PasswordVisualTransformation())
                if (!valid) Text("Informe um valor válido e um pagamento disponível.", color = MaterialTheme.colorScheme.error)
            }
        },
        confirmButton = {
            if (expanded) Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ConfirmRefund(Modifier.fillMaxWidth())
                TextButton(onClick = onDismiss, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 44.dp)) { Text("Cancelar") }
            } else ConfirmRefund()
        },
        dismissButton = { if (!expanded) TextButton(onClick = onDismiss, enabled = !busy, modifier = Modifier.heightIn(min = 44.dp)) { Text("Cancelar") } },
    )
}

@Composable
private fun MessageDialog(title: String, message: String, onDismiss: () -> Unit) {
    AlertDialog(onDismissRequest = onDismiss, title = { Text(title) }, text = { Text(message) }, confirmButton = { Button(onClick = onDismiss) { Text("Entendi") } })
}

@Composable
private fun LoadingRow() {
    Row(modifier = Modifier.fillMaxWidth().padding(24.dp), horizontalArrangement = Arrangement.Center) { CircularProgressIndicator() }
}

internal fun TabSummary.stateLabel(): String =
    when (state) {
        "OPEN" -> "ABERTA"
        "REQUIRES_ACTION" -> "ATENÇÃO"
        "SETTLING" -> "PAGAMENTO"
        "CLOSED" -> "FECHADA"
        else -> state
    }

private fun itemStateLabel(state: String): String =
    when (state) {
        "NEW" -> "Novo"
        "ACCEPTED" -> "Aceito"
        "PREPARING" -> "Em preparo"
        "READY" -> "Pronto"
        "DELIVERED" -> "Entregue"
        "CANCELLED" -> "Cancelado"
        else -> state
    }

internal fun paymentMethodLabel(method: String): String =
    when (method) {
        "CASH" -> "Dinheiro"
        "EXTERNAL_TERMINAL" -> "Maquininha externa"
        else -> method
    }

internal fun paymentStatusLabel(status: String): String =
    when (status) {
        "CONFIRMED" -> "Pago"
        "PARTIALLY_REFUNDED" -> "Estornado parcialmente"
        "REFUNDED" -> "Estornado"
        "PENDING" -> "Pendente"
        "CONFIRMATION_PENDING" -> "Verificando"
        "FAILED" -> "Falhou"
        else -> status
    }

internal fun ConnectivityState.label(): String =
    when (this) {
        ConnectivityState.ONLINE -> "ONLINE · API atualizada por consulta"
        ConnectivityState.RECONNECTING -> "RECONECTANDO · verificando a API"
        ConnectivityState.STALE -> "DESATUALIZADO · última leitura preservada"
        ConnectivityState.OFFLINE -> "OFFLINE · não inicie cobranças"
    }
