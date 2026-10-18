package com.rodada.attendance.operations

import androidx.activity.compose.BackHandler
import com.rodada.attendance.ui.AttendanceUx2
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.clickable
import androidx.compose.material3.HorizontalDivider
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
    partySizeEditor: @Composable (String) -> Unit = {},
    onOpenStandaloneTab: () -> Unit = {},
    onOpenFirstTab: (String, String) -> Unit = { _, _ -> },
    onLoadHistory: () -> Unit = {},
    requestedTarget: StaffTaskTarget.Table? = null,
    onTargetConsumed: () -> Unit = {},
    onDetailVisibility: (Boolean) -> Unit = {},
    onViewDeliveries: () -> Unit = {},
) {
    var search by rememberSaveable { mutableStateOf("") }
    var showHistory by rememberSaveable { mutableStateOf(false) }
    var expandedTableId by rememberSaveable { mutableStateOf<String?>(null) }
    LaunchedEffect(requestedTarget, state.tables) {
        if (requestedTarget != null) {
            expandedTableId = requestedTarget.currentTable(state.tables)?.id
            onTargetConsumed()
        }
    }
    LaunchedEffect(expandedTableId) { onDetailVisibility(expandedTableId != null) }
    androidx.compose.runtime.DisposableEffect(Unit) { onDispose { onDetailVisibility(false) } }
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
    val visibleTables = state.tables.filter { table -> !showHistory &&
            (search.isBlank() || listOfNotNull(table.label, table.zone?.label).any { it.contains(search, true) } ||
                table.activeOccupancy?.tabs.orEmpty().any { it.displayLabel.contains(search, true) || it.displayReference.contains(search, true) })
    }
    val columns = if (LocalDensity.current.fontScale > 1.3f) 1 else 2
    val otherTabs = (if (showHistory) state.historyTabs else state.tabs).filter {
        (showHistory || it.id !in attachedTabIds) &&
            (if (showHistory) it.state in setOf("CLOSED", "CANCELLED") else it.state !in setOf("CLOSED", "CANCELLED")) &&
            it.matchesOperationalQuery(search)
    }
    val locked = state.loading || state.submitting || state.pendingTableService != null

    BackHandler(enabled = expandedTableId != null) { if (!locked) expandedTableId = null }
    if (expandedTableId == null) {
    LazyColumn(
        modifier = Modifier.padding(horizontal = 20.dp).testTag("tables-list"),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Column(Modifier.weight(1f).padding(top = 27.dp)) {
                    Ux2Eyebrow("Encontrar destino")
                    Ux2Title("Mesas e\ncomandas.")
                    Text("Uma busca, sem filtros de status nem formulários na lista.", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
                }
                TextButton(onClick = { showHistory = !showHistory; if (showHistory) onLoadHistory() }, enabled = !locked, modifier = Modifier.heightIn(min = 48.dp).semantics { contentDescription = if (showHistory) "Voltar às mesas" else "Histórico de comandas" }) { Text(if (showHistory) "Voltar" else "↶") }
            }
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(search, { search = it }, placeholder = { Text("Mesa, nome ou comanda") }, modifier = Modifier.fillMaxWidth().semantics { contentDescription = "Buscar mesa ou comanda" }, singleLine = true)
            Text("Mesas", style = AttendanceUx2.text(18, 800), modifier = Modifier.padding(top = 16.dp))

        }
        if (!canManageTables) {
            item { Text("Seu acesso atual não permite alterar ocupação ou limpeza.") }
        }
        if (state.loading && state.tables.isEmpty()) item { Text("Carregando mesas…") }
        if (!state.loading && state.tables.isEmpty()) item { Text("Nenhuma mesa cadastrada.") }
        if (!showHistory && !state.loading && state.tables.isNotEmpty() && visibleTables.isEmpty()) item { Text("Nenhuma mesa encontrada. Ajuste a busca.") }
        items(visibleTables.chunked(columns), key = { row -> row.joinToString { it.id } }) { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                row.forEach { table ->
                    Card(onClick = { expandedTableId = table.id }, enabled = !locked,
                        shape = RoundedCornerShape(8.dp), border = BorderStroke(1.dp, RodadaVisual.Border),
                        colors = CardDefaults.cardColors(containerColor = RodadaVisual.Control, contentColor = RodadaVisual.Paper),
                        modifier = Modifier.weight(1f).heightIn(min = 115.dp).testTag("table-${table.id}")) {
                        Column(Modifier.padding(horizontal = 13.dp, vertical = 15.dp), verticalArrangement = Arrangement.spacedBy(17.dp)) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("Mesa ${table.label}", style = AttendanceUx2.text(21, 850))
                                Text("${table.activeOccupancy?.tabs?.count { it.state !in setOf("CLOSED", "CANCELLED") } ?: 0}", style = AttendanceUx2.text(11, 750), color = RodadaVisual.Muted)
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(7.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                                TableStatusIcon(tableStatusColor(table.status))
                                Text(table.status.tableStatusLabel(), style = AttendanceUx2.text(11), color = RodadaVisual.Muted)
                            }
                        }
                    }
                }
                if (row.size < columns) Spacer(Modifier.weight(1f))
            }
        }

        item {
            Text(if (showHistory) "Histórico de comandas" else "Comandas sem mesa", style = AttendanceUx2.text(18, 800))
            if (showHistory && state.historyLoading) Text("Carregando histórico…")
            if (showHistory && state.historyError != null) Text(state.historyError, color = MaterialTheme.colorScheme.error)
            if (otherTabs.isEmpty() && (!showHistory || state.historyLoaded && !state.historyLoading)) Text(if (showHistory) "Nenhuma comanda no histórico disponível." else if (search.isBlank()) "Nenhuma comanda aberta fora das mesas." else "Nenhuma outra comanda encontrada.")
        }
        items(otherTabs, key = { "tab:${it.id}" }) { tab ->
            OutlinedButton(onClick = { onSelectTab(tab.id) }, enabled = !locked, modifier = Modifier.fillMaxWidth().testTag("other-tab-${tab.id}")) {
                Column(Modifier.fillMaxWidth()) { Text(tab.operationalLabel(historical = showHistory)); Text(tab.operationalSubtitle(historical = showHistory), style = MaterialTheme.typography.bodySmall) }
            }
        }
        item {
            if (canOpenTabs && !showHistory) Ux2Action("Abrir comanda sem mesa", !locked, onOpenStandaloneTab)
            Spacer(Modifier.height(12.dp))
        }
    }
    }

    state.tables.firstOrNull { it.id == expandedTableId }?.let { table ->
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
            TextButton(onClick = { expandedTableId = null }, enabled = !locked, modifier = Modifier.heightIn(min = 44.dp)) { Text("Voltar") }
            Text(table.zone?.label.orEmpty().uppercase(), style = AttendanceUx2.text(11, 800), color = RodadaVisual.Amber)
            Column {
            TableCard(
                table = table,
                balances = state.tabs.associate { it.id to it.exposureCents },
                pendingDeliveries = state.deliveryTasks.count { task -> task.state in setOf("OPEN", "CLAIMED") && (task.target as? StaffTaskTarget.Table)?.currentTable(listOf(table)) != null },
                onViewDeliveries = onViewDeliveries,
                busy = locked,
                canManage = canManageTables,
                onOccupy = { if (table.tableServiceEnabled) onStartService(table.id) else occupyingTableId = table.id },
                staffId = staffId,
                canOpenTabs = canOpenTabs && table.tableServiceEnabled,
                onNewTab = { newLabel = ""; openingOccupancy = it.id },
                onClaim = { if (it.responsibleStaffId != null && it.responsibleStaffId != staffId) takingOccupancy = it.id else onClaim(it) },
                onSelectTab = onSelectTab,
                onAttach = { attachingOccupancyId = it },
                onRelease = {
                    table.activeOccupancy?.takeIf { occupancy -> occupancy.tabs.none { it.state !in setOf("CLOSED", "CANCELLED") } && state.deliveryTasks.none { task -> task.state in setOf("OPEN", "CLAIMED") && (task.target as? StaffTaskTarget.Table)?.currentTable(listOf(table)) != null } }?.let {
                        releasingTableId = table.id
                        releasingOccupancyId = it.id
                        releasingGeneration = it.generation
                        releasingLabel = table.label
                    }
                },
                onStartCleaning = { onStartCleaning(table.id) },
                onCompleteCleaning = { returnTableId = table.id; returnStatus = "AVAILABLE"; onCompleteCleaning(table.id) },
                partySizeEditor = partySizeEditor,
                onNewFirstTab = { newLabel = ""; openingTableId = table.id },
            )
            }
        }
    }

    openingTableId?.let { tableId ->
        AlertDialog(onDismissRequest = { if (!locked) openingTableId = null }, title = { Text("Nova comanda na mesa ${state.tables.firstOrNull { it.id == tableId }?.label.orEmpty()}") },
            text = { Column { Text("A mesa será ocupada junto com a abertura da comanda."); OutlinedTextField(newLabel, { newLabel = it.take(120) }, label = { Text("Nome ou apelido") }, enabled = !locked) } },
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
            title = { Text("＋ Abrir nova comanda") }, text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Informe o nome ou apelido para identificar a comanda.")
                    androidx.compose.material3.OutlinedTextField(
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
    balances: Map<String, Long>,
    pendingDeliveries: Int,
    onViewDeliveries: () -> Unit,
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
    partySizeEditor: @Composable (String) -> Unit,
    onNewFirstTab: () -> Unit,
) {
    var managementExpanded by rememberSaveable(table.id) { mutableStateOf(false) }
    val openTabs = table.activeOccupancy?.tabs?.count { it.state !in setOf("CLOSED", "CANCELLED") } ?: 0
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column(Modifier.weight(1f)) {
                Ux2Title("Mesa ${table.label}")
                Text(table.status.tableStatusLabel(), style = AttendanceUx2.text(13), color = RodadaVisual.Muted)
            }
            Text("$openTabs aberta(s)", style = AttendanceUx2.text(11, 750), modifier = Modifier.background(RodadaVisual.Control, RoundedCornerShape(5.dp)).padding(8.dp))
        }
        if (table.status in setOf("DIRTY", "CLEANING")) {
            Text(if (table.status == "DIRTY") "Aguardando limpeza" else "Em limpeza", style = AttendanceUx2.text(16, 800))
            Text(if (table.status == "DIRTY") "A mesa está liberada, mas ainda não está pronta para outro grupo." else "Quando terminar, marque a mesa como pronta.", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
            if (canManage) Ux2Action(if (table.status == "DIRTY") "Iniciar limpeza" else "Mesa limpa · Disponibilizar", !busy, if (table.status == "DIRTY") onStartCleaning else onCompleteCleaning, table.status == "CLEANING")
        }
        Text("Comandas desta mesa", style = AttendanceUx2.text(18, 800))
        val tabs = table.activeOccupancy?.tabs.orEmpty()
        if (tabs.isEmpty()) Text("Sem ocupação ativa", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
        tabs.forEach { tab ->
            Column {
                HorizontalDivider(color = RodadaVisual.Border)
                Row(Modifier.fillMaxWidth().clickable(enabled = !busy && tab.state != "CANCELLED", role = androidx.compose.ui.semantics.Role.Button) { onSelectTab(tab.id) }.heightIn(min = 72.dp).padding(vertical = 14.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(tab.displayLabel.ifBlank { tab.displayReference }, style = AttendanceUx2.text(17, 800))
                        Text("${tab.displayReference} · ${if (tab.state == "CLOSED") "Encerrada" else "Mesa ${table.label}"}", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                    }
                    Text("${balances[tab.id]?.let(::formatCents) ?: "Ver conta"}  ›", style = AttendanceUx2.text(15, 800).copy(fontFamily = RodadaVisual.Number))
                }
                HorizontalDivider(color = RodadaVisual.Border)
            }
        }
        if (table.status == "OCCUPIED") {
            Text("Saída do grupo", style = AttendanceUx2.text(18, 800))
            if (openTabs > 0) Text("$openTabs comanda(s) abertas. Encerre cada uma para liberar a mesa.", style = AttendanceUx2.text(14), color = RodadaVisual.Amber, modifier = Modifier.background(RodadaVisual.Surface, RoundedCornerShape(10.dp)).padding(14.dp))
            else if (pendingDeliveries > 0) {
                Text("$pendingDeliveries entrega(s) ainda prontas. Resolva as entregas antes de liberar.", style = AttendanceUx2.text(14), color = RodadaVisual.Amber)
                Ux2Action("Ver entregas prontas", !busy, onViewDeliveries)
            } else if (canManage) {
                Ux2Action("Grupo saiu · Liberar mesa", !busy, onRelease, true)
                Text("A mesa passará para Aguardando limpeza e o QR desta ocupação perderá o acesso.", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
            }
        }
        if (canOpenTabs) Ux2Action("＋ Abrir nova comanda", !busy && table.status in setOf("AVAILABLE", "OCCUPIED"), {
            table.activeOccupancy?.let(onNewTab) ?: onNewFirstTab()
        })
        if (table.guestOrderingBlocked) Text("Pedidos por QR bloqueados", color = MaterialTheme.colorScheme.error)
        if (canManage) {
            TextButton(onClick = { managementExpanded = !managementExpanded }) { Text("Opções da mesa") }
            if (managementExpanded) {
                table.activeOccupancy?.let { occupancy ->
                    androidx.compose.runtime.key(occupancy.id) { partySizeEditor(occupancy.id) }
                    OutlinedButton(onClick = { onAttach(occupancy.id) }, enabled = !busy) { Text("Vincular comanda existente") }
                    if (table.tableServiceEnabled && occupancy.responsibleStaffId != staffId) OutlinedButton(onClick = { onClaim(occupancy) }, enabled = !busy) { Text("Assumir atendimento${occupancy.responsibleStaffName?.let { " de $it" } ?: ""}") }
                }
                if (table.status == "AVAILABLE") OutlinedButton(onClick = onOccupy, enabled = !busy) { Text(if (table.tableServiceEnabled) "Iniciar atendimento sem comanda" else "Ocupar mesa") }
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
