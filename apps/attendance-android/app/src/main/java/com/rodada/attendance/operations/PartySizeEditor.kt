package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaButton as Button
import com.rodada.attendance.ui.RodadaOutlinedButton as OutlinedButton
import org.json.JSONObject
import java.util.UUID
import kotlinx.coroutines.launch

data class PartySizeSnapshot(val count: Int?, val version: Int, val source: String?) {
    companion object { fun fromJson(row: JSONObject) = PartySizeSnapshot(if (row.isNull("covers_count")) null else row.getInt("covers_count"), row.getInt("version"), if (row.isNull("source")) null else row.getString("source")) }
}
data class PartySizeCommand(val count: Int, val version: Int, val reason: String, val key: String) {
    fun toJson() = JSONObject().put("covers_count", count).put("expected_version", version).put("reason", reason).put("idempotency_key", key)
}

@Composable
fun PartySizeEditor(load: suspend () -> PartySizeSnapshot, save: suspend (PartySizeCommand) -> PartySizeSnapshot) {
    var open by rememberSaveable { mutableStateOf(false) }
    var current by remember { mutableStateOf<PartySizeSnapshot?>(null) }
    var count by rememberSaveable { mutableStateOf("") }
    var reason by rememberSaveable { mutableStateOf("") }
    var pending by remember { mutableStateOf<PartySizeCommand?>(null) }
    var busy by remember { mutableStateOf(false) }
    var fresh by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    OutlinedButton(onClick = {
        open = true
        scope.launch {
            busy = true
            runCatching { load() }.onSuccess { current = it; fresh = true; message = null }.onFailure { fresh = false; message = "Não foi possível consultar pessoas." }
            busy = false
        }
    }, modifier = Modifier.fillMaxWidth()) { Text("Pessoas na ocupação") }
    if (!open) return
    AlertDialog(onDismissRequest = { if (!busy && pending == null) open = false },
        title = { Text("Pessoas na ocupação") },
        text = {
            Column(modifier = Modifier.heightIn(max = 400.dp).verticalScroll(rememberScrollState()).imePadding(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(current?.count?.let { "$it pessoa(s) · ${if (current?.source == "GUEST") "Informado pelo cliente" else "Observação registrada"}" } ?: if (current != null) "Quantidade não informada" else "Quantidade ainda não consultada")
                Text("Opcional. Não altera o saldo nem impede pedidos.")
                message?.let { Text(it) }
                OutlinedTextField(value = count, onValueChange = { count = it }, label = { Text("Quantidade de pessoas") }, enabled = !busy && pending == null, modifier = Modifier.fillMaxWidth())
                listOf(listOf(1, 2, 3, 4), listOf(5, 6, 7, 8)).forEach { values ->
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) { values.forEach { value ->
                        OutlinedButton(onClick = { count = value.toString() }, enabled = !busy && pending == null, modifier = Modifier.weight(1f)) { Text(value.toString()) }
                    } }
                }
                OutlinedTextField(value = reason, onValueChange = { reason = it.take(500) }, label = { Text("Motivo (opcional)") }, enabled = !busy && pending == null, modifier = Modifier.fillMaxWidth())
                if (!fresh) OutlinedButton(onClick = { scope.launch { busy = true; runCatching { load() }.onSuccess { current = it; fresh = true }.onFailure { message = "Consulta indisponível." }; busy = false } }, enabled = !busy) { Text("Consultar quantidade") }
            }
        },
        confirmButton = { Button(enabled = !busy && fresh && current != null && (pending != null || (count.toIntOrNull() ?: 0) > 0), onClick = {
            val intent = pending ?: PartySizeCommand(count.toInt(), current!!.version, reason, UUID.randomUUID().toString())
            busy = true; message = null
            scope.launch {
                try { current = save(intent); pending = null; count = ""; reason = ""; message = "Quantidade confirmada." }
                catch (failure: Exception) {
                    if (failure is OperationsApiException && failure.status < 500) {
                        pending = null; message = failure.message
                        if (failure.status == 409) { runCatching { load() }.onSuccess { current = it }.onFailure { fresh = false }; message = "Confira a quantidade atual antes de enviar novamente." }
                        if (failure.status == 401 || failure.status == 403) fresh = false
                    } else { pending = intent; message = "Resultado não confirmado. Verifique a mesma quantidade antes de editar." }
                } finally { busy = false }
            }
        }) { Text(if (pending == null) "Confirmar quantidade" else "Verificar mesma quantidade") } },
        dismissButton = { OutlinedButton(onClick = { open = false }, enabled = !busy && pending == null) { Text("Voltar") } },
    )
}
