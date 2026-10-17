package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaVisual

/** Explicit existing mutations remain separate from opening the operational context. */
@Composable
internal fun ServiceTaskContext(task: ServiceRequest, staffId: String, state: OperationsUiState, onAction: (Boolean) -> Unit) {
    Column(Modifier.fillMaxWidth().padding(12.dp)) {
        Text("${task.title} · ${task.responsibility(staffId)}", color = RodadaVisual.Amber)
        val pending = state.pendingServiceAction
        val enabled = !state.loading && !state.submitting && state.serviceRequestsFresh && state.connectivity == ConnectivityState.ONLINE && !task.belongsToOther(staffId)
        if (pending?.taskId == task.id) TextButton(onClick = { onAction(pending.complete) }, enabled = enabled) { Text("Verificar mesma chamada") }
        else if (pending == null) {
            // Preserve readable labels and touch areas when user fonts need more width.
            val largeFont = LocalDensity.current.fontScale >= 1.5f
            BoxWithConstraints(Modifier.fillMaxWidth()) {
                if (largeFont || maxWidth < 360.dp) {
                    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        if (task.claimedById != staffId) TextButton(onClick = { onAction(false) }, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Assumir chamada") }
                        TextButton(onClick = { onAction(true) }, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Concluir chamada") }
                    }
                } else {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        if (task.claimedById != staffId) TextButton(onClick = { onAction(false) }, enabled = enabled, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Assumir chamada") }
                        TextButton(onClick = { onAction(true) }, enabled = enabled, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Concluir chamada") }
                    }
                }
            }
        }
    }
}

@Composable
internal fun DeliveryTaskDetail(task: DeliveryTask?, busy: Boolean, staffId: String, onDismiss: () -> Unit,
    onOpenTab: (String) -> Unit, onComplete: () -> Unit) {
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Entrega") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (task == null) Text("Tarefa ausente da fila atual. Isso não comprova entrega; confira o histórico original.")
            else {
                Text("${task.quantity}× ${task.productName}")
                Text(task.fulfillmentStation?.stationLabel() ?: "Estação não informada")
                Text(task.destinationLabel.ifBlank { "Destino não informado" })
                Text("Tarefa ${task.id.take(8)} · ${task.state}")
                task.orderItemId?.let { Text("Item ${it.take(8)}") }
                Text("Abrir não assume nem conclui esta entrega.")
                (task.target as? StaffTaskTarget.Tab)?.let { target ->
                    TextButton(onClick = { onOpenTab(target.tabId) }, enabled = !busy) { Text("Abrir comanda") }
                }
                if (task.claimedById != null && task.claimedById != staffId) Text("Outro operador está responsável. Atualize ou peça revisão.")
                TextButton(onClick = onComplete, enabled = !busy && (task.claimedById == null || task.claimedById == staffId)) { Text("Registrar entrega por exceção") }
            }
        }
    }, confirmButton = { TextButton(onClick = onDismiss) { Text("Voltar à fila") } })
}
