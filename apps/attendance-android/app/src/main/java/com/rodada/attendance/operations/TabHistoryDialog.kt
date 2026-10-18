package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaVisual
import com.rodada.attendance.ui.rodadaTextFieldColors

@Composable
internal fun TabHistoryDialog(
    state: OperationsUiState,
    onReload: () -> Unit,
    onInspect: (String?) -> Unit,
    onDismiss: () -> Unit,
) {
    var search by rememberSaveable { mutableStateOf("") }
    val inspecting = state.historyDetailId != null
    AlertDialog(
        onDismissRequest = { if (inspecting) onInspect(null) else onDismiss() },
        title = { Text(if (inspecting) "Detalhes da comanda" else "Histórico da noite") },
        containerColor = RodadaVisual.Surface,
        text = {
            Column(Modifier.heightIn(max = (LocalConfiguration.current.screenHeightDp * .6f).dp)
                .verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (!inspecting) {
                    Text("Dia operacional atual · somente consulta", style = MaterialTheme.typography.bodySmall)
                    OutlinedTextField(search, { search = it }, label = { Text("Buscar comanda") },
                        singleLine = true, colors = rodadaTextFieldColors(), modifier = Modifier.fillMaxWidth())
                    when {
                        state.historyLoading -> Text("Carregando histórico…")
                        state.historyError != null -> {
                            Text(state.historyError, color = MaterialTheme.colorScheme.error)
                            TextButton(onClick = onReload) { Text("Tentar novamente") }
                        }
                        state.historyLoaded -> {
                            val rows = state.historyTabs.filter { it.matchesOperationalQuery(search) }
                            if (rows.isEmpty()) Text(if (search.isBlank()) "Nenhuma comanda encerrada nesta noite." else "Nenhuma comanda encontrada.")
                            rows.forEach { tab ->
                                com.rodada.attendance.ui.RodadaOutlinedButton(onClick = { onInspect(tab.id) }, modifier = Modifier.fillMaxWidth()) {
                                    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                        Text(tab.operationalLabel(historical = true))
                                        Text(tab.operationalSubtitle(historical = true), style = MaterialTheme.typography.bodySmall)
                                        Text("${if (tab.state == "CANCELLED") "Cancelada" else "Concluída"} · ${formatCents(tab.payableCents)}", style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                            }
                        }
                    }
                } else {
                    if (state.historyDetailLoading) Text("Carregando comanda…")
                    state.historyDetailError?.let {
                        Text(it, color = MaterialTheme.colorScheme.error)
                        TextButton(onClick = { onInspect(state.historyDetailId) }) { Text("Tentar novamente") }
                    }
                    state.historyDetail?.let { detail ->
                        val tab = detail.summary
                        Text(tab.operationalLabel(historical = true), style = MaterialTheme.typography.titleMedium)
                        Text(tab.operationalSubtitle(historical = true), style = MaterialTheme.typography.bodySmall)
                        Text(when (tab.state) { "CLOSED" -> "Concluída"; "CANCELLED" -> "Cancelada"; else -> "Comanda reaberta · somente consulta" })
                        HorizontalDivider(color = RodadaVisual.Border)
                        HistoryValue("Consumo", tab.originalSubtotalCents)
                        if (tab.discountsCents != 0L) HistoryValue("Descontos", tab.discountsCents)
                        if (tab.courtesyCents != 0L) HistoryValue("Cortesias", tab.courtesyCents)
                        if (tab.correctionsCents != 0L) HistoryValue("Correções", tab.correctionsCents)
                        HistoryValue("Taxa de serviço", tab.serviceChargeCents)
                        HistoryValue("Total", tab.payableCents)
                        HistoryValue("Recebido", tab.paymentsCents)
                        if (tab.refundsCents != 0L) HistoryValue("Estornos", tab.refundsCents)
                        if (tab.transfersCents != 0L) HistoryValue("Responsabilidade transferida", tab.transfersCents)
                        HistoryValue("Saldo", tab.exposureCents)
                        Text("Pedidos", style = MaterialTheme.typography.titleMedium)
                        if (detail.orders.isEmpty()) Text("Sem pedidos registrados.")
                        detail.orders.forEachIndexed { index, order ->
                            Text("Pedido ${index + 1}", style = MaterialTheme.typography.labelLarge)
                            order.items.forEach { item ->
                                Text("${item.quantity}× ${item.productName} · ${formatCents(item.lineTotalCents)}")
                                Text(itemStateLabel(item.state), style = MaterialTheme.typography.bodySmall)
                                if (item.customizationText.isNotBlank()) Text(item.customizationText, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                        Text("Pagamentos", style = MaterialTheme.typography.titleMedium)
                        if (detail.payments.isEmpty()) Text("Sem pagamentos registrados.")
                        detail.payments.forEach { payment ->
                            val method = when (payment.method) { "CASH" -> "Dinheiro"; "PIX" -> "Pix"; "CARD", "EXTERNAL_TERMINAL" -> "Cartão"; "TAP_TO_PAY" -> "Aproximação"; else -> "Outro meio" }
                            Text("$method · ${formatCents(payment.amountCents)}")
                            Text(when (payment.status) { "CONFIRMED" -> "Confirmado"; "REFUNDED" -> "Estornado"; "PARTIALLY_REFUNDED" -> "Estornado parcialmente"; "FAILED" -> "Falhou"; "CANCELLED" -> "Cancelado"; "EXPIRED" -> "Expirado"; else -> "Pendente de confirmação" }, style = MaterialTheme.typography.bodySmall)
                            if (payment.simulated) Text("Simulação", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text("Fechar histórico") } },
        dismissButton = { if (inspecting) TextButton(onClick = { onInspect(null) }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Voltar à lista") } },
    )
}

@Composable
private fun HistoryValue(label: String, cents: Long) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, modifier = Modifier.weight(1f))
        Text(formatCents(cents))
    }
}
