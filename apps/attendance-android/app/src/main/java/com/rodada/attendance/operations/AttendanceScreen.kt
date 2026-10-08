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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.StoredSession

@Composable
fun AttendanceScreen(
    session: StoredSession,
    viewModel: OperationsViewModel,
    onOpenAccount: () -> Unit,
) {
    val state = viewModel.state
    var openingTab by rememberSaveable { mutableStateOf(false) }
    var takingPayment by rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(session.staffId, session.venueId) { viewModel.ensureLoaded(session) }

    Surface(modifier = Modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize()) {
            Header(session, state.loading || state.submitting, onOpenAccount) { viewModel.refresh(session) }
            when (val selected = state.selectedTab) {
                null -> TabList(
                    state = state,
                    onOpenTab = { openingTab = true },
                    onSelect = { viewModel.selectTab(session, it) },
                    onCompleteDelivery = { viewModel.completeDelivery(session, it) },
                )
                else -> TabWorkspace(
                    state = state,
                    tab = selected,
                    onBack = { viewModel.clearSelection(); viewModel.refresh(session) },
                    onAdd = viewModel::addProduct,
                    onQuantity = viewModel::changeCartQuantity,
                    onConfirmOrder = { viewModel.confirmOrder(session) },
                    onPay = { takingPayment = true },
                    onClose = { viewModel.closeTab(session) },
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
            busy = state.submitting,
            onDismiss = { takingPayment = false },
            onPay = { amount, method ->
                viewModel.collectPayment(session, amount, method)
                takingPayment = false
            },
        )
    }
    state.errorMessage?.let { MessageDialog("Atenção", it, viewModel::dismissMessage) }
    state.noticeMessage?.let { MessageDialog("Rodada", it, viewModel::dismissMessage) }
}

@Composable
private fun Header(
    session: StoredSession,
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
            BalanceCard(tab.summary, onPay, onClose, state.submitting)
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
                            Text("${item.quantity}× ${item.productName} · ${formatCents(item.lineTotalCents)} · ${item.state}")
                        }
                    }
                }
            }
        }
        item { Spacer(Modifier.height(24.dp)) }
    }
}

@Composable
private fun BalanceCard(tab: TabSummary, onPay: () -> Unit, onClose: () -> Unit, busy: Boolean) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Saldo em aberto", style = MaterialTheme.typography.labelLarge)
            Text(formatCents(tab.exposureCents), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text("Cobrado ${formatCents(tab.chargesCents)} · recebido ${formatCents(tab.paymentsCents)}")
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(onClick = onPay, enabled = tab.exposureCents > 0 && tab.state != "CLOSED" && !busy, modifier = Modifier.weight(1f)) {
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
private fun PaymentDialog(tab: TabSummary, busy: Boolean, onDismiss: () -> Unit, onPay: (Long, PaymentMethod) -> Unit) {
    var rawAmount by rememberSaveable(tab.id) { mutableStateOf("${tab.exposureCents / 100},${(tab.exposureCents % 100).toString().padStart(2, '0')}") }
    var method by rememberSaveable(tab.id) { mutableStateOf(PaymentMethod.CASH) }
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
                if (!valid) Text("Informe um valor entre R$ 0,01 e o saldo em aberto.", color = MaterialTheme.colorScheme.error)
                if (method != PaymentMethod.CASH) Text("Registre somente após confirmação no terminal/provedor. O app não confirma pagamentos externos sozinho.")
            }
        },
        confirmButton = { Button(onClick = { onPay(amount ?: 0, method) }, enabled = valid && !busy) { Text("Registrar") } },
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
