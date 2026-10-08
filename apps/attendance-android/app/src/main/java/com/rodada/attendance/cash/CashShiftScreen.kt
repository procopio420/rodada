package com.rodada.attendance.cash

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.StoredSession
import java.text.NumberFormat
import java.util.Locale

@Composable
fun CashShiftScreen(session: StoredSession, viewModel: CashShiftViewModel) {
    val state = viewModel.state
    var dialog by rememberSaveable { mutableStateOf<CashDialog?>(null) }
    // Re-entering Caixa is also the recovery boundary after an opening/movement
    // response was lost.  A cached closed cash point must not hide a shift that
    // the server has already committed.
    LaunchedEffect(session.staffId, session.venueId) { viewModel.refresh(session) }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Text("Caixa", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("Valores e divergências são confirmados pelo Rodada.")
        }
        if (state.cashPoints.size > 1) {
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.cashPoints.forEach { point ->
                        val selected = point.id == state.selectedCashPointId
                        if (selected) Button(onClick = {}, enabled = false) { Text(point.label) }
                        else OutlinedButton(onClick = { viewModel.selectCashPoint(session, point.id) }, enabled = !state.submitting) { Text(point.label) }
                    }
                }
            }
        }
        when (val shift = state.activeShift) {
            null -> item {
                CashClosedCard(
                    point = state.selectedCashPoint,
                    enabled = state.selectedCashPoint != null && !state.loading && !state.submitting,
                    onOpen = { dialog = CashDialog.OPEN },
                )
            }
            else -> {
                item {
                    ActiveCashCard(
                        shift = shift,
                        point = state.selectedCashPoint,
                        enabled = !state.submitting,
                        onSupply = { dialog = CashDialog.SUPPLY },
                        onWithdrawal = { dialog = CashDialog.WITHDRAWAL },
                        onCount = {
                            if (shift.status == "COUNTING") dialog = CashDialog.CLOSE
                            else viewModel.startCount(session)
                        },
                    )
                }
                state.detail?.movements?.take(20)?.let { movements ->
                    item { Text("Movimentos recentes", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold) }
                    items(movements, key = { it.id }) { movement -> MovementCard(movement) }
                }
                if (shift.reviewStatus != "NOT_REQUIRED" && shift.status != "OPEN") {
                    item {
                        OutlinedButton(onClick = { dialog = CashDialog.REVIEW }, enabled = !state.submitting, modifier = Modifier.fillMaxWidth()) {
                            Text("Revisar divergência")
                        }
                    }
                }
            }
        }
        if (state.loading) item { Text("Atualizando caixa…") }
        if (state.cashPoints.isEmpty() && !state.loading) item { Text("Nenhum ponto de caixa disponível para este acesso.") }
    }

    when (dialog) {
        CashDialog.OPEN -> MoneyDialog("Abrir caixa", "Fundo inicial", "Abrir caixa", state.submitting, onDismiss = { dialog = null }) {
            viewModel.openShift(session, it)
            dialog = null
        }
        CashDialog.SUPPLY -> MovementDialog("Suprimento", "Registrar suprimento", state.submitting, onDismiss = { dialog = null }) { amount, reason ->
            viewModel.supply(session, amount, reason)
            dialog = null
        }
        CashDialog.WITHDRAWAL -> MovementDialog("Sangria", "Registrar sangria", state.submitting, onDismiss = { dialog = null }) { amount, reason ->
            viewModel.withdraw(session, amount, reason)
            dialog = null
        }
        CashDialog.CLOSE -> CountDialog(state.activeShift, state.submitting, onDismiss = { dialog = null }) { amount ->
            viewModel.close(session, amount)
            dialog = null
        }
        CashDialog.REVIEW -> ReasonDialog(state.submitting, onDismiss = { dialog = null }) { reason ->
            viewModel.review(session, reason.first, reason.second)
            dialog = null
        }
        null -> Unit
    }
    state.errorMessage?.let { CashMessageDialog("Atenção", it, viewModel::dismissMessage) }
    state.noticeMessage?.let { CashMessageDialog("Caixa", it, viewModel::dismissMessage) }
}

private enum class CashDialog { OPEN, SUPPLY, WITHDRAWAL, CLOSE, REVIEW }

@Composable
private fun CashClosedCard(point: CashPointSnapshot?, enabled: Boolean, onOpen: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(point?.label ?: "Caixa", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text("Caixa fechado")
            Button(onClick = onOpen, enabled = enabled, modifier = Modifier.fillMaxWidth()) { Text("Abrir caixa") }
        }
    }
}

@Composable
private fun ActiveCashCard(
    shift: CashShiftSnapshot,
    point: CashPointSnapshot?,
    enabled: Boolean,
    onSupply: () -> Unit,
    onWithdrawal: () -> Unit,
    onCount: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(point?.label ?: "Caixa", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text("Aberto · ${shift.businessDate}")
            MoneyRow("Fundo inicial", shift.openingFloatCents)
            shift.expectedCents?.let { MoneyRow("Esperado", it) }
            shift.countedAmountCents?.let { MoneyRow("Contado", it) }
            shift.discrepancyCents?.let { MoneyRow("Diferença", it, emphasis = true) }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onSupply, enabled = enabled, modifier = Modifier.weight(1f)) { Text("Suprimento") }
                OutlinedButton(onClick = onWithdrawal, enabled = enabled, modifier = Modifier.weight(1f)) { Text("Sangria") }
            }
            Button(onClick = onCount, enabled = enabled, modifier = Modifier.fillMaxWidth()) {
                Text(if (shift.status == "COUNTING") "Informar contagem" else "Iniciar contagem")
            }
        }
    }
}

@Composable
private fun MovementCard(movement: CashMovementSnapshot) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(movement.kind.cashMovementLabel(), fontWeight = FontWeight.Bold)
            Text(formatCashCents(movement.amountCents))
            if (movement.reason.isNotBlank()) Text(movement.reason, style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun MoneyDialog(title: String, label: String, action: String, busy: Boolean, onDismiss: () -> Unit, onConfirm: (Long) -> Unit) {
    var amount by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = { MoneyInput(label, amount) { amount = it } },
        confirmButton = { Button(onClick = { parseCashInput(amount)?.let(onConfirm) }, enabled = !busy && parseCashInput(amount) != null) { Text(action) } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
private fun MovementDialog(title: String, action: String, busy: Boolean, onDismiss: () -> Unit, onConfirm: (Long, String) -> Unit) {
    var amount by rememberSaveable { mutableStateOf("") }
    var reason by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                MoneyInput("Valor", amount) { amount = it }
                OutlinedTextField(reason, { reason = it }, label = { Text("Motivo") }, modifier = Modifier.fillMaxWidth())
            }
        },
        confirmButton = { Button(onClick = { parseCashInput(amount)?.let { onConfirm(it, reason) } }, enabled = !busy && parseCashInput(amount) != null) { Text(action) } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
private fun CountDialog(shift: CashShiftSnapshot?, busy: Boolean, onDismiss: () -> Unit, onConfirm: (Long) -> Unit) {
    var amount by rememberSaveable { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Contar caixa") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Conte o dinheiro antes de consultar o esperado.")
                MoneyInput("Valor contado", amount) { amount = it }
                parseCashInput(amount)?.let { counted ->
                    shift?.expectedCents?.let { expected ->
                        MoneyRow("Esperado", expected)
                        MoneyRow("Contado", counted)
                        MoneyRow("Diferença", counted - expected, emphasis = true)
                    }
                }
            }
        },
        confirmButton = { Button(onClick = { parseCashInput(amount)?.let(onConfirm) }, enabled = !busy && parseCashInput(amount) != null) { Text("Fechar caixa") } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
private fun ReasonDialog(busy: Boolean, onDismiss: () -> Unit, onConfirm: (Pair<String, String>) -> Unit) {
    var reason by rememberSaveable { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Revisar divergência") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(reason, { reason = it }, label = { Text("Motivo da revisão") }, modifier = Modifier.fillMaxWidth())
                Text("Confirme a identidade do operador autorizado; o PIN não é salvo.", style = MaterialTheme.typography.bodySmall)
                OutlinedTextField(pin, { pin = it }, label = { Text("Seu PIN") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword), visualTransformation = PasswordVisualTransformation())
            }
        },
        confirmButton = { Button(onClick = { onConfirm(reason to pin); pin = "" }, enabled = !busy && reason.isNotBlank() && pin.isNotBlank()) { Text("Confirmar revisão") } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
    )
}

@Composable
private fun MoneyInput(label: String, value: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        prefix = { Text("R$ ") },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun MoneyRow(label: String, cents: Long, emphasis: Boolean = false) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, fontWeight = if (emphasis) FontWeight.Bold else null)
        Text(formatCashCents(cents), fontWeight = if (emphasis) FontWeight.Bold else null)
    }
}

@Composable
private fun CashMessageDialog(title: String, message: String, onDismiss: () -> Unit) = AlertDialog(
    onDismissRequest = onDismiss,
    title = { Text(title) },
    text = { Text(message) },
    confirmButton = { TextButton(onClick = onDismiss) { Text("Entendi") } },
)

internal fun parseCashInput(value: String): Long? {
    val normalized = value.trim().replace("R$", "", ignoreCase = true).replace(" ", "")
    if (normalized.isBlank()) return null
    val decimal = when {
        ',' in normalized -> normalized.replace(".", "").replace(',', '.')
        else -> normalized
    }
    return runCatching { decimal.toBigDecimal().movePointRight(2).longValueExact() }
        .getOrNull()
        ?.takeIf { it >= 0 }
}

internal fun formatCashCents(cents: Long): String =
    NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(cents / 100.0)

private fun String.cashMovementLabel(): String = when (this) {
    "OPENING_FLOAT" -> "Fundo inicial"
    "CASH_PAYMENT" -> "Recebimento em dinheiro"
    "SUPPLY" -> "Suprimento"
    "WITHDRAWAL" -> "Sangria"
    "REFUND" -> "Estorno"
    else -> this
}
