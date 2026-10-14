package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.selected
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun RecoveryPanel(state: OperationsUiState, onOpen: (String) -> Unit, onCheckOrders: () -> Unit) {
    Column(Modifier.fillMaxWidth().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("PENDÊNCIAS LOCAIS", style = MaterialTheme.typography.titleMedium)
        Text("Registros preservados no aparelho. Ainda não representam operações confirmadas.")
        val evidence = state.pendingEvidence()
        if (evidence.isEmpty()) Text("Nenhuma pendência legível neste aparelho. Confira também os avisos de recuperação.")
        evidence.forEach { row ->
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(row.label, style = MaterialTheme.typography.titleMedium)
                row.tabId?.let { id ->
                    val label = state.tabs.firstOrNull { it.id == id }?.displayLabel?.takeIf { it.isNotBlank() }
                    Text(label ?: "Comanda ${id.take(8)}")
                }
                if (row.summary.isNotBlank()) Text(row.summary)
                if (row.status.isNotBlank()) Text(row.status, color = RodadaVisual.Amber)
                Text("Capturado em ${java.text.DateFormat.getDateTimeInstance(java.text.DateFormat.SHORT, java.text.DateFormat.SHORT).format(java.util.Date(row.capturedAtMillis))}")
                if (row.canOpenContext) RodadaOutlinedButton(onClick = { onOpen(row.id) },
                    enabled = !state.loading && !state.submitting && state.selectedTab == null && state.cart.isEmpty(),
                    modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Verificar esta operação · ${row.id.take(8)}") }
                else Text(if (row.reviewOnly) "Outra sessão: revisão pela gerência. Não repita a operação."
                    else "Contexto direto ainda indisponível. Peça à gerência para conferir o registro original.", color = RodadaVisual.Amber)
            }
        }
        if (state.queuedOrders.any { it.state in setOf(RecoveryState.PENDING, RecoveryState.CHECKING, RecoveryState.SAFE_TO_RETRY) }) {
            RodadaOutlinedButton(onClick = onCheckOrders, enabled = !state.loading && !state.submitting,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Conferir pedidos no servidor") }
        }
    }
}

enum class NowQueue(val label: String) { READY("Prontos"), CALLS("Chamadas"), PENDING("Pendências") }

fun nowQueueCounts(state: OperationsUiState): Map<NowQueue, String> = mapOf(
    NowQueue.READY to if (!state.loading && state.lastSyncedAtMillis != null && state.connectivity == ConnectivityState.ONLINE) state.deliveryTasks.size.toString() else "—",
    NowQueue.CALLS to if (state.serviceRequestsFresh && state.connectivity == ConnectivityState.ONLINE) state.serviceRequests.size.toString() else "—",
    NowQueue.PENDING to if (state.recoveryEvidenceReadable) state.pendingEvidence().size.toString() else "—")

@Composable
internal fun NowQueueNavigation(selected: NowQueue, counts: Map<NowQueue, String>, onSelect: (NowQueue) -> Unit) {
    val enlarged = LocalDensity.current.fontScale > 1.3f
    @Composable fun QueueButton(queue: NowQueue, modifier: Modifier) {
        RodadaOutlinedButton(onClick = { onSelect(queue) }, modifier = modifier.heightIn(min = 48.dp).semantics { this.selected = selected == queue }) {
            Text("${if (selected == queue) "• " else ""}${queue.label}\n${counts[queue] ?: "—"}")
        }
    }
    if (enlarged) Column(Modifier.fillMaxWidth().padding(horizontal = 12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        NowQueue.entries.forEach { QueueButton(it, Modifier.fillMaxWidth()) }
    } else Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        NowQueue.entries.forEach { QueueButton(it, Modifier.weight(1f)) }
    }
}
