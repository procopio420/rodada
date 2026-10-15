package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaButton
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun RepeatOrderDialog(
    review: RepeatOrderReview,
    enabled: Boolean,
    onDismiss: () -> Unit,
    onAdd: (Map<String, Int>) -> Unit,
) {
    val checked = remember(review) {
        mutableStateMapOf<String, Boolean>().apply { review.lines.forEach { put(it.original.id, true) } }
    }
    val inputs = remember(review) {
        mutableStateMapOf<String, String>().apply { review.lines.forEach { put(it.original.id, it.original.quantity.toString()) } }
    }
    val quantities = review.lines.associate { line ->
        val id = line.original.id
        val raw = inputs[id].orEmpty()
        id to (if (checked[id] == true) {
            if (raw.matches(Regex("[1-9][0-9]*"))) raw.toIntOrNull() ?: -1 else -1
        } else 0)
    }
    val chosen = selectedRepeatedLines(review, quantities)
    val total = chosen?.sumOf { it.line.product.unitPrice(it.line.customization) * it.quantity } ?: 0L
    val units = chosen?.sumOf { it.quantity } ?: 0

    AlertDialog(onDismissRequest = onDismiss, title = { Text("Mais uma rodada") }, text = {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Escolha os itens e ajuste as quantidades. Nada será enviado antes de confirmar o pedido.", style = MaterialTheme.typography.bodySmall)
            if (!enabled) Text("O contexto mudou ou está ocupado. Feche e revise novamente.", color = MaterialTheme.colorScheme.error)
            if (review.excluded > 0) Text("${review.excluded} linha(s) canceladas ou sem unidades restantes não serão repetidas.")
            review.problems.forEach { Text(it, color = MaterialTheme.colorScheme.error) }
            if (review.lines.isEmpty() && review.problems.isEmpty()) Text("Nenhum item para repetir.")
            review.lines.forEach { line ->
                val id = line.original.id
                val selected = checked[id] == true
                val quantity = quantities[id] ?: 0
                val price = line.product.unitPrice(line.customization)
                HorizontalDivider(color = RodadaVisual.Border)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = selected, onCheckedChange = { checked[id] = it }, enabled = enabled,
                        modifier = Modifier.heightIn(min = 48.dp))
                    Column(Modifier.weight(1f)) {
                        Text(line.product.name, style = MaterialTheme.typography.titleSmall)
                        val configuration = line.product.configurationText(line.customization)
                        if (configuration.isNotBlank()) Text(configuration, style = MaterialTheme.typography.bodySmall)
                        Text("${formatCents(price)} / un.", style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Muted)
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Quantidade", style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                    TextButton(onClick = { inputs[id] = (quantity - 1).toString() },
                        enabled = enabled && selected && quantity > 1, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text("−")
                    }
                    OutlinedTextField(
                        value = inputs[id].orEmpty(),
                        onValueChange = { value -> if (value.length <= 2 && value.all(Char::isDigit)) inputs[id] = value },
                        modifier = Modifier.width(76.dp),
                        label = { Text("Qtd.") },
                        singleLine = true,
                        enabled = enabled && selected,
                        isError = selected && quantity !in 1..99,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    )
                    TextButton(onClick = { inputs[id] = (quantity + 1).toString() },
                        enabled = enabled && selected && quantity in 1..98, modifier = Modifier.heightIn(min = 48.dp)) {
                        Text("+")
                    }
                }
                if (line.original.unitPriceCents != price ||
                    line.original.productName != line.product.name ||
                    line.original.customizationText != line.product.configurationText(line.customization)) {
                    Text("Alteração: antes ${formatCents(line.original.unitPriceCents)} / un. Confira o valor e a descrição atuais.",
                        style = MaterialTheme.typography.bodySmall, color = RodadaVisual.Amber)
                }
            }
            Text("Selecionados: $units unidade(s) · ${formatCents(total)}", style = MaterialTheme.typography.titleSmall)
            if (chosen == null && review.canAdd) Text("Marque ao menos um item e informe quantidades de 1 a 99.",
                color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }
    }, confirmButton = {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            RodadaButton(onClick = { if (chosen != null) onAdd(quantities) },
                enabled = enabled && chosen != null, modifier = Modifier.fillMaxWidth()) { Text("Adicionar ao carrinho") }
            RodadaOutlinedButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Cancelar") }
        }
    })
}
