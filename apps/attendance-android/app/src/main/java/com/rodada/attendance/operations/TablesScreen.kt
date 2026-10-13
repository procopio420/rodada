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
    onOccupy: (tableId: String, tabId: String?) -> Unit,
    onAttachTab: (occupancyId: String, tabId: String) -> Unit,
    onRelease: (tableId: String) -> Unit,
    onStartCleaning: (tableId: String) -> Unit,
    onCompleteCleaning: (tableId: String) -> Unit,
    partySizeEditor: @Composable (String) -> Unit = {},
) {
    var occupyingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var attachingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingTableId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingOccupancyId by rememberSaveable { mutableStateOf<String?>(null) }
    var releasingGeneration by rememberSaveable { mutableStateOf<Int?>(null) }
    var releasingLabel by rememberSaveable { mutableStateOf("") }
    val attachedTabIds = state.tables.flatMap { it.activeOccupancy?.tabs.orEmpty() }.map { it.id }.toSet()
    val assignableTabs = state.tabs.filter { it.state != "CLOSED" && it.id !in attachedTabIds }

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
                busy = state.submitting,
                canManage = canManageTables,
                onOccupy = { occupyingTableId = table.id },
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
    attachingOccupancyId?.let { occupancyId ->
        AssignTabDialog(
            tabs = assignableTabs,
            busy = state.submitting,
            onDismiss = { attachingOccupancyId = null },
            onAssign = { tabId ->
                onAttachTab(occupancyId, tabId)
                attachingOccupancyId = null
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
                occupancy.tabs.forEach { tab -> Text("• ${tab.displayLabel}") }
            } ?: Text("Sem ocupação ativa")
            if (table.guestOrderingBlocked) Text("Pedidos por QR bloqueados", color = MaterialTheme.colorScheme.error)
            if (!canManage) return@Column
            table.activeOccupancy?.let { occupancy -> androidx.compose.runtime.key(occupancy.id) { partySizeEditor(occupancy.id) } }
            when (table.status) {
                "AVAILABLE" -> Button(onClick = onOccupy, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Ocupar mesa") }
                "OCCUPIED" -> {
                    table.activeOccupancy?.let { occupancy ->
                        OutlinedButton(onClick = { onAttach(occupancy.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text("Adicionar comanda")
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

@Composable
private fun AssignTabDialog(
    tabs: List<TabSummary>,
    busy: Boolean,
    onDismiss: () -> Unit,
    onAssign: (String) -> Unit,
) = AlertDialog(
    onDismissRequest = onDismiss,
    title = { Text("Adicionar comanda") },
    text = {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (tabs.isEmpty()) Text("Não há comandas abertas disponíveis.")
            tabs.forEach { tab ->
                OutlinedButton(onClick = { onAssign(tab.id) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text(tab.displayLabel)
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
