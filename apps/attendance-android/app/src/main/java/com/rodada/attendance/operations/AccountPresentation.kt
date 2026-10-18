package com.rodada.attendance.operations

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaButton
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun AccountPanel(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Surface(modifier.fillMaxWidth(), shape = MaterialTheme.shapes.medium,
        color = RodadaVisual.Surface, contentColor = RodadaVisual.Paper,
        border = BorderStroke(1.dp, RodadaVisual.Border), content = content)
}

@Composable
private fun AccountValue(label: String, value: String) {
    val largeText = LocalDensity.current.fontScale > 1.3f
    val labelContent: @Composable () -> Unit = { Text(label, style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted) }
    val valueContent: @Composable () -> Unit = { Text(value, style = MaterialTheme.typography.bodyMedium, fontFamily = RodadaVisual.Number) }
    if (largeText) Column(Modifier.fillMaxWidth().semantics(mergeDescendants = true) {}, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        labelContent(); valueContent()
    } else Row(Modifier.fillMaxWidth().semantics(mergeDescendants = true) {}, horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.weight(1f)) { labelContent() }; valueContent()
    }
}

@Composable
internal fun BalanceCard(tab: TabSummary, onPay: () -> Unit, onClose: () -> Unit, busy: Boolean, canInitiatePayment: Boolean) {
    var expanded by rememberSaveable(tab.id) { mutableStateOf(false) }
    AccountPanel(Modifier.testTag("account-balance")) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Saldo em aberto", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
            Text(formatCents(tab.exposureCents), style = MaterialTheme.typography.headlineSmall,
                fontFamily = RodadaVisual.Number, fontWeight = FontWeight.Bold, color = RodadaVisual.Paper)
            TextButton(onClick = { expanded = !expanded }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                .semantics { stateDescription = if (expanded) "Detalhes expandidos" else "Detalhes recolhidos" }) {
                Text(if (expanded) "Recolher detalhes da conta" else "Ver detalhes da conta", style = MaterialTheme.typography.bodySmall, modifier = Modifier.fillMaxWidth())
            }
            if (expanded) {
                HorizontalDivider(color = RodadaVisual.Border)
                AccountValue("Subtotal original", formatCents(tab.originalSubtotalCents))
                AccountValue("Descontos", formatCents(tab.discountsCents))
                AccountValue("Cortesias", formatCents(tab.courtesyCents))
                if (tab.correctionsCents != 0L) AccountValue("Correções", formatCents(tab.correctionsCents))
                AccountValue("Taxa de serviço", formatCents(tab.serviceChargeCents))
                AccountValue("Total a pagar", formatCents(tab.payableCents))
                AccountValue("Pagamentos recebidos", formatCents(tab.paymentsCents))
                AccountValue("Estornos", formatCents(tab.refundsCents))
                if (tab.transfersCents != 0L) AccountValue("Responsabilidade transferida", formatCents(tab.transfersCents))
                AccountValue("Limite", formatCents(tab.effectiveLimitCents))
                AccountValue("Disponível", formatCents(tab.remainingCapacityCents))
                tab.percentageUsed?.let { Text("$it% do limite utilizado", style = MaterialTheme.typography.bodySmall) }
            }
            if (tab.serviceAssessmentStale) Text("Atualize a taxa de serviço no caixa antes de receber.", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Amber)
            if (tab.actionReasons.any { it != "SPENDING_LIMIT" }) Text("Há outras ações pendentes na comanda.", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Amber)
            HorizontalDivider(color = RodadaVisual.Border)
            val payEnabled = !tab.serviceAssessmentStale && tab.exposureCents > 0 && tab.state != "CLOSED" && !busy && canInitiatePayment
            val closeEnabled = !tab.serviceAssessmentStale && tab.exposureCents == 0L && tab.state != "CLOSED" && !busy
            if (LocalDensity.current.fontScale > 1.3f) Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                RodadaButton(onClick = onPay, enabled = payEnabled, modifier = Modifier.fillMaxWidth()) { Text("Pagar", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold) }
                RodadaOutlinedButton(onClick = onClose, enabled = closeEnabled, modifier = Modifier.fillMaxWidth()) { Text(if (tab.state == "CLOSED") "Fechada" else "Fechar", style = MaterialTheme.typography.bodyMedium) }
            } else Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                RodadaButton(onClick = onPay, enabled = payEnabled, modifier = Modifier.weight(1f)) { Text("Pagar", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold) }
                RodadaOutlinedButton(onClick = onClose, enabled = closeEnabled, modifier = Modifier.weight(1f)) { Text(if (tab.state == "CLOSED") "Fechada" else "Fechar", style = MaterialTheme.typography.bodyMedium) }
            }
        }
    }
}

@Composable
internal fun AccountActions(tab: TabSummary, busy: Boolean, online: Boolean, onAdjustPricing: () -> Unit, onOperations: () -> Unit, onResolveLimit: () -> Unit) {
    var expanded by rememberSaveable(tab.id) { mutableStateOf(false) }
    AccountPanel {
        Column(Modifier.padding(horizontal = 12.dp)) {
            TextButton(onClick = { expanded = !expanded }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
                .semantics { stateDescription = if (expanded) "Ações expandidas" else "Ações recolhidas" }) {
                Text("Ações da conta", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
                Text(if (expanded) "Recolher" else "Ver", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
            }
            if (expanded) {
                HorizontalDivider(color = RodadaVisual.Border)
                TextButton(onClick = onAdjustPricing, enabled = !busy && online, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Ajustar conta / serviço", modifier = Modifier.fillMaxWidth(), style = MaterialTheme.typography.bodyMedium) }
                TextButton(onClick = onOperations, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Operações da comanda", modifier = Modifier.fillMaxWidth(), style = MaterialTheme.typography.bodyMedium) }
                if (tab.state != "CLOSED") TextButton(onClick = onResolveLimit, enabled = !busy && online, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Solicitar / aprovar limite", modifier = Modifier.fillMaxWidth(), style = MaterialTheme.typography.bodyMedium) }
            }
        }
    }
}

@Composable
internal fun ConfirmedOrderCard(order: TabOrder, repeatEnabled: Boolean, correctionEnabled: Boolean, onRepeat: () -> Unit, onCorrect: (OrderItem) -> Unit) {
    val largeText = LocalDensity.current.fontScale > 1.3f
    AccountPanel {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            val heading: @Composable () -> Unit = { Text("Pedido · ${order.id.take(8).uppercase()}", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted) }
            val repeat: @Composable () -> Unit = { TextButton(onClick = onRepeat, enabled = repeatEnabled, modifier = Modifier.heightIn(min = 48.dp)) { Text("Mais uma rodada", style = MaterialTheme.typography.bodySmall) } }
            if (largeText) Column { heading(); repeat() } else Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Box(Modifier.weight(1f)) { heading() }; repeat() }
            order.items.forEach { item ->
                HorizontalDivider(color = RodadaVisual.Border)
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    val name: @Composable () -> Unit = { Text("${item.quantity}× ${item.productName}", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold) }
                    val amount: @Composable () -> Unit = { Text(formatCents(item.lineTotalCents), style = MaterialTheme.typography.bodyMedium, fontFamily = RodadaVisual.Number) }
                    if (largeText) Column(verticalArrangement = Arrangement.spacedBy(4.dp)) { name(); amount() }
                    else Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) { Box(Modifier.weight(1f)) { name() }; amount() }
                    if (item.customizationText.isNotBlank()) Text(item.customizationText, style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text(itemStateLabel(item.state), style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted, modifier = Modifier.weight(1f))
                        if (item.state != "CANCELLED") TextButton(onClick = { onCorrect(item) }, enabled = correctionEnabled, modifier = Modifier.heightIn(min = 48.dp)) { Text("Corrigir", style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
        }
    }
}
