package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun ExceptionalRecoveryScreen(context: ExceptionalRecoveryContext, busy: Boolean, onRefresh: () -> Unit, onBack: () -> Unit) {
    val original = context.original
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Conferir operação original", style = MaterialTheme.typography.headlineSmall)
            Text("Consulta da correção ou estorno guardado. Esta tela não repete a operação.")
            RodadaOutlinedButton(onClick = onBack, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Voltar às pendências") }
        }
        item {
            Text(original.evidence().label, style = MaterialTheme.typography.titleMedium)
            Text("Registro ${original.id}")
            Text("Estado guardado: ${original.evidence().status}", color = RodadaVisual.Amber)
            when (original) {
                is RecoveryIntent.Correction -> {
                    Text("Ação guardada: ${when (original.action) { CorrectionRecoveryAction.CANCEL -> "Cancelar item"; CorrectionRecoveryAction.REMAKE -> "Refazer item"; CorrectionRecoveryAction.REPLACEMENT -> "Substituir item" }}")
                    original.quantity?.let { Text("Quantidade guardada: $it") }
                    original.reasonText?.takeIf { it.isNotBlank() }?.let { Text(it) }
                }
                is RecoveryIntent.Refund -> {
                    Text("Estorno guardado: ${formatCents(original.amountCents)}")
                    original.reason?.takeIf { it.isNotBlank() }?.let { Text(it) }
                }
                else -> Unit
            }
        }
        item {
            Text(context.detail.summary.displayLabel.ifBlank { "Sem identificação" }, style = MaterialTheme.typography.titleMedium)
            Text("Comanda ${context.target.tabId}")
            Text("Estado consultado da comanda: ${context.detail.summary.stateLabel()}")
        }
        context.target.itemId?.let { id -> item {
            val target = context.detail.orders.flatMap { it.items }.first { it.id == id }
            Text("Item original: ${target.quantity} ${target.productName}", style = MaterialTheme.typography.titleMedium)
            Text("Item $id")
            Text("Estado consultado do item: ${target.state.exceptionItemStateLabel()}")
        } }
        context.target.paymentId?.let { id -> item {
            val target = context.detail.payments.first { it.id == id }
            Text("Pagamento original: ${formatCents(target.amountCents)}", style = MaterialTheme.typography.titleMedium)
            Text("Pagamento $id")
            Text("${paymentMethodLabel(target.method)} · ${paymentStatusLabel(target.status)}")
            Text("Estornos confirmados consultados: ${formatCents(target.refundedCents)}")
        } }
        context.target.correctionId?.let { id -> item {
            Text("Correção $id")
            Text("Estado na consulta do vínculo: ${when (context.target.correctionStatus) { "REQUESTED" -> "Solicitada"; "APPLIED" -> "Aplicada"; "REJECTED" -> "Rejeitada"; else -> "A conferir" }}")
        } }
        item {
            Text("O estado do alvo não confirma o resultado deste registro guardado. Não repita a operação; peça à gerência para reconciliar o histórico original.", color = RodadaVisual.Amber)
            RodadaOutlinedButton(onClick = onRefresh, enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Atualizar operação original") }
        }
    }
}

private fun String.exceptionItemStateLabel() = when (this) {
    "NEW" -> "Novo"
    "ACCEPTED" -> "Aceito"
    "PREPARING" -> "Em preparo"
    "READY" -> "Pronto"
    "PICKED_UP" -> "Retirado"
    "DELIVERED" -> "Entregue"
    "CANCELLED" -> "Cancelado"
    else -> "A conferir"
}
