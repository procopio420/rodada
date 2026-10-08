package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.corrections.CorrectionAction
import com.rodada.attendance.corrections.CorrectionCommand
import com.rodada.attendance.corrections.requiresPostProductionEndpoint
import com.rodada.attendance.refunds.DirectRefundCommand
import com.rodada.attendance.refunds.RefundCommand
import com.rodada.attendance.refunds.SettleCorrectionRefundCommand
import java.util.UUID

@Composable
fun AttendanceScreen(
    session: StoredSession,
    viewModel: OperationsViewModel,
    onOpenAccount: () -> Unit,
) {
    val state = viewModel.state
    var openingTab by rememberSaveable { mutableStateOf(false) }
    var takingPayment by rememberSaveable { mutableStateOf(false) }
    var showingTables by rememberSaveable { mutableStateOf(false) }
    var correctionItem by remember { mutableStateOf<OrderItem?>(null) }
    var refundTarget by remember { mutableStateOf<RefundTarget?>(null) }

    LaunchedEffect(session.staffId, session.venueId) { viewModel.ensureLoaded(session) }

    Surface(modifier = Modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize()) {
            Header(
                session = session,
                connectivity = state.connectivity,
                busy = state.loading || state.submitting,
                onOpenAccount = onOpenAccount,
            ) { viewModel.refresh(session) }
            when (val selected = state.selectedTab) {
                null -> {
                    FrontlineNavigation(showingTables = showingTables, onShowTables = { showingTables = it })
                    if (showingTables) {
                        TablesScreen(
                            state = state,
                            canManageTables = "table.manage" in session.capabilities,
                            onOccupy = { tableId, tabId -> viewModel.occupyTable(session, tableId, tabId) },
                            onAttachTab = { occupancyId, tabId -> viewModel.attachTabToOccupancy(session, occupancyId, tabId) },
                            onRelease = { viewModel.releaseTable(session, it) },
                            onStartCleaning = { viewModel.startTableCleaning(session, it) },
                            onCompleteCleaning = { viewModel.completeTableCleaning(session, it) },
                        )
                    } else {
                        TabList(
                            state = state,
                            onOpenTab = { openingTab = true },
                            onSelect = { viewModel.selectTab(session, it) },
                            onCompleteDelivery = { viewModel.completeDelivery(session, it) },
                        )
                    }
                }
                else -> TabWorkspace(
                    state = state,
                    tab = selected,
                    onBack = { viewModel.clearSelection(); viewModel.refresh(session) },
                    onAdd = viewModel::addProduct,
                    onQuantity = viewModel::changeCartQuantity,
                    onConfirmOrder = { viewModel.confirmOrder(session) },
                    onPay = { takingPayment = true },
                    onClose = { viewModel.closeTab(session) },
                    onCorrectItem = { correctionItem = it },
                    onRefundPayment = { refundTarget = RefundTarget.Payment(it) },
                    onSettleCorrection = { refundTarget = RefundTarget.Correction(it) },
                )
            }
        }
    }

    if (openingTab) {
        OpenTabDialog(
            busy = state.submitting,
            onDismiss = { openingTab = false },
            onOpen = {
                viewModel.openTab(session, it)
                openingTab = false
            },
        )
    }
    if (takingPayment && state.selectedTab != null) {
        PaymentDialog(
            tab = state.selectedTab.summary,
            cashPoints = state.cashPoints,
            busy = state.submitting,
            onDismiss = { takingPayment = false },
            onPay = { amount, method, cashPointId ->
                viewModel.collectPayment(session, amount, method, cashPointId)
                takingPayment = false
            },
        )
    }
    correctionItem?.let { item ->
        CorrectionDialog(
            item = item,
            products = state.products,
            busy = state.submitting,
            onDismiss = { correctionItem = null },
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
    state.noticeMessage?.let { MessageDialog("Rodada", it, viewModel::dismissMessage) }
}

@Composable
private fun FrontlineNavigation(showingTables: Boolean, onShowTables: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (showingTables) {
            OutlinedButton(onClick = { onShowTables(false) }, modifier = Modifier.weight(1f)) { Text("Comandas") }
            Button(onClick = {}, modifier = Modifier.weight(1f)) { Text("Mesas") }
        } else {
            Button(onClick = {}, modifier = Modifier.weight(1f)) { Text("Comandas") }
            OutlinedButton(onClick = { onShowTables(true) }, modifier = Modifier.weight(1f)) { Text("Mesas") }
        }
    }
}

@Composable
private fun Header(
    session: StoredSession,
    connectivity: ConnectivityState,
    busy: Boolean,
    onOpenAccount: () -> Unit,
    onRefresh: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text("RODADA / ATENDIMENTO", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
            Text(session.venueName.ifBlank { session.venueSlug }, style = MaterialTheme.typography.titleMedium)
            Text(
                connectivity.label(),
                style = MaterialTheme.typography.labelSmall,
                color = if (connectivity == ConnectivityState.ONLINE) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
            )
        }
        TextButton(onClick = onRefresh, enabled = !busy) { Text("Atualizar") }
        OutlinedButton(onClick = onOpenAccount, enabled = !busy) { Text("Conta") }
    }
}

@Composable
private fun TabList(
    state: OperationsUiState,
    onOpenTab: () -> Unit,
    onSelect: (String) -> Unit,
    onCompleteDelivery: (String) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Button(onClick = onOpenTab, enabled = !state.submitting, modifier = Modifier.fillMaxWidth()) {
                Text("Abrir nova comanda")
            }
            Spacer(Modifier.height(12.dp))
            Text("Entregas prontas", style = MaterialTheme.typography.headlineSmall)
        }
        if (!state.loading && state.deliveryTasks.isEmpty()) {
            item { Text("Nenhuma entrega aguardando.") }
        }
        items(state.deliveryTasks, key = { it.id }) { task ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(5.dp),
                ) {
                    Text(task.destinationLabel.ifBlank { "Destino não informado" }, fontWeight = FontWeight.Bold)
                    Text("${task.quantity}× ${task.productName}")
                    if (task.tabLabel.isNotBlank()) Text("Comanda: ${task.tabLabel}")
                    Text("Pronto há ${deliveryAge(task.ageSeconds)}", style = MaterialTheme.typography.bodySmall)
                    Button(
                        onClick = { onCompleteDelivery(task.id) },
                        enabled = !state.submitting,
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Entregue") }
                }
            }
        }
        item {
            Spacer(Modifier.height(12.dp))
            Text("Comandas", style = MaterialTheme.typography.headlineSmall)
        }
        if (state.loading && state.tabs.isEmpty()) {
            item { LoadingRow() }
        }
        if (!state.loading && state.tabs.isEmpty()) {
            item { Text("Nenhuma comanda aberta neste dispositivo.") }
        }
        items(state.tabs, key = { it.id }) { tab ->
            OutlinedButton(onClick = { onSelect(tab.id) }, modifier = Modifier.fillMaxWidth(), enabled = !state.submitting) {
                Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(tab.displayLabel, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(tab.stateLabel())
                    }
                    Text("Em aberto: ${formatCents(tab.exposureCents)}", style = MaterialTheme.typography.bodyLarge)
                }
            }
        }
        item { Spacer(Modifier.height(20.dp)) }
    }
}

private fun deliveryAge(seconds: Long): String =
    if (seconds < 60) "agora" else "${seconds / 60} min"

@Composable
private fun TabWorkspace(
    state: OperationsUiState,
    tab: TabDetail,
    onBack: () -> Unit,
    onAdd: (Product) -> Unit,
    onQuantity: (String, Int) -> Unit,
    onConfirmOrder: () -> Unit,
    onPay: () -> Unit,
    onClose: () -> Unit,
    onCorrectItem: (OrderItem) -> Unit,
    onRefundPayment: (TabPayment) -> Unit,
    onSettleCorrection: (RefundRequiredCorrection) -> Unit,
) {
    var query by rememberSaveable(tab.summary.id) { mutableStateOf("") }
    val availableProducts = remember(state.products, query) {
        state.products.filter { it.name.contains(query, ignoreCase = true) }
    }
    val cartTotal = state.cart.sumOf { it.product.priceCents * it.quantity }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            TextButton(onClick = onBack, enabled = !state.submitting) { Text("← Comandas") }
            Text(tab.summary.displayLabel, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("${tab.summary.stateLabel()} · versão ${tab.summary.version}")
            BalanceCard(tab.summary, onPay, onClose, state.submitting, state.connectivity == ConnectivityState.ONLINE)
        }
        item {
            Text("Novo pedido", style = MaterialTheme.typography.titleLarge)
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                label = { Text("Buscar no catálogo") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                enabled = tab.summary.state != "CLOSED" && !state.submitting,
            )
        }
        items(availableProducts, key = { it.id }) { product ->
            val sellable = product.active && product.availability == "AVAILABLE" && tab.summary.state != "CLOSED"
            OutlinedButton(onClick = { onAdd(product) }, enabled = sellable && !state.submitting && state.orderIntentId == null, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(product.name, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(formatCents(product.priceCents))
                    }
                    Text(
                        if (sellable) product.fulfillmentStation else "${product.availability} · indisponível",
                        color = if (sellable) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.error,
                    )
                }
            }
        }
        item {
            if (availableProducts.isEmpty()) Text("Nenhum produto encontrado.")
            OrderCart(state.cart, cartTotal, state.submitting, state.orderIntentId != null, onQuantity, onConfirmOrder)
        }
        if (tab.orders.isNotEmpty()) {
            item { Text("Pedidos confirmados", style = MaterialTheme.typography.titleLarge) }
            items(tab.orders, key = { it.id }) { order ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Pedido", fontWeight = FontWeight.Bold)
                        order.items.forEach { item ->
                            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text("${item.quantity}× ${item.productName} · ${formatCents(item.lineTotalCents)}")
                                    Text(itemStateLabel(item.state), style = MaterialTheme.typography.bodySmall)
                                }
                                OutlinedButton(
                                    onClick = { onCorrectItem(item) },
                                    enabled = !state.submitting && tab.summary.state != "CLOSED" && item.state !in setOf("CANCELLED"),
                                ) { Text("Corrigir") }
                            }
                        }
                    }
                }
            }
        }
        if (tab.payments.isNotEmpty()) {
            item { Text("Pagamentos", style = MaterialTheme.typography.titleLarge) }
            items(tab.payments, key = { it.id }) { payment ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        Text(paymentMethodLabel(payment.method), fontWeight = FontWeight.Bold)
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
        if (tab.refundRequiredCorrections.isNotEmpty()) {
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

@Composable
private fun BalanceCard(
    tab: TabSummary,
    onPay: () -> Unit,
    onClose: () -> Unit,
    busy: Boolean,
    canInitiatePayment: Boolean,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Saldo em aberto", style = MaterialTheme.typography.labelLarge)
            Text(formatCents(tab.exposureCents), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("Cobrado ${formatCents(tab.chargesCents)} · recebido ${formatCents(tab.paymentsCents)}")
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = onPay, enabled = tab.exposureCents > 0 && tab.state != "CLOSED" && !busy && canInitiatePayment, modifier = Modifier.weight(1f)) {
                    Text("Receber")
                }
                OutlinedButton(onClick = onClose, enabled = tab.exposureCents == 0L && tab.state != "CLOSED" && !busy, modifier = Modifier.weight(1f)) {
                    Text(if (tab.state == "CLOSED") "Fechada" else "Fechar")
                }
            }
        }
    }
}

@Composable
private fun OrderCart(
    cart: List<CartLine>,
    total: Long,
    busy: Boolean,
    locked: Boolean,
    onQuantity: (String, Int) -> Unit,
    onConfirm: () -> Unit,
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
                        Text("${formatCents(line.product.priceCents)} cada")
                    }
                    TextButton(onClick = { onQuantity(line.product.id, -1) }, enabled = !busy && !locked) { Text("−") }
                    Text("${line.quantity}")
                    TextButton(onClick = { onQuantity(line.product.id, 1) }, enabled = !busy && !locked) { Text("+") }
                }
            }
            if (cart.isNotEmpty()) {
                Text("Total: ${formatCents(total)}", fontWeight = FontWeight.Bold)
                Button(onClick = onConfirm, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Confirmar pedido") }
            }
        }
    }
}

@Composable
private fun OpenTabDialog(busy: Boolean, onDismiss: () -> Unit, onOpen: (String) -> Unit) {
    var label by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Abrir comanda") },
        text = {
            OutlinedTextField(value = label, onValueChange = { label = it }, label = { Text("Nome ou apelido (opcional)") }, modifier = Modifier.fillMaxWidth())
        },
        confirmButton = { Button(onClick = { onOpen(label.trim()) }, enabled = !busy) { Text("Abrir") } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
private fun PaymentDialog(
    tab: TabSummary,
    cashPoints: List<CashPoint>,
    busy: Boolean,
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
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Receber pagamento") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Em aberto: ${formatCents(tab.exposureCents)}")
                OutlinedTextField(value = rawAmount, onValueChange = { rawAmount = it }, label = { Text("Valor") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                PaymentMethod.entries.forEach { candidate ->
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
                if (!valid) Text("Informe um valor entre R$ 0,01 e o saldo em aberto.", color = MaterialTheme.colorScheme.error)
                if (method != PaymentMethod.CASH) Text("Registre somente após confirmação no terminal/provedor. O app não confirma pagamentos externos sozinho.")
            }
        },
        confirmButton = {
            Button(
                onClick = { onPay(amount ?: 0, method, cashPointId.ifBlank { null }) },
                enabled = valid && !busy && (method != PaymentMethod.CASH || cashPointId.isNotBlank()),
            ) { Text("Registrar") }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
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
    var action by remember(item.id) { mutableStateOf(CorrectionAction.CANCEL) }
    var reason by remember(item.id) { mutableStateOf("") }
    var pin by remember(item.id) { mutableStateOf("") }
    var replacementId by remember(item.id) { mutableStateOf("") }
    // Retain this key while the dialog remains open. A timeout retry is therefore the same command.
    val idempotencyKey = remember(item.id, action, replacementId) { UUID.randomUUID().toString() }
    val replacementProducts = products.filter { it.active && it.availability == "AVAILABLE" && it.id != replacementId }
    val requiresReauth = CorrectionCommand(item.id, item.state, action, "OPERATIONAL", reason, idempotencyKey, replacementId.ifBlank { null }).requiresPostProductionEndpoint()
    val replacementValid = action != CorrectionAction.REPLACEMENT || replacementId.isNotBlank()
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Corrigir ${item.productName}") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${item.quantity}× ${formatCents(item.lineTotalCents)} · ${itemStateLabel(item.state)}")
                CorrectionAction.entries.forEach { candidate ->
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
                    Text("Esta ação preserva o histórico de produção e requer confirmação gerencial.", color = MaterialTheme.colorScheme.error)
                    OutlinedTextField(
                        value = pin,
                        onValueChange = { pin = it },
                        label = { Text("PIN do gerente") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        enabled = !busy,
                        visualTransformation = PasswordVisualTransformation(),
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
                enabled = !busy && reason.isNotBlank() && replacementValid && (!requiresReauth || pin.isNotBlank()),
            ) { Text(action.label) }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Voltar") } },
    )
}

private sealed interface RefundTarget {
    data class Payment(val payment: TabPayment) : RefundTarget
    data class Correction(val correction: RefundRequiredCorrection) : RefundTarget
}

@Composable
private fun RefundDialog(
    target: RefundTarget,
    payments: List<TabPayment>,
    cashPoints: List<CashPoint>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (RefundCommand, String) -> Unit,
) {
    val eligiblePayments = payments.filter { it.amountCents > it.refundedCents }
    var paymentId by remember(target) { mutableStateOf((target as? RefundTarget.Payment)?.payment?.id ?: eligiblePayments.firstOrNull()?.id.orEmpty()) }
    val selectedPayment = eligiblePayments.firstOrNull { it.id == paymentId }
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
    val valid = amount != null && amount > 0 && amount <= maximum && selectedPayment != null
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (target is RefundTarget.Correction) "Resolver estorno" else "Estornar pagamento") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
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
                OutlinedTextField(value = rawAmount, onValueChange = { rawAmount = it }, label = { Text("Valor do estorno") }, modifier = Modifier.fillMaxWidth(), singleLine = true, enabled = !busy)
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
                Text("Confirme sua identidade; o PIN não é salvo.", color = MaterialTheme.colorScheme.error)
                OutlinedTextField(value = pin, onValueChange = { pin = it }, label = { Text("PIN do gerente") }, modifier = Modifier.fillMaxWidth(), singleLine = true, enabled = !busy, visualTransformation = PasswordVisualTransformation())
                if (!valid) Text("Informe um valor válido e um pagamento disponível.", color = MaterialTheme.colorScheme.error)
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val command = when (target) {
                        is RefundTarget.Payment -> DirectRefundCommand(paymentId, amount ?: 0, reason.trim(), key, cashPointId.ifBlank { null })
                        is RefundTarget.Correction -> SettleCorrectionRefundCommand(target.correction.id, paymentId, amount ?: 0, key, cashPointId.ifBlank { null })
                    }
                    onSubmit(command, pin)
                    pin = ""
                },
                enabled = !busy && valid && pin.isNotBlank() && (target is RefundTarget.Correction || reason.isNotBlank()),
            ) { Text("Confirmar estorno") }
        },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
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

private fun TabSummary.stateLabel(): String =
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

private fun paymentMethodLabel(method: String): String =
    when (method) {
        "CASH" -> "Dinheiro"
        "EXTERNAL_TERMINAL" -> "Maquininha externa"
        else -> method
    }

private fun paymentStatusLabel(status: String): String =
    when (status) {
        "CONFIRMED" -> "Pago"
        "PENDING" -> "Pendente"
        "CONFIRMATION_PENDING" -> "Verificando"
        "FAILED" -> "Falhou"
        else -> status
    }

private fun ConnectivityState.label(): String =
    when (this) {
        ConnectivityState.ONLINE -> "ONLINE · API atualizada por consulta"
        ConnectivityState.RECONNECTING -> "RECONECTANDO · verificando a API"
        ConnectivityState.STALE -> "DESATUALIZADO · última leitura preservada"
        ConnectivityState.OFFLINE -> "OFFLINE · não inicie cobranças"
    }
