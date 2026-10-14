package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaButton
import com.rodada.attendance.ui.RodadaOutlinedButton

@Composable
internal fun RepeatOrderDialog(review: RepeatOrderReview, enabled: Boolean, onDismiss: () -> Unit, onAdd: () -> Unit) {
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Conferir rodada") }, text = {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Adicionar ao carrinho não envia o pedido. Preços e disponibilidade serão conferidos novamente no envio.")
            if (!enabled) Text("O contexto mudou ou está ocupado. Feche e revise novamente.")
            if (review.excluded > 0) Text("${review.excluded} linha(s) sem unidades disponíveis ou canceladas não serão repetidas.")
            review.problems.forEach { Text(it) }
            if (review.lines.isEmpty() && review.problems.isEmpty()) Text("Nenhum item para repetir.")
            review.lines.forEach { line ->
                Text("${line.original.quantity} × ${line.product.name}")
                Text("Anterior: ${line.original.productName} · ${formatCents(line.original.unitPriceCents)} por unidade")
                if (line.original.customizationText.isNotBlank()) Text(line.original.customizationText)
                Text("Atual: ${formatCents(line.product.unitPrice(line.customization))} por unidade")
                val configuration = line.product.configurationText(line.customization)
                if (configuration.isNotBlank()) Text(configuration)
                if (line.original.unitPriceCents != line.product.unitPrice(line.customization) ||
                    line.original.productName != line.product.name || line.original.customizationText != configuration) Text("Preço ou descrição mudou. Confira os valores atuais.")
            }
        }
    }, confirmButton = {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            RodadaButton(onClick = onAdd, enabled = enabled && review.canAdd, modifier = Modifier.fillMaxWidth()) { Text("Adicionar ao carrinho") }
            RodadaOutlinedButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Cancelar") }
        }
    })
}
