package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
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
) {
    var occupyingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var openingOccupancy by rememberSaveable { mutableStateOf<String?>(null) }
    var takingOccupancy by rememberSaveable { mutableStateOf<String?>(null) }
    var newLabel by rememberSaveable { mutableStateOf("") }
    var showOptionalName by rememberSaveable { mutableStateOf(false) }
    var attachingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingGeneration by rememberSaveable { mutableStateOf<Int?>(null) }
    var releasingLabel by rememberSaveable { mutableStateOf("") }
    val attachedTabIds = state.tables.flatMap { it.activeOccupancy?.tabs.orEmpty() }.map { it.id }.toSet()
    var movingTabId by rememberSaveable { mutableStateOf<String?>(null) }
    val assignableTabs = state.tabs.filter { it.state !in setOf("CLOSED", "CANCELLED") && (canMoveTabs || it.id !in attachedTabIds) }

    LazyColumn(
        modifier = Modifier.padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Text("Mesas", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text("Mesa é contexto físico. Cada comanda mantém seu próprio saldo.")
        }
        if (!canManageTables) {
            item { Text("Seu acesso atual não permite alterar ocupação ou limpeza.") }
        }
        if (state.loading && state.tables.isEmpty()) item { Text("Carregando mesas…") }
        if (!state.loading && state.tables.isEmpty()) item { Text("Nenhuma mesa cadastrada.") }
        items(state.tables, key = { it.id }) { table ->
            TableCard(
                table = table,
                busy = state.submitting || state.pendingTableService != null,
                canManage = canManageTables,
                onOccupy = { if (table.tableServiceEnabled) onStartService(table.id) else occupyingTableId = table.id },
                staffId = staffId,
                canOpenTabs = canOpenTabs && table.tableServiceEnabled,
                onNewTab = { newLabel = ""; showOptionalName = false; openingOccupancy = it.id },
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
                onCompleteCleaning = { onCompleteCleaning(table.id) },
                partySizeEditor = partySizeEditor,
            )
        }
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
                    Text("A mesa já está selecionada. Você pode abrir a comanda sem informar o nome.")
                    TextButton(onClick = { showOptionalName = !showOptionalName },
                        enabled = !state.submitting && state.pendingTableService == null) {
                        Text(if (showOptionalName) "Ocultar nome" else "Adicionar nome ou apelido (opcional)")
                    }
                    if (showOptionalName) androidx.compose.material3.OutlinedTextField(
                        value = newLabel, onValueChange = { newLabel = it.take(120) },
                        label = { Text("Nome ou apelido (opcional)") },
                        enabled = !state.submitting && state.pendingTableService == null,
                    )
                }
            }, confirmButton = { Button(enabled = !state.submitting && state.pendingTableService == null, onClick = { onOpenTableTab(occupancy, newLabel); openingOccupancy = null }) { Text("Abrir e pedir") } },
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
    partySizeEditor: @Composable (String) -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Mesa ${table.label}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text(table.status.tableStatusLabel(), fontWeight = FontWeight.Bold)
            }
            table.activeOccupancy?.let { occupancy ->
                Text("Em uso · ${occupancy.tabs.size} comanda${if (occupancy.tabs.size == 1) "" else "s"}")
                Text(if (occupancy.responsibleStaffId == staffId) "Atendimento: você" else occupancy.responsibleStaffName?.let { "Atendimento: $it" } ?: "Sem responsável")
                if (occupancy.serviceAttention in setOf("UNASSIGNED_GUEST_ORDER", "UNASSIGNED_READY")) {
                    Text("Pedido via QR · Sem responsável", fontWeight = FontWeight.Bold)
                    Text("${occupancy.guestOrderCount} pedido(s) · ${if (occupancy.serviceAttention == "UNASSIGNED_READY") "Pedido pronto" else "Confirmado"}")
                    Text(serviceOrderAgeLabel(occupancy.oldestGuestOrderAt))
                }
                occupancy.tabs.forEach { tab -> OutlinedButton(onClick = { onSelectTab(tab.id) }, enabled = !busy && tab.state !in setOf("CLOSED", "CANCELLED"), modifier = Modifier.fillMaxWidth()) { Text("${tab.displayLabel.takeUnless { it.isBlank() || it == "Comanda sem nome" }?.let { "$it · " } ?: ""}${tab.displayReference.ifBlank { "Comanda ${tab.id.take(8)}" }}") } }
                if (canOpenTabs) Button(onClick = { onNewTab(occupancy) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Nova comanda nesta mesa") }
                if (canManage && table.tableServiceEnabled && occupancy.responsibleStaffId != staffId) OutlinedButton(onClick = { onClaim(occupancy) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Assumir atendimento${occupancy.responsibleStaffName?.let { " de $it" } ?: ""}") }
            } ?: Text("Sem ocupação ativa")
            if (table.guestOrderingBlocked) Text("Pedidos por QR bloqueados", color = MaterialTheme.colorScheme.error)
            if (!canManage) return@Column
            table.activeOccupancy?.let { occupancy -> androidx.compose.runtime.key(occupancy.id) { partySizeEditor(occupancy.id) } }
            when (table.status) {
                "AVAILABLE" -> Button(onClick = onOccupy, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text(if (table.tableServiceEnabled) "Iniciar atendimento" else "Ocupar mesa") }
                "OCCUPIED" -> {
                    table.activeOccupancy?.let { occupancy ->
                        OutlinedButton(onClick = { onAttach(occupancy.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text("Vincular comanda existente")
                        }
                    }
                    Button(onClick = onRelease, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Liberar mesa") }
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
        "AVAILABLE" -> "DISPONÍVEL"
        "OCCUPIED" -> "EM USO"
        "DIRTY" -> "AGUARDA LIMPEZA"
        "CLEANING" -> "LIMPANDO"
        "OUT_OF_SERVICE" -> "FORA DE SERVIÇO"
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
