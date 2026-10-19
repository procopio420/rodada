package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
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
                        if (task.claimedById != staffId) TextButton(onClick = { onAction(false) }, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Assumir chamada", modifier = Modifier.fillMaxWidth(), textAlign = androidx.compose.ui.text.style.TextAlign.Center) }
                        TextButton(onClick = { onAction(true) }, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Concluir chamada", modifier = Modifier.fillMaxWidth(), textAlign = androidx.compose.ui.text.style.TextAlign.Center) }
                    }
                } else {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        if (task.claimedById != staffId) TextButton(onClick = { onAction(false) }, enabled = enabled, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Assumir chamada", modifier = Modifier.fillMaxWidth(), textAlign = androidx.compose.ui.text.style.TextAlign.Center) }
                        TextButton(onClick = { onAction(true) }, enabled = enabled, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Concluir chamada", modifier = Modifier.fillMaxWidth(), textAlign = androidx.compose.ui.text.style.TextAlign.Center) }
                    }
                }
            }
        }
    }
}

@Composable
internal fun DeliveryTaskDetail(task: DeliveryTask?, busy: Boolean, staffId: String, onDismiss: () -> Unit,
    onOpenTab: (String) -> Unit, onComplete: () -> Unit) {
    androidx.activity.compose.BackHandler { onDismiss() }
    val horizontalInset = if (LocalConfiguration.current.screenWidthDp <= 375) 15.dp else 20.dp
    Column(Modifier.fillMaxSize()) {
        Column(Modifier.weight(1f).padding(horizontal = horizontalInset).padding(top = 12.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(13.dp)) {
            TextButton(onClick = onDismiss, contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) {
                Text("‹  Voltar", style = com.rodada.attendance.ui.AttendanceUx2.text(14), color = RodadaVisual.Muted)
            }
            Spacer(Modifier.height(8.dp))
            Ux2Eyebrow("Produção · pedido pronto")
            val titleSize = if (LocalConfiguration.current.screenWidthDp <= 375) 30 else 34
            Text("Levar pedido.", style = com.rodada.attendance.ui.AttendanceUx2.text(titleSize, 900, titleSize * 1.05f).copy(letterSpacing = (-titleSize * .055f).sp), modifier = Modifier.semantics { heading() })
            if (task == null) {
                Text("Tarefa ausente da fila atual. Isso não comprova entrega; confira o histórico original.", color = RodadaVisual.Muted)
            } else {
                Text(listOf(task.destinationLabel.ifBlank { "Destino não informado" }, task.tabLabel, task.tabReference.orEmpty()).filter { it.isNotBlank() }.joinToString(" · "),
                    style = com.rodada.attendance.ui.AttendanceUx2.text(14), color = RodadaVisual.Muted)
                Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(topEnd = 8.dp, bottomEnd = 8.dp)).drawBehind { drawLine(RodadaVisual.Amber, Offset(1.5.dp.toPx(), 0f), Offset(1.5.dp.toPx(), size.height), 3.dp.toPx()) }.padding(horizontal = 15.dp, vertical = 13.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(when (task.itemState) { "READY" -> "Pronto para entrega"; "PICKED_UP" -> "Em entrega"; else -> "Confira o estado da entrega" }, style = com.rodada.attendance.ui.AttendanceUx2.text(14, 800), color = RodadaVisual.Paper)
                    Text(if (task.itemState in setOf("READY", "PICKED_UP")) if (task.itemState == "READY") "Os itens abaixo estão marcados como prontos na produção. Abrir a tarefa não conclui a entrega." else "Os itens abaixo estão em entrega. Abrir a tarefa não conclui a entrega." else "O estado de produção mudou ou não foi informado. Atualize antes de agir; abrir não conclui a entrega.", style = com.rodada.attendance.ui.AttendanceUx2.text(13), color = RodadaVisual.Muted)
                }
                Text("O que levar", style = com.rodada.attendance.ui.AttendanceUx2.text(18, 800))
                Row(Modifier.fillMaxWidth().padding(vertical = 18.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        Text("${task.quantity}× ${task.productName}", style = com.rodada.attendance.ui.AttendanceUx2.text(16, 800))
                        Text("Origem · ${task.fulfillmentStation?.stationLabel() ?: "Estação não informada"}", style = com.rodada.attendance.ui.AttendanceUx2.text(12), color = RodadaVisual.Muted)
                    }
                    Text(when (task.itemState) { "READY" -> "Pronto"; "PICKED_UP" -> "Em entrega"; "DELIVERED" -> "Entregue"; else -> "Não confirmado" }, color = RodadaVisual.Amber,
                        modifier = Modifier.background(RodadaVisual.Surface, RoundedCornerShape(5.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(5.dp)).padding(horizontal = 8.dp, vertical = 6.dp),
                        style = com.rodada.attendance.ui.AttendanceUx2.text(11, 800))
                }
                HorizontalDivider(color = RodadaVisual.StrongBorder)
                Text("Confirme a entrega somente depois de entregar. A ação exige atualização canônica da tarefa e do item correto, com proteção contra repetição.",
                    modifier = Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(9.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(9.dp)).padding(13.dp), style = com.rodada.attendance.ui.AttendanceUx2.text(12), color = RodadaVisual.Muted)
                if (task.claimedById != null && task.claimedById != staffId) Text("Outro operador está responsável. Atualize ou peça revisão.", color = RodadaVisual.Amber)
                Ux2Action("Voltar sem concluir", true, onDismiss)
                (task.target as? StaffTaskTarget.Tab)?.let { target ->
                    TextButton(onClick = { onOpenTab(target.tabId) }, enabled = !busy) { Text("Abrir comanda") }
                }
            }
            Spacer(Modifier.height(20.dp))
        }
        if (task != null) Column(Modifier.fillMaxWidth().padding(horizontal = horizontalInset, vertical = 12.dp)) {
            Ux2Action("Registrar entrega por exceção", !busy && task.itemState in setOf("READY", "PICKED_UP") && task.state in setOf("OPEN", "CLAIMED") && (task.claimedById == null || task.claimedById == staffId), onComplete, true)
        }
    }
}
