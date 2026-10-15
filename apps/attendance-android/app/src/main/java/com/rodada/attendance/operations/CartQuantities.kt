package com.rodada.attendance.operations

internal fun sameCustomization(a: Customization, b: Customization): Boolean =
    a.variantId == b.variantId && a.note == b.note && a.optionIds.sorted() == b.optionIds.sorted()

internal fun draftQuantityCapacity(cart: List<CartLine>, productId: String, selection: Customization): Int =
    (99 - cart.filter { it.product.id == productId && sameCustomization(it.customization, selection) }.sumOf { it.quantity }).coerceAtLeast(0)

internal fun addDraftQuantity(cart: List<CartLine>, product: Product, selection: Customization, quantity: Int): List<CartLine>? {
    if (quantity !in 1..99 || quantity > draftQuantityCapacity(cart, product.id, selection)) return null
    val existing = cart.firstOrNull { it.product.id == product.id && sameCustomization(it.customization, selection) }
    return if (existing == null) cart + CartLine(product, quantity, selection)
    else cart.map { if (it.lineId == existing.lineId) it.copy(product = product, quantity = it.quantity + quantity) else it }
}

internal fun editDraftConfiguration(cart: List<CartLine>, lineId: String, product: Product, selection: Customization): List<CartLine>? {
    val line = cart.firstOrNull { it.lineId == lineId } ?: return null
    if (line.quantity > draftQuantityCapacity(cart.filterNot { it.lineId == lineId }, product.id, selection)) return null
    return cart.map { if (it.lineId == lineId) it.copy(product = product, customization = selection) else it }
}

internal fun changeDraftQuantity(cart: List<CartLine>, lineId: String, delta: Int): List<CartLine>? {
    val line = cart.firstOrNull { it.lineId == lineId } ?: return null
    val quantity = line.quantity + delta
    if (quantity <= 0) return cart.filterNot { it.lineId == lineId }
    if (quantity > draftQuantityCapacity(cart.filterNot { it.lineId == lineId }, line.product.id, line.customization)) return null
    return cart.map { if (it.lineId == lineId) it.copy(quantity = quantity) else it }
}
