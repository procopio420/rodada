package com.rodada.attendance.operations

import androidx.compose.runtime.LaunchedEffect

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rodada.attendance.ui.AttendanceUx2
import com.rodada.attendance.ui.RodadaVisual

/** Production two-queue UX2 surface. Callbacks only open work; no claim/completion on tap. */
@Composable
internal fun AttendanceNowScreen(
    state: OperationsUiState,
    onOpenService: (ServiceRequest) -> Unit,
    onOpenDelivery: (DeliveryTask) -> Unit,
    initiallyShowDeliveries: Boolean = false,
) {
    var deliveries by rememberSaveable { mutableStateOf(initiallyShowDeliveries) }
    LaunchedEffect(initiallyShowDeliveries) { if (initiallyShowDeliveries) deliveries = true }
    val servicesScroll = rememberLazyListState()
    val deliveriesScroll = rememberLazyListState()
    val servicesKnown = state.serviceRequestsFresh && state.connectivity == ConnectivityState.ONLINE
    val deliveriesKnown = state.deliveryTasksFresh && !state.loading && state.connectivity == ConnectivityState.ONLINE
    val horizontalInset = if (LocalConfiguration.current.screenWidthDp <= 375) 15.dp else 20.dp
    LazyColumn(state = if (deliveries) deliveriesScroll else servicesScroll,
        modifier = Modifier.fillMaxSize().testTag("attendance-now-content"),
        contentPadding = PaddingValues(start = horizontalInset, end = horizontalInset, top = 24.dp, bottom = 53.dp)) {
        item {
            Text("FILA OPERACIONAL", style = AttendanceUx2.text(10, 850).copy(letterSpacing = 1.5.sp), color = RodadaVisual.Amber)
            Spacer(Modifier.height(9.dp))
            Text("Agora", style = AttendanceUx2.text(28, 900, 31.36f).copy(letterSpacing = (-1.54).sp), modifier = Modifier.semantics { heading() })
            Spacer(Modifier.height(16.dp))
            Surface(shape = RoundedCornerShape(10.dp), color = RodadaVisual.Surface, border = BorderStroke(1.dp, RodadaVisual.Border)) {
                Row(Modifier.fillMaxWidth().padding(5.dp), horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                    @Composable fun Choice(label: String, count: String, chosen: Boolean, action: () -> Unit) {
                        Surface(Modifier.weight(1f).heightIn(min = 50.dp).testTag("now-queue-$label")
                            .semantics { selected = chosen }.clickable(role = Role.Button, onClick = action),
                            shape = RoundedCornerShape(7.dp), color = if (chosen) RodadaVisual.Control else RodadaVisual.Surface,
                            border = if (chosen) BorderStroke(1.dp, RodadaVisual.StrongBorder) else null) {
                            Row(Modifier.padding(horizontal = 4.dp), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                                Text(label, modifier = Modifier.weight(1f, fill = false), textAlign = TextAlign.Center,
                                    style = AttendanceUx2.text(13, 820), color = if (chosen) RodadaVisual.Paper else RodadaVisual.Muted)
                                Text(" $count", style = AttendanceUx2.text(11, 750).copy(fontFamily = RodadaVisual.Number), color = RodadaVisual.Amber)
                            }
                        }
                    }
                    Choice("Atendimentos", if (servicesKnown) state.serviceRequests.size.toString() else "—", !deliveries) { deliveries = false }
                    Choice("Entregas", if (deliveriesKnown) state.deliveryTasks.size.toString() else "—", deliveries) { deliveries = true }
                }
            }
            Spacer(Modifier.height(18.dp))
            Text(if (deliveries) "Prontos para levar" else "Chamados e pedidos de conta", style = AttendanceUx2.text(17, 800).copy(letterSpacing = (-.425).sp), modifier = Modifier.semantics { heading() })
            Spacer(Modifier.height(8.dp))
            if (deliveries) {
                Text("Fila separada do atendimento. Confira item, estação e destino antes de levar.", style = AttendanceUx2.text(13), color = RodadaVisual.Muted)
                Spacer(Modifier.height(13.dp))
            }
            val fresh = if (deliveries) deliveriesKnown else servicesKnown
            if (!fresh) {
                Text(if (state.loading || (deliveries && state.deliveryTasksLoading)) "Atualizando fila…" else if (!deliveries) state.serviceRequestsError ?: "Chamados desatualizados. Atualize para conferir."
                    else state.deliveryTasksError ?: "Entregas desatualizadas. Atualize para conferir.", style = AttendanceUx2.text(12), color = RodadaVisual.Amber,
                    modifier = Modifier.padding(vertical = 8.dp).testTag("now-queue-freshness"))
            }
        }
        if (!deliveries) items(state.serviceRequests, key = { "service-${it.id}" }) { task ->
            val tab = (task.target as? StaffTaskTarget.Tab)?.let { target -> state.tabs.firstOrNull { it.id == target.tabId } }
            val table = (task.target as? StaffTaskTarget.Table)?.currentTable(state.tables)
            val title = tab?.displayLabel?.takeIf { it.isNotBlank() }?.let { "$it · ${task.destination}" } ?: task.destination
            val action = when (task.target) {
                is StaffTaskTarget.Tab -> if (task.type == "BILL_REQUEST") "Abrir conta" else "Atender cliente"
                is StaffTaskTarget.Table -> "Escolher comanda"
                StaffTaskTarget.Unavailable -> "Vínculo indisponível"
            }
            QueueRow(type = if (task.type == "BILL_REQUEST") "PEDIDO DE CONTA" else "ATENDIMENTO", age = task.ageSeconds,
                title = title, detail = when {
                    task.target is StaffTaskTarget.Tab -> "Comanda ${task.target.tabId.take(8)}"
                    table != null -> "Seleção necessária · ${table.activeOccupancy?.tabs?.size ?: 0} comanda(s) nessa mesa"
                    else -> "Confira o vínculo autorizado desta chamada"
                }, action = action, typeColor = if (task.type == "BILL_REQUEST") RodadaVisual.Info else RodadaVisual.Amber,
                tag = "service-${task.id}") { onOpenService(task) }
        }
        if (deliveries) items(state.deliveryTasks.sortedByDescending { it.ageSeconds }, key = { "delivery-${it.id}" }) { task ->
            QueueRow(type = "PEDIDO PRONTO", age = task.ageSeconds, title = "${task.quantity}× ${task.productName}",
                detail = listOfNotNull(task.fulfillmentStation?.stationLabel(), task.destinationLabel.takeIf { it.isNotBlank() }).joinToString(" · ").ifBlank { "Destino não informado" },
                action = "Ver entrega", typeColor = RodadaVisual.Success, tag = "delivery-${task.id}") { onOpenDelivery(task) }
        }
        val empty = if (deliveries) state.deliveryTasks.isEmpty() && deliveriesKnown else state.serviceRequests.isEmpty() && servicesKnown
        if (empty) item {
            Surface(shape = RoundedCornerShape(12.dp), border = BorderStroke(1.dp, RodadaVisual.StrongBorder), color = RodadaVisual.Ground) {
                Text("Nenhuma tarefa nesta fila. Selecione a outra categoria para conferir.", style = AttendanceUx2.text(14),
                    color = RodadaVisual.Muted, modifier = Modifier.padding(21.dp))
            }
        }
    }
}

internal fun String.stationLabel() = when (this) { "BAR" -> "Bar"; "KITCHEN" -> "Cozinha"; else -> this }

@Composable
private fun QueueRow(type: String, age: Long?, title: String, detail: String, action: String,
    typeColor: androidx.compose.ui.graphics.Color, tag: String, onOpen: () -> Unit) {
    Column(Modifier.fillMaxWidth().heightIn(min = 94.dp).clickable(role = Role.Button, onClick = onOpen)
        .testTag(tag).padding(vertical = 14.dp)) {
        FlowRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            Text(type, style = AttendanceUx2.text(11, 820), color = typeColor)
            Text("·", style = AttendanceUx2.text(11, 820), color = RodadaVisual.Muted)
            Text(age?.let { if (it < 60) "agora" else "há ${it / 60} min" } ?: "tempo não informado", style = AttendanceUx2.text(11, 820), color = RodadaVisual.Muted)
        }
        Spacer(Modifier.height(7.dp))
        Text(title, style = AttendanceUx2.text(17, 850, 22.1f).copy(letterSpacing = (-.255).sp))
        Spacer(Modifier.height(5.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(detail, style = AttendanceUx2.text(12), color = RodadaVisual.Muted, modifier = Modifier.weight(1f))
            Text("$action ›", style = AttendanceUx2.text(12, 800), textAlign = TextAlign.End)
        }
    }
    HorizontalDivider(color = RodadaVisual.Border, thickness = 1.dp)
}
