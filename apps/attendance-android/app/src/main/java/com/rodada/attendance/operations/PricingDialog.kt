package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.StoredSession
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.util.UUID

private val pricingLabels = linkedMapOf("TAB_DISCOUNT" to "Desconto na comanda", "ITEM_DISCOUNT" to "Desconto no item",
    "COURTESY" to "Cortesia", "SERVICE_CHARGE" to "Calcular / atualizar serviço",
    "SERVICE_CHARGE_REDUCTION" to "Reduzir / remover serviço", "REVERSAL" to "Reverter ajuste")

internal fun pricingMinorUnits(raw: String): Long? {
    val text = raw.trim().replace(',', '.')
    if (!Regex("\\d+(\\.\\d{1,2})?").matches(text)) return null
    val parts = text.split('.')
    val whole = parts[0].toLongOrNull() ?: return null
    if (whole > 21474836L) return null
    return whole * 100 + (parts.getOrNull(1) ?: "").padEnd(2, '0').toLong()
}

@Composable
private fun PricingChoice(label: String, value: String, options: Map<String, String>, locked: Boolean, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Box {
        OutlinedButton(onClick = { expanded = true }, enabled = !locked, modifier = Modifier.fillMaxWidth()) { Text("$label: ${options[value] ?: "Selecione"}") }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { (key, text) -> DropdownMenuItem(text = { Text(text) }, onClick = { onChange(key); expanded = false }) }
        }
    }
}

@Composable
fun PricingDialog(session: StoredSession, tab: TabSummary, viewModel: OperationsViewModel, onDismiss: () -> Unit) {
    val scope = rememberCoroutineScope()
    val recovered = remember(tab.id) { viewModel.pendingPricing(session, tab.id)?.let { JSONObject(it.commandJson) } }
    var command by remember { mutableStateOf(recovered) }
    var preview by remember { mutableStateOf(recovered?.optJSONObject("_preview")) }
    var pricing by remember { mutableStateOf<JSONObject?>(null) }
    var kind by remember { mutableStateOf("TAB_DISCOUNT") }
    var calculation by remember { mutableStateOf("FIXED") }
    var charge by remember { mutableStateOf("") }
    var adjustment by remember { mutableStateOf("") }
    var value by remember { mutableStateOf("") }
    var reason by remember { mutableStateOf("") }
    var pin by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf(if (recovered != null) "Há um ajuste aguardando confirmação. Verifique esta mesma operação." else "") }
    suspend fun load() { pricing = viewModel.pricing(session, tab.id) }
    LaunchedEffect(tab.id) { runCatching { load() }.onFailure { message = it.message ?: "Não foi possível atualizar a conta." } }
    AlertDialog(onDismissRequest = { if (!busy) onDismiss() }, title = { Text("Ajustar conta") }, text = {
        Column(modifier = Modifier.heightIn(max = 560.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (message.isNotBlank()) Text(message)
            if (command == null) {
                PricingChoice("Ação", kind, pricingLabels, busy) { kind = it }
                if (kind == "ITEM_DISCOUNT" || kind == "COURTESY") {
                    val choices = linkedMapOf("" to "Comanda inteira (cortesia)")
                    pricing?.optJSONArray("charges")?.let { rows -> for (i in 0 until rows.length()) { val row = rows.getJSONObject(i); val id = row.getString("charge_id"); choices[id] = "${row.optString("product_name", "Consumo ${id.take(8)}")} · ${formatCents(row.getLong("gross"))}" } }
                    PricingChoice("Item", charge, choices, busy) { charge = it }
                }
                if (kind == "REVERSAL") {
                    val choices = linkedMapOf("" to "Selecione")
                    pricing?.optJSONArray("history")?.let { rows -> for (i in 0 until rows.length()) { val row = rows.getJSONObject(i); if (row.getString("kind") !in listOf("REVERSAL", "SERVICE_CHARGE")) choices[row.getString("id")] = "${pricingLabels[row.getString("kind")] ?: row.getString("kind")} · ${formatCents(row.getLong("amount_cents"))}" } }
                    PricingChoice("Ajuste original", adjustment, choices, busy) { adjustment = it }
                } else {
                    if (!kind.startsWith("SERVICE")) PricingChoice("Tipo", calculation, mapOf("FIXED" to "Valor em reais", "PERCENTAGE" to "Percentual"), busy) { calculation = it }
                    OutlinedTextField(value = value, onValueChange = { value = it }, enabled = !busy, label = { Text(if (kind == "SERVICE_CHARGE" || (kind != "SERVICE_CHARGE_REDUCTION" && calculation == "PERCENTAGE")) "Percentual (%)" else "Valor (R$)") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    if (kind == "SERVICE_CHARGE") Text("Deixe em branco para usar o percentual configurado pelo estabelecimento.")
                }
                OutlinedTextField(value = reason, onValueChange = { reason = it.take(80) }, enabled = !busy, label = { Text("Motivo") }, modifier = Modifier.fillMaxWidth())
            } else {
                preview?.let { Text("Antes ${formatCents(it.getLong("before_payable_cents"))} → depois ${formatCents(it.getLong("after_payable_cents"))}"); Text("Saldo restante ${formatCents(it.getLong("after_remaining_cents"))}") }
                if (preview?.optBoolean("approval_required") != true) OutlinedTextField(value = pin, onValueChange = { pin = it }, enabled = !busy, label = { Text("PIN para ação gerencial") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(), singleLine = true)
            }
            pricing?.optJSONArray("history")?.let { rows ->
                if (rows.length() > 0) Text("Histórico de ajustes", style = MaterialTheme.typography.titleSmall)
                for (i in 0 until rows.length()) { val row = rows.getJSONObject(i); Text("${pricingLabels[row.getString("kind")] ?: row.getString("kind")} · ${formatCents(row.getLong("amount_cents"))} · ${row.optString("reason_code")}") }
            }
            if (busy) CircularProgressIndicator()
        }
    }, confirmButton = {
        TextButton(enabled = !busy && pricing != null, onClick = {
            scope.launch {
                busy = true
                try {
                    if (command == null) {
                        val data = JSONObject().put("kind", kind).put("expected_version", pricing!!.getInt("version")).put("idempotency_key", UUID.randomUUID().toString()).put("reason_code", reason)
                        if (kind == "REVERSAL") data.put("adjustment_id", adjustment)
                        else {
                            val parsed = if (kind == "SERVICE_CHARGE" && value.isBlank()) pricing!!.getJSONObject("policy").getLong("service_basis_points") else pricingMinorUnits(value) ?: throw IllegalArgumentException("Informe um valor com até duas casas decimais.")
                            data.put("value", parsed).put("calculation_type", if (kind == "SERVICE_CHARGE") "PERCENTAGE" else if (kind == "SERVICE_CHARGE_REDUCTION") "FIXED" else calculation)
                            if (charge.isNotBlank() && kind in listOf("ITEM_DISCOUNT", "COURTESY")) data.put("charge_id", charge)
                        }
                        val result = viewModel.pricing(session, tab.id, data, "preview/")
                        data.put("_preview", result); preview = result; command = data
                    } else {
                        viewModel.commitPricing(session, tab.id, command!!, preview?.optBoolean("approval_required") == true, pin)
                        pin = ""; onDismiss()
                    }
                } catch (error: Exception) {
                    pin = ""; message = error.message ?: "Resposta não confirmada. Verifique o mesmo ajuste."
                    if (error is OperationsApiException && error.status in 400..499 && error.code != "REAUTH_REQUIRED") { command = null; preview = null; runCatching { load() } }
                } finally { busy = false }
            }
        }) { Text(if (command == null) "Conferir antes de aplicar" else if (preview?.optBoolean("approval_required") == true) "Solicitar aprovação" else "Confirmar ajuste") }
    }, dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text("Voltar à comanda") } })
}
