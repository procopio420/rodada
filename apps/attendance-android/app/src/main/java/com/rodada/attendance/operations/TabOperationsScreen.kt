package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.rodada.attendance.auth.StoredSession
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** Cents from the server remain canonical. No financial mutation is replayed automatically. */
@Composable
fun TabOperationsDialog(session: StoredSession, state: OperationsUiState, onDismiss: () -> Unit,
                        onPreview: (JSONObject) -> Unit, onCommit: (JSONObject) -> Unit,
                        onEdit: () -> Unit, onRefresh: () -> Unit) {
    val source = state.operationState
    var kind by remember { mutableStateOf(if (state.selectedTab?.summary?.state == "CLOSED") "REOPEN" else "MOVE_LOCATION") }
    var query by remember { mutableStateOf("") }
    var destination by remember { mutableStateOf<TabSummary?>(null) }
    var newLabel by remember { mutableStateOf("") }
    var occupancyId by remember { mutableStateOf<String?>(null) }
    var pointId by remember { mutableStateOf<String?>(null) }
    var reason by remember { mutableStateOf("") }
    var quantities by remember { mutableStateOf<Map<String, Int>>(emptyMap()) }
    var amounts by remember { mutableStateOf<Map<String, String>>(emptyMap()) }
    var submitted by remember { mutableStateOf<JSONObject?>(null) }
    val busy = state.submitting
    val financial = kind in setOf("SPLIT", "MOVE_ITEMS", "MERGE")
    val pending = state.pendingTabOperation
    LaunchedEffect(source) {
        submitted = null
        quantities = emptyMap()
        amounts = emptyMap()
        destination = null
    }
    val online = state.connectivity == ConnectivityState.ONLINE
    fun changed() { submitted = null; onEdit() }
    fun command(): JSONObject {
        val tab = source!!.getJSONObject("tab")
        return JSONObject().put("kind", kind).put("expected_version", tab.getInt("version"))
            .put("idempotency_key", UUID.randomUUID().toString()).put("reason", reason)
            .apply {
                if (financial) {
                    if (destination != null) put("destination_tab_id", destination!!.id).put("destination_version", destination!!.version)
                    else put("destination_label", newLabel)
                    put("lines", JSONArray().apply {
                        quantities.filterValues { it > 0 }.forEach { (id, quantity) -> put(JSONObject().put("charge_id", id).put("quantity", quantity)) }
                        amounts.filterValues { it.isNotBlank() }.forEach { (id, value) ->
                            if ((quantities[id] ?: 0) == 0) put(JSONObject().put("charge_id", id).put("amount_cents", parseCents(value) ?: 0))
                        }
                    })
                } else if (kind == "MOVE_LOCATION") {
                    put("occupancy_id", occupancyId ?: JSONObject.NULL).put("service_point_id", pointId ?: JSONObject.NULL)
                }
            }
    }
    Dialog(onDismissRequest = { if (!busy) onDismiss() }) {
        Surface(shape = MaterialTheme.shapes.large) {
            LazyColumn(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                item { Text("Operações da comanda", style = MaterialTheme.typography.titleLarge) }
                item {
                    if (state.errorMessage != null) Text(state.errorMessage, color = MaterialTheme.colorScheme.error)
                    if (!online) Text("Atualize a conexão. Operações financeiras exigem o servidor online.")
                    TextButton(onClick = onRefresh, enabled = !busy) { Text("Atualizar dados") }
                }
                if (pending != null) {
                    item {
                        Text("Resultado pendente. Confira a comanda e consulte a mesma operação; não crie outra transferência.")
                        Button(onClick = { onCommit(JSONObject(pending.commandJson)) }, enabled = online && !busy) { Text("Consultar operação original") }
                    }
                } else if (source != null) {
                    item {
                        val options = tabOperationOptions(session.capabilities,
                            source.getJSONObject("tab").getString("state"))
                        if (options.isEmpty()) Text("Nenhuma operação disponível para esta comanda.")
                        options.forEach { (value, label) ->
                            OutlinedButton(onClick = { kind = value; changed() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text(if (kind == value) "✓ $label" else label) }
                        }
                    }
                    if (financial) {
                        item {
                            source.optJSONObject("blocker")?.let { Text(it.getString("message"), color = MaterialTheme.colorScheme.error) }
                            OutlinedTextField(query, { query = it }, label = { Text("Buscar comanda de destino") }, enabled = !busy, modifier = Modifier.fillMaxWidth())
                            state.tabs.filter { it.id != state.selectedTab?.summary?.id && it.state in setOf("OPEN", "REQUIRES_ACTION") && it.displayLabel.contains(query, true) }.take(20).forEach { tab ->
                                TextButton(onClick = { destination = tab; changed() }, enabled = !busy) { Text("${if (destination?.id == tab.id) "✓ " else ""}${tab.displayLabel} · ${formatCents(tab.exposureCents)}") }
                            }
                            if (kind != "MERGE") {
                                TextButton(onClick = { destination = null; changed() }, enabled = !busy) { Text("Criar nova comanda") }
                                if (destination == null) OutlinedTextField(newLabel, { newLabel = it; changed() }, label = { Text("Nome da nova comanda") }, enabled = !busy)
                            }
                            if (kind == "MERGE") Text("A origem será cancelada. Sessões guest serão revogadas e não serão transferidas.")
                        }
                        if (kind != "MERGE") {
                            val lines = source.getJSONArray("lines")
                            for (index in 0 until lines.length()) {
                                val line = lines.getJSONObject(index)
                                val id = line.getString("charge_id")
                                val available = line.getLong("available_cents")
                                val unit = line.getLong("unit_price_cents")
                                if (available > 0) item(key = id) {
                                    Text("${line.getString("product_name")} · disponível ${formatCents(available)}")
                                    Text("Origem: ${line.getString("original_tab_id").take(8)}")
                                    Row {
                                        TextButton(onClick = { quantities = quantities + (id to maxOf(0, (quantities[id] ?: 0) - 1)); changed() }, enabled = !busy) { Text("−") }
                                        Text("${quantities[id] ?: 0}")
                                        TextButton(onClick = { quantities = quantities + (id to ((quantities[id] ?: 0) + 1)); amounts = amounts - id; changed() }, enabled = !busy && unit > 0 && ((quantities[id] ?: 0) + 1) * unit <= available) { Text("+") }
                                    }
                                    OutlinedTextField(amounts[id].orEmpty(), { amounts = amounts + (id to it); quantities = quantities - id; changed() }, label = { Text("Ou valor parcial (R$)") }, enabled = !busy, singleLine = true)
                                }
                            }
                        }
                    } else if (kind == "MOVE_LOCATION") {
                        item {
                            TextButton(onClick = { occupancyId = null; pointId = null; changed() }, enabled = !busy) { Text("Sem local") }
                            state.tables.filter { it.activeOccupancy != null }.forEach { table ->
                                TextButton(onClick = { occupancyId = table.activeOccupancy!!.id; pointId = null; changed() }, enabled = !busy) { Text("${if (occupancyId == table.activeOccupancy!!.id) "✓ " else ""}Mesa ${table.label}") }
                            }
                            state.operationPoints.forEach { (id, label) ->
                                TextButton(onClick = { pointId = id; occupancyId = null; changed() }, enabled = !busy) { Text("${if (pointId == id) "✓ " else ""}$label") }
                            }
                        }
                    }
                    item { OutlinedTextField(reason, { reason = it; changed() }, label = { Text(if (kind == "REOPEN") "Motivo obrigatório" else "Motivo (opcional)") }, enabled = !busy) }
                    item {
                        Text("Saldo atual: ${formatCents(source.getJSONObject("tab").getLong("exposure_cents"))}")
                        state.operationPreview?.let { preview ->
                            Text("Transferir ${formatCents(preview.getLong("amount_cents"))}")
                            Text("Origem após: ${formatCents(preview.getLong("source_after_cents"))}")
                            Text("Destino após: ${formatCents(preview.getLong("destination_after_cents"))}")
                        }
                        val valid = online && !busy && tabOperationOptions(session.capabilities, source.getJSONObject("tab").getString("state")).any { it.first == kind } && (!financial || source.optJSONObject("blocker") == null) && (kind != "MERGE" || destination != null) && (kind != "REOPEN" || reason.isNotBlank())
                        if (financial && state.operationPreview == null) Button(onClick = { val cmd = command(); submitted = cmd; onPreview(cmd) }, enabled = valid) { Text("Conferir transferência") }
                        else Button(onClick = { val cmd = submitted ?: command().also { submitted = it }; onCommit(cmd) }, enabled = valid) { Text("Confirmar operação") }
                    }
                }
                item { TextButton(onClick = onDismiss, enabled = !busy) { Text("Voltar") } }
            }
        }
    }
}
