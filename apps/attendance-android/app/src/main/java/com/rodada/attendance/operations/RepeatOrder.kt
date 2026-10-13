package com.rodada.attendance.operations

import org.json.JSONObject

internal fun historicalCustomization(snapshot: JSONObject?): Customization? = runCatching {
    requireNotNull(snapshot)
    require(snapshot.has("variant") && snapshot.has("modifiers") && snapshot.has("special_instructions"))
    Customization(
        if (snapshot.isNull("variant")) null else snapshot.getJSONObject("variant").getString("id").also { require(it.isNotBlank()) },
        snapshot.getJSONArray("modifiers").let { values -> List(values.length()) { values.getJSONObject(it).getString("option_id").also { id -> require(id.isNotBlank()) } } },
        snapshot.getString("special_instructions"),
    )
}.getOrNull()

data class RepeatedLine(val original: OrderItem, val product: Product, val customization: Customization)
data class RepeatOrderReview(val orderId: String, val lines: List<RepeatedLine>, val problems: List<String>, val excluded: Int) {
    val canAdd: Boolean get() = lines.isNotEmpty() && problems.isEmpty()
}

fun reviewRepeatedOrder(order: TabOrder, products: List<Product>): RepeatOrderReview {
    val lines = mutableListOf<RepeatedLine>()
    val problems = mutableListOf<String>()
    var excluded = 0
    order.items.forEach { item ->
        if (item.state == "CANCELLED" || item.quantity == 0) { excluded++; return@forEach }
        val product = products.firstOrNull { it.id == item.productId }
        val selection = item.customization
        val problem = when {
            product == null -> "Produto ausente do catálogo atual."
            !product.active || product.availability != "AVAILABLE" -> "Produto inativo ou indisponível."
            selection == null -> "Histórico sem configuração verificável. Escolha o item no catálogo."
            selection.variantId != null && product.variants.none { it.id == selection.variantId } -> "Variação removida."
            selection.optionIds.distinct().size != selection.optionIds.size || selection.note.length > 500 -> "Configuração inválida."
            product.customizationError(selection) != null -> product.customizationError(selection)
            item.quantity !in 1..999 -> "Quantidade fora do limite."
            product.unitPrice(selection) !in 0..(Int.MAX_VALUE.toLong() / item.quantity) -> "Valor fora do limite."
            else -> null
        }
        if (problem != null) problems += "${item.productName}: $problem"
        else lines += RepeatedLine(item, requireNotNull(product), requireNotNull(selection))
    }
    return RepeatOrderReview(order.id, lines, problems, excluded)
}

/** A reviewed draft is local only; sending still captures a new recovery intent. */
internal fun OperationsUiState.withRepeatedOrder(tabId: String, review: RepeatOrderReview): OperationsUiState {
    val tab = selectedTab ?: return this
    if (tab.summary.id != tabId || tab.summary.state == "CLOSED" || loading || submitting ||
        connectivity != ConnectivityState.ONLINE || orderIntentId != null || queuedOrders.any { it.tabId == tabId }) return this
    val order = tab.orders.firstOrNull { it.id == review.orderId } ?: return this
    val current = reviewRepeatedOrder(order, products)
    if (!current.canAdd || current != review) return copy(errorMessage = "A rodada mudou. Abra novamente a revisão.")
    return copy(cart = cart + current.lines.map { CartLine(it.product, it.original.quantity, it.customization) },
        errorMessage = null, noticeMessage = "Rodada adicionada ao carrinho. Confira antes de confirmar o novo pedido.")
}
