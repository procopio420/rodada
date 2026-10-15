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

/** A choice is identified by the historical OrderItem ID, never by product name. Zero means unchecked. */
data class RepeatedSelection(val line: RepeatedLine, val quantity: Int)

fun selectedRepeatedLines(review: RepeatOrderReview, quantities: Map<String, Int>): List<RepeatedSelection>? {
    if (!review.canAdd) return null
    val byId = review.lines.associateBy { it.original.id }
    if (quantities.keys.any { it !in byId } || quantities.values.any { it !in 0..99 }) return null
    val selected = review.lines.mapNotNull { line ->
        val quantity = quantities[line.original.id] ?: 0
        if (quantity == 0) null else RepeatedSelection(line, quantity)
    }
    if (selected.isEmpty() || selected.any {
        val price = it.line.product.unitPrice(it.line.customization)
        price < 0 || price > Int.MAX_VALUE.toLong() / it.quantity
    }) return null
    return selected
}

/** Validate a direct repeat without mutating the manual cart or the historical Order. */
internal fun OperationsUiState.repeatedOrderLines(
    tabId: String,
    review: RepeatOrderReview,
    quantities: Map<String, Int>,
): List<PendingOrderLine>? {
    val tab = selectedTab ?: return null
    if (tab.summary.id != tabId || tab.summary.state == "CLOSED" || loading || submitting ||
        connectivity != ConnectivityState.ONLINE || orderIntentId != null ||
        queuedOrders.any { it.tabId == tabId }) return null
    val order = tab.orders.firstOrNull { it.id == review.orderId } ?: return null
    val current = reviewRepeatedOrder(order, products)
    if (!current.canAdd || current != review) return null
    val chosen = selectedRepeatedLines(current, quantities) ?: return null
    return chosen.map { PendingOrderLine(it.line.product.id, it.quantity, it.line.customization) }
}
