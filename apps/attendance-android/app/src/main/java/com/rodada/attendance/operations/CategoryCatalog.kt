package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.rodadaTextFieldColors
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun CategoryCatalog(
    state: OperationsUiState,
    tabId: String,
    closed: Boolean,
    onAdd: (Product, Customization, Int) -> Unit,
    onReview: () -> Unit,
) {
    var query by rememberSaveable(tabId) { mutableStateOf("") }
    var category by rememberSaveable(tabId) { mutableStateOf<String?>(null) }
    var productId by rememberSaveable(tabId) { mutableStateOf<String?>(null) }
    val columns = if (LocalDensity.current.fontScale > 1.3f) 1 else 2
    val locked = !state.canLeaveTabContext()
    val filtered = state.products.filter { it.name.contains(query.trim(), ignoreCase = true) }
    val groups = filtered.groupBy { it.category.trim().ifBlank { "Outros" } }.toSortedMap()
    // Empty category key is reserved for the aggregate; blank product categories use Outros.
    val categories = if (filtered.isEmpty()) emptyList() else listOf("" to filtered) + groups.toList()
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Escolha uma categoria", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(query, { query = it }, colors = rodadaTextFieldColors(), label = { Text("Buscar no catálogo") },
            modifier = Modifier.fillMaxWidth(), singleLine = true, enabled = !locked && !closed)
        if (state.loading && state.products.isEmpty()) Text("Carregando catálogo…")
        else if (groups.isEmpty()) Text(if (query.isBlank()) "Nenhum produto no catálogo." else "Nenhum produto encontrado.")
        categories.chunked(columns).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                row.forEach { (name, products) ->
                    RodadaOutlinedButton(onClick = { category = name }, enabled = !locked && !closed,
                        modifier = Modifier.weight(1f).heightIn(min = 88.dp).testTag(if (name.isEmpty()) "catalog-category-all" else "catalog-category-$name")) {
                        Column { Text(name.ifEmpty { "Todos" }); Text("${products.size} itens", style = MaterialTheme.typography.bodySmall) }
                    }
                }
                if (row.size < columns) Spacer(Modifier.weight(1f))
            }
        }
    }
    category?.let { name ->
        Dialog(onDismissRequest = { if (!locked && productId == null) category = null },
            properties = DialogProperties(usePlatformDefaultWidth = false)) {
            Surface(Modifier.fillMaxWidth(.95f).fillMaxHeight(.9f).safeDrawingPadding(),
                shape = MaterialTheme.shapes.medium, color = RodadaVisual.Surface) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(name.ifEmpty { "Todos" }, style = MaterialTheme.typography.titleLarge)
                    LazyColumn(Modifier.weight(1f).testTag("category-products"), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        val products = if (name.isEmpty()) filtered else groups[name].orEmpty()
                        if (products.isEmpty()) item { Text("Nenhum produto nesta categoria.") }
                        items(products.chunked(columns), key = { row -> row.joinToString { it.id } }) { row ->
                            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                row.forEach { product ->
                                    AttendanceCatalogCard(product, state.cart.filter { it.product.id == product.id }.sumOf { it.quantity },
                                        canSelect = !locked && !closed && product.active && product.availability == "AVAILABLE" && state.connectivity == ConnectivityState.ONLINE,
                                        onSelect = { productId = product.id }, modifier = Modifier.weight(1f))
                                }
                                if (row.size < columns) Spacer(Modifier.weight(1f))
                            }
                        }
                    }
                    RodadaOutlinedButton(onClick = { category = null; onReview() }, enabled = !locked,
                        modifier = Modifier.fillMaxWidth()) { Text("Ver pedido atual · ${state.cart.sumOf { it.quantity }} itens") }
                    TextButton(onClick = { category = null }, enabled = !locked, modifier = Modifier.fillMaxWidth()) { Text("Voltar às categorias") }
                }
            }
        }
    }
    productId?.let { id ->
        // A removed product remains visible as an unavailable selection until dismissed.
        val original = remember(id) { state.products.firstOrNull { it.id == id } }
        original?.let { originalProduct ->
            val current = state.products.firstOrNull { it.id == id } ?: originalProduct.copy(active = false)
            var quantity by rememberSaveable(id) { mutableStateOf(1) }
            ProductCustomizationSheet(current, onDismiss = { productId = null },
                quantity = quantity, onQuantityChange = { quantity = it },
                capacity = { draftQuantityCapacity(state.cart, id, it) }, locked = locked,
                canSubmit = !locked && !closed && current.active && current.availability == "AVAILABLE" && state.connectivity == ConnectivityState.ONLINE) { selection ->
                onAdd(current, selection, quantity)
                productId = null
            }
        }
    }
}
