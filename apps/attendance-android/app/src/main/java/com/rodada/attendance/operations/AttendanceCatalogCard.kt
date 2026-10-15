package com.rodada.attendance.operations

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun AttendanceCatalogCard(
    product: Product,
    quantity: Int,
    canSelect: Boolean,
    onSelect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(modifier.testTag("product-${product.id}"), colors = CardDefaults.cardColors(containerColor = if (quantity > 0) RodadaVisual.Control else RodadaVisual.Surface)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            RodadaOutlinedButton(onClick = onSelect, enabled = canSelect, modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    // Same generic fallback as Web; never synthesize a new ProductIcon identity.
                    val ink = RodadaVisual.Muted
                    Canvas(Modifier.size(44.dp)) {
                        drawCircle(ink, size.minDimension * .31f, style = Stroke(2.dp.toPx()))
                        drawCircle(ink, size.minDimension * .208f, style = Stroke(2.dp.toPx()))
                    }
                    Text(product.name, fontWeight = FontWeight.Bold)
                    Text(formatCents(product.priceCents), fontFamily = RodadaVisual.Number)
                }
            }
            if (!product.active || product.availability != "AVAILABLE") Text("Indisponível", color = MaterialTheme.colorScheme.error)
            if (quantity > 0) Text("$quantity no pedido", style = MaterialTheme.typography.bodySmall)
        }
    }
}
