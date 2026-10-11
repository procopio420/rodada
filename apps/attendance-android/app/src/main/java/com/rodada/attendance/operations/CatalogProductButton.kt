package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import com.rodada.attendance.ui.RodadaOutlinedButton

@Composable
internal fun CatalogProductButton(product: Product, sellable: Boolean, enabled: Boolean, onClick: () -> Unit) {
    RodadaOutlinedButton(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.fillMaxWidth()) {
            Text(product.name, modifier = Modifier.fillMaxWidth(), fontWeight = FontWeight.SemiBold)
            Text(formatCents(product.priceCents), modifier = Modifier.fillMaxWidth())
            Text(if (sellable) product.fulfillmentStation else "${product.availability} · indisponível",
                color = if (sellable) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.error)
        }
    }
}
