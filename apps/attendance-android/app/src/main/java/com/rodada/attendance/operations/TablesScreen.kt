package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CardDefaults
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.window.Dialog
import com.rodada.attendance.ui.rodadaTextFieldColors
import com.rodada.attendance.ui.RodadaButtonTone
import com.rodada.attendance.ui.RodadaVisual
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Spacer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.material3.OutlinedTextField
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import com.rodada.attendance.ui.RodadaButton as Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import com.rodada.attendance.ui.RodadaOutlinedButton as OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun TablesScreen(
    state: OperationsUiState,
    canManageTables: Boolean,
    onAttachTab: (occupancyId: String, tabId: String) -> Unit,
    onRelease: (tableId: String) -> Unit,
    onStartCleaning: (tableId: String) -> Unit,
    onCompleteCleaning: (tableId: String) -> Unit,
    onOccupy: (String, String?) -> Unit = { _, _ -> },
    staffId: String = "",
    canOpenTabs: Boolean = false,
    onStartService: (String) -> Unit = {},
    onOpenTableTab: (TableOccupancy, String) -> Unit = { _, _ -> },
    onClaim: (TableOccupancy) -> Unit = {},
    onSelectTab: (String) -> Unit = {},
    canMoveTabs: Boolean = false,
    onMoveTab: (String, TabSummary) -> Unit = { _, _ -> },
    onOpenStandaloneTab: () -> Unit = {},
    onOpenFirstTab: (String, String) -> Unit = { _, _ -> },
    onLoadHistory: () -> Unit = {},
    onInspectHistory: (String?) -> Unit = {},
) {
    var search by rememberSaveable { mutableStateOf("") }
    var showHistory by rememberSaveable { mutableStateOf(false) }
    var otherExpanded by rememberSaveable { mutableStateOf(false) }
    var expandedTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var returnTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var returnStatus by rememberSaveable { mutableStateOf("") }
    LaunchedEffect(state.tables, returnTableId, returnStatus) {
        if (returnTableId != null && state.tables.any { it.id == returnTableId && it.status == returnStatus }) {
            expandedTableId = null
            returnTableId = null
            returnStatus = ""
        }
    }
    var openingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var occupyingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var openingOccupancy by rememberSaveable { mutableStateOf<String?>(null) }
    var takingOccupancy by rememberSaveable { mutableStateOf<String?>(null) }
    var newLabel by rememberSaveable { mutableStateOf("") }
    var attachingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingGeneration by rememberSaveable { mutableStateOf<Int?>(null) }
    var releasingLabel by rememberSaveable { mutableStateOf("") }
    val attachedTabIds = state.tables.flatMap { it.activeOccupancy?.tabs.orEmpty() }.map { it.id }.toSet()
    var movingTabId by rememberSaveable { mutableStateOf<String?>(null) }
    val assignableTabs = state.tabs.filter { it.state !in setOf("CLOSED", "CANCELLED") && (canMoveTabs || it.id !in attachedTabIds) }
    val visibleTables = state.tables.filter { table ->
            (search.isBlank() || listOfNotNull(table.label, table.zone?.label).any { it.contains(search, true) } ||
                table.activeOccupancy?.tabs.orEmpty().any { it.displayLabel.contains(search, true) || it.displayReference.contains(search, true) })
    }
    val columns = if (LocalDensity.current.fontScale > 1.3f) 1 else 2
    val otherTabs = state.tabs.filter { it.id !in attachedTabIds && it.state !in setOf("CLOSED", "CANCELLED") && it.matchesOperationalQuery(search) }
    val locked = state.loading || state.submitting || state.pendingTableService != null

    Card(Modifier.padding(horizontal = 16.dp).fillMaxWidth(), border = BorderStroke(1.dp, RodadaVisual.Border), colors = CardDefaults.cardColors(containerColor = RodadaVisual.Surface)) {
    LazyColumn(
        modifier = Modifier.padding(12.dp).testTag("tables-list"),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text("Mesas e comandas", modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                TextButton(onClick = { showHistory = true; onInspectHistory(null); onLoadHistory() }, enabled = !locked,
                    modifier = Modifier.heightIn(min = 48.dp).semantics { contentDescription = "Histórico de comandas" }) { Text("↶") }
            }
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(search, { search = it }, colors = rodadaTextFieldColors(), label = { Text("Buscar mesa ou comanda") }, modifier = Modifier.fillMaxWidth(), singleLine = true)

        }
        if (!canManageTables) {
            item { Text("Seu acesso atual não permite alterar ocupação ou limpeza.") }
        }
        if (state.loading && state.tables.isEmpty()) item { Text("Carregando mesas…") }
        if (!state.loading && state.tables.isEmpty()) item { Text("Nenhuma mesa cadastrada.") }
        if (!state.loading && state.tables.isNotEmpty() && visibleTables.isEmpty()) item { Text("Nenhuma mesa encontrada. Ajuste a busca.") }
        items(visibleTables.chunked(columns), key = { row -> row.joinToString { it.id } }) { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                row.forEach { table ->
                    Card(onClick = { expandedTableId = table.id }, enabled = !locked,
                        shape = RoundedCornerShape(8.dp), border = BorderStroke(1.dp, if (table.status == "OCCUPIED") RodadaVisual.OccupiedBorder else RodadaVisual.Border),
                        colors = CardDefaults.cardColors(containerColor = RodadaVisual.Control, contentColor = RodadaVisual.Paper),
                        modifier = Modifier.weight(1f).heightIn(min = 132.dp).testTag("table-${table.id}")) {
                        Box(Modifier.fillMaxWidth().height(4.dp).background(tableStatusColor(table.status)))
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            TableStatusIcon(tableStatusColor(table.status))
                            Text("Mesa ${table.label}", style = MaterialTheme.typography.titleLarge)
                            Text("${table.status.tableStatusLabel()} · ${table.activeOccupancy?.tabs?.count { it.state !in setOf("CLOSED", "CANCELLED") } ?: 0} comandas abertas", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                            table.zone?.let { Text(it.label, style = MaterialTheme.typography.bodySmall) }
                        }
                    }
                }
                if (row.size < columns) Spacer(Modifier.weight(1f))
            }
        }

        item {
            OutlinedButton(onClick = { otherExpanded = !otherExpanded }, modifier = Modifier.fillMaxWidth()) { Text("Outras comandas (${otherTabs.size})") }
            if (otherExpanded && canOpenTabs) OutlinedButton(onClick = onOpenStandaloneTab, enabled = !locked, modifier = Modifier.fillMaxWidth()) { Text("Nova comanda sem mesa") }
            if (otherExpanded && otherTabs.isEmpty()) Text("Nenhuma comanda aberta fora das mesas.")
        }
        items(if (otherExpanded) otherTabs else emptyList(), key = { "tab:${it.id}" }) { tab ->
            OutlinedButton(onClick = { onSelectTab(tab.id) }, enabled = !locked, modifier = Modifier.fillMaxWidth().testTag("other-tab-${tab.id}")) {
                Column(Modifier.fillMaxWidth()) { Text(tab.operationalLabel()); Text(tab.operationalSubtitle(), style = MaterialTheme.typography.bodySmall) }
            }
        }
        item { Spacer(Modifier.height(12.dp)) }
    }
    }

    if (showHistory) TabHistoryDialog(state, onLoadHistory, onInspectHistory,
        onDismiss = { showHistory = false; onInspectHistory(null) })

    state.tables.firstOrNull { it.id == expandedTableId }?.let { table ->
        Dialog(onDismissRequest = { if (!locked) expandedTableId = null }) {
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = RodadaVisual.Surface)) {
                Column(Modifier.verticalScroll(rememberScrollState()).padding(8.dp)) {
            TableCard(
                table = table,
                busy = state.submitting || state.pendingTableService != null,
                canManage = canManageTables,
                onOccupy = { if (table.tableServiceEnabled) onStartService(table.id) else occupyingTableId = table.id },
                staffId = staffId,
                canOpenTabs = canOpenTabs && table.tableServiceEnabled,
                onNewTab = { newLabel = ""; openingOccupancy = it.id },
                onClaim = { if (it.responsibleStaffId != null && it.responsibleStaffId != staffId) takingOccupancy = it.id else onClaim(it) },
                onSelectTab = onSelectTab,
                onAttach = { attachingOccupancyId = it },
                onRelease = {
                    table.activeOccupancy?.let {
                        releasingTableId = table.id
                        releasingOccupancyId = it.id
                        releasingGeneration = it.generation
                        releasingLabel = table.label
                    }
                },
                onStartCleaning = { onStartCleaning(table.id) },
                onCompleteCleaning = { returnTableId = table.id; returnStatus = "AVAILABLE"; onCompleteCleaning(table.id) },
                onNewFirstTab = { newLabel = ""; openingTableId = table.id },
            )
                    OutlinedButton(onClick = { expandedTableId = null }, enabled = !locked, modifier = Modifier.fillMaxWidth()) { Text("Voltar") }
                }
            }
        }
    }

    openingTableId?.let { tableId ->
        AlertDialog(onDismissRequest = { if (!locked) openingTableId = null }, title = { Text("Nova comanda na mesa ${state.tables.firstOrNull { it.id == tableId }?.label.orEmpty()}") },
            text = { Column { Text("A mesa será ocupada junto com a abertura da comanda."); OutlinedTextField(newLabel, { newLabel = it.take(120) }, colors = rodadaTextFieldColors(), label = { Text("Nome ou apelido") }, enabled = !locked) } },
            confirmButton = { Button(onClick = { onOpenFirstTab(tableId, newLabel.trim()); openingTableId = null }, enabled = !locked && newLabel.isNotBlank()) { Text("Abrir e pedir") } },
            dismissButton = { TextButton(onClick = { openingTableId = null }, enabled = !locked) { Text("Cancelar") } })
    }

    releasingTableId?.let { tableId ->
        val current = state.tables.firstOrNull { it.id == tableId }
        val sameOccupancy = current?.status == "OCCUPIED" &&
            current.activeOccupancy?.id == releasingOccupancyId &&
            current.activeOccupancy?.generation == releasingGeneration
        AlertDialog(
            onDismissRequest = { releasingTableId = null },
            title = { Text("Liberar mesa $releasingLabel?") },
            text = {
                Column(modifier = Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("A ocupação será encerrada e o acesso atual dos clientes pelo QR será revogado. A mesa ficará aguardando limpeza.")
                    Text("As comandas e seus saldos permanecem. Esta ação não recebe pagamentos nem fecha comandas.")
                    if (!sameOccupancy) Text("A ocupação mudou. Cancele e confira a mesa novamente.", color = MaterialTheme.colorScheme.error)
                    if (!canManageTables) Text("Seu acesso atual não permite liberar a mesa.")
                }
            },
            confirmButton = {
                TextButton(
                    modifier = Modifier.heightIn(min = 44.dp),
                    enabled = sameOccupancy && canManageTables && !state.submitting,
                    onClick = {
                        if (releasingTableId == tableId && sameOccupancy && canManageTables && !state.submitting) {
                            releasingTableId = null
                            returnTableId = tableId
                            returnStatus = "DIRTY"
                            onRelease(tableId)
                        }
                    },
                ) { Text("Confirmar liberação") }
            },
            dismissButton = { TextButton(onClick = { releasingTableId = null }, modifier = Modifier.heightIn(min = 44.dp)) { Text("Cancelar") } },
        )
    }

    occupyingTableId?.let { tableId ->
        OccupyTableDialog(
            tabs = assignableTabs,
            busy = state.submitting,
            onDismiss = { occupyingTableId = null },
            onOccupy = { tabId ->
                onOccupy(tableId, tabId)
                occupyingTableId = null
            },
        )
    }

    state.tables.mapNotNull { it.activeOccupancy }.firstOrNull { it.id == openingOccupancy }?.let { occupancy ->
        AlertDialog(onDismissRequest = { if (!state.submitting && state.pendingTableService == null) openingOccupancy = null },
            title = { Text("Nova comanda nesta mesa") }, text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Informe o nome ou apelido para identificar a comanda.")
                    androidx.compose.material3.OutlinedTextField(
                        colors = rodadaTextFieldColors(),
                        value = newLabel, onValueChange = { newLabel = it.take(120) },
                        label = { Text("Nome ou apelido") },
                        enabled = !state.submitting && state.pendingTableService == null,
                    )
                }
            }, confirmButton = { Button(enabled = !state.submitting && state.pendingTableService == null && newLabel.isNotBlank(), onClick = { onOpenTableTab(occupancy, newLabel.trim()); openingOccupancy = null }) { Text("Abrir e pedir") } },
            dismissButton = { TextButton(enabled = !state.submitting && state.pendingTableService == null, onClick = { openingOccupancy = null }) { Text("Cancelar") } })
    }
    state.tables.mapNotNull { it.activeOccupancy }.firstOrNull { it.id == takingOccupancy }?.let { occupancy ->
        AlertDialog(onDismissRequest = { takingOccupancy = null }, title = { Text("Assumir atendimento?") },
            text = { Text("${occupancy.responsibleStaffName} está responsável. Você também pode atender sem assumir.") },
            confirmButton = { Button(enabled = !state.submitting && state.pendingTableService == null, onClick = { onClaim(occupancy); takingOccupancy = null }) { Text("Confirmar transferência") } },
            dismissButton = { TextButton(onClick = { takingOccupancy = null }) { Text("Atender sem assumir") } })
    }
    movingTabId?.let { id -> state.tabs.firstOrNull { it.id == id }?.let { tab ->
        val origin = state.tables.firstOrNull { it.activeOccupancy?.tabs?.any { it.id == id } == true }
        val destination = state.tables.firstOrNull { it.activeOccupancy?.id == attachingOccupancyId }
        AlertDialog(onDismissRequest = { movingTabId = null }, title = { Text("Mover comanda?") },
            text = { Text("${tab.displayLabel} · ${tab.id.take(8)}: Mesa ${origin?.label} → Mesa ${destination?.label}. O saldo permanece nesta comanda.") },
            confirmButton = { Button(enabled = !state.submitting && state.pendingTableService == null, onClick = {
                attachingOccupancyId?.let { onMoveTab(it, tab) }; movingTabId = null; attachingOccupancyId = null
            }) { Text("Confirmar mudança de mesa") } },
            dismissButton = { TextButton(onClick = { movingTabId = null }) { Text("Cancelar") } })
    } }
    attachingOccupancyId?.takeIf { movingTabId == null }?.let { occupancyId ->
        AssignTabDialog(
            tabs = assignableTabs.filter { tab -> state.tables.firstOrNull { it.activeOccupancy?.id == occupancyId }?.activeOccupancy?.tabs?.none { it.id == tab.id } != false },
            locations = state.tables.flatMap { table -> table.activeOccupancy?.tabs.orEmpty().map { it.id to "Mesa ${table.label}" } }.toMap(),
            busy = state.submitting,
            onDismiss = { attachingOccupancyId = null },
            onAssign = { tabId ->
                if (tabId in attachedTabIds) movingTabId = tabId
                else { onAttachTab(occupancyId, tabId); attachingOccupancyId = null }
            },
        )
    }
}

@Composable
private fun TableCard(
    table: TableSummary,
    busy: Boolean,
    canManage: Boolean,
    onOccupy: () -> Unit,
    onAttach: (String) -> Unit,
    onRelease: () -> Unit,
    onStartCleaning: () -> Unit,
    onCompleteCleaning: () -> Unit,
    staffId: String,
    canOpenTabs: Boolean,
    onNewTab: (TableOccupancy) -> Unit,
    onClaim: (TableOccupancy) -> Unit,
    onSelectTab: (String) -> Unit,
    onNewFirstTab: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth(), border = BorderStroke(1.dp, RodadaVisual.Border),
        colors = CardDefaults.cardColors(containerColor = RodadaVisual.Surface, contentColor = RodadaVisual.Paper)) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Mesa ${table.label}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text(table.status.tableStatusLabel(), fontWeight = FontWeight.Bold)
            }
            if (table.status in setOf("DIRTY", "CLEANING")) {
                if (canManage) Button(onClick = onCompleteCleaning, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Concluir limpeza") }
                return@Column
            }
            table.activeOccupancy?.let { occupancy ->
                Text("Em uso · ${occupancy.tabs.size} comanda${if (occupancy.tabs.size == 1) "" else "s"}")
                Text(if (occupancy.responsibleStaffId == staffId) "Atendimento: você" else occupancy.responsibleStaffName?.let { "Atendimento: $it" } ?: "Sem responsável")
                if (occupancy.serviceAttention in setOf("UNASSIGNED_GUEST_ORDER", "UNASSIGNED_READY")) {
                    Text("Pedido via QR · Sem responsável", fontWeight = FontWeight.Bold)
                    Text("${occupancy.guestOrderCount} pedido(s) · ${if (occupancy.serviceAttention == "UNASSIGNED_READY") "Pedido pronto" else "Confirmado"}")
                    Text(serviceOrderAgeLabel(occupancy.oldestGuestOrderAt))
                }
                occupancy.tabs.forEach { tab -> OutlinedButton(onClick = { onSelectTab(tab.id) }, tone = RodadaButtonTone.SELECTED, enabled = !busy && tab.state !in setOf("CLOSED", "CANCELLED"), modifier = Modifier.fillMaxWidth()) { Text("${tab.displayLabel.takeUnless { it.isBlank() || it == "Comanda sem nome" }?.let { "$it · " } ?: ""}${tab.displayReference.ifBlank { "Comanda ${tab.id.take(8)}" }}") } }
                if (canOpenTabs) Button(onClick = { onNewTab(occupancy) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Nova comanda nesta mesa") }
                if (canManage && table.tableServiceEnabled && occupancy.responsibleStaffId != staffId) OutlinedButton(onClick = { onClaim(occupancy) }, tone = RodadaButtonTone.CONTEXT, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Assumir atendimento${occupancy.responsibleStaffName?.let { " de $it" } ?: ""}") }
            } ?: Text("Sem ocupação ativa")
            if (table.guestOrderingBlocked) Text("Pedidos por QR bloqueados", color = MaterialTheme.colorScheme.error)
            if (!canManage) return@Column
            when (table.status) {
                "AVAILABLE" -> {
                    if (table.tableServiceEnabled && canOpenTabs) Button(onClick = onNewFirstTab, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Nova comanda nesta mesa") }
                    OutlinedButton(onClick = onOccupy, tone = RodadaButtonTone.CONTEXT, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text(if (table.tableServiceEnabled) "Iniciar atendimento sem comanda" else "Ocupar mesa") }
                }
                "OCCUPIED" -> {
                    table.activeOccupancy?.let { occupancy ->
                        OutlinedButton(onClick = { onAttach(occupancy.id) }, tone = RodadaButtonTone.CONTEXT, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text("Vincular comanda existente")
                        }
                    }
                    OutlinedButton(onClick = onRelease, tone = RodadaButtonTone.CONTEXT, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Liberar mesa") }
                }
                "DIRTY" -> Button(onClick = onStartCleaning, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Iniciar limpeza") }
                "CLEANING" -> Button(onClick = onCompleteCleaning, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Concluir limpeza") }
            }
        }
    }
}

@Composable
private fun AssignTabDialog(
    tabs: List<TabSummary>,
    locations: Map<String, String>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onAssign: (String) -> Unit,
) = AlertDialog(
    onDismissRequest = onDismiss,
    title = { Text("Vincular comanda existente") },
    text = {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (tabs.isEmpty()) Text("Não há comandas abertas disponíveis.")
            tabs.forEach { tab ->
                OutlinedButton(onClick = { onAssign(tab.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text("${tab.displayLabel} · ${tab.id.take(8)} · ${locations[tab.id]?.let { "$it · Mover" } ?: "Sem mesa"}")
                }
            }
        }
    },
    confirmButton = {},
    dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
)

private fun String.tableStatusLabel(): String =
    when (this) {
        "AVAILABLE" -> "Disponível"
        "OCCUPIED" -> "Ocupada"
        "DIRTY" -> "Aguardando limpeza"
        "CLEANING" -> "Em limpeza"
        "OUT_OF_SERVICE" -> "Fora de serviço"
        else -> this
    }

@Composable
private fun OccupyTableDialog(
    tabs: List<TabSummary>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onOccupy: (String?) -> Unit,
) = AlertDialog(
    onDismissRequest = onDismiss,
    title = { Text("Ocupar mesa") },
    text = {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Você pode associar uma comanda agora ou fazê-lo depois.")
            OutlinedButton(onClick = { onOccupy(null) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Ocupar sem comanda") }
            tabs.forEach { tab ->
                OutlinedButton(onClick = { onOccupy(tab.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text("Ocupar com ${tab.displayLabel}")
                }
            }
            if (tabs.isEmpty()) Text("Abra uma comanda para associá-la à mesa.")
        }
    },
    confirmButton = {},
    dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Cancelar") } },
)

internal fun tableStatusColor(status: String): Color = when (status) {
    "AVAILABLE" -> RodadaVisual.Success
    "OCCUPIED" -> RodadaVisual.Info
    "DIRTY", "CLEANING" -> RodadaVisual.Amber
    "OUT_OF_SERVICE" -> RodadaVisual.Danger
    else -> RodadaVisual.Muted
}

@Composable
private fun TableStatusIcon(color: Color) {
    Canvas(Modifier.size(24.dp)) {
        val stroke = 2.dp.toPx()
        drawLine(color, Offset(size.width * .15f, size.height * .35f), Offset(size.width * .85f, size.height * .35f), stroke)
        drawLine(color, Offset(size.width * .15f, size.height * .55f), Offset(size.width * .85f, size.height * .55f), stroke)
        for (x in listOf(.25f, .75f)) drawLine(color, Offset(size.width * x, size.height * .55f), Offset(size.width * x, size.height * .9f), stroke)
        for (x in listOf(.15f, .85f)) drawLine(color, Offset(size.width * x, size.height * .35f), Offset(size.width * x, size.height * .55f), stroke)
    }
}
