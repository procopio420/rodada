package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class RepeatOrderTest {
    private val product = Product("product", "Nome atual", 1000, true, "BAR", "AVAILABLE")
    private val item = OrderItem("historical-item", "Nome anterior", 800, 2, 1600, "DELIVERED", productId = product.id, customization = Customization())
    private val order = TabOrder("historical-order", "", listOf(item))
    private val tab = TabSummary("tab", "Comanda", "OPEN", 1, 1600, 0, 1600)
    private val state = OperationsUiState(selectedTab = TabDetail(tab, listOf(order)), products = listOf(product), connectivity = ConnectivityState.ONLINE)

    @Test fun `repeat preserves draft uses current cents and new line identities without historical intent`() {
        val draft = CartLine(product, 1)
        val review = reviewRepeatedOrder(order, state.products)
        val next = state.copy(cart = listOf(draft)).withRepeatedOrder(tab.id, review)
        assertEquals(draft, next.cart.first())
        assertEquals(2, next.cart.last().quantity)
        assertEquals(1000L, next.cart.last().unitPriceCents)
        assertNotEquals(item.id, next.cart.last().lineId)
        assertNotEquals(draft.lineId, next.cart.last().lineId)
        assertNull(next.orderIntentId)
        assertEquals(order, next.selectedTab!!.orders.single())
    }
    @Test fun `stale review and operational guards leave draft untouched`() {
        val review = reviewRepeatedOrder(order, state.products)
        val changed = state.copy(products = listOf(product.copy(priceCents = 1100))).withRepeatedOrder(tab.id, review)
        assertTrue(changed.cart.isEmpty())
        assertNotNull(changed.errorMessage)
        listOf(state.copy(loading = true), state.copy(submitting = true), state.copy(orderIntentId = "pending"),
            state.copy(connectivity = ConnectivityState.OFFLINE), state.copy(selectedTab = TabDetail(tab.copy(state = "CLOSED"), listOf(order))))
            .forEach { assertEquals(it, it.withRepeatedOrder(tab.id, review)) }
        assertEquals(state, state.withRepeatedOrder("other-tab", review))
    }
    @Test fun `unavailable inactive absent legacy and removed configuration block entire round`() {
        listOf(product.copy(active = false), product.copy(availability = "UNAVAILABLE"), product.copy(id = "other"))
            .forEach { assertFalse(reviewRepeatedOrder(order, listOf(it)).canAdd) }
        listOf(item.copy(customization = null), item.copy(customization = Customization("removed")),
            item.copy(customization = Customization(optionIds = listOf("removed"))), item.copy(quantity = 1000))
            .forEach { assertFalse(reviewRepeatedOrder(order.copy(items = listOf(item, it)), listOf(product)).canAdd) }
    }
    @Test fun `variant and modifiers retain exact selection current prices and notes`() {
        val configured = product.copy(variants = listOf(ProductVariant("variant", "Grande", 1500, true, false)),
            modifierGroups = listOf(ModifierGroup("group", "Extras", 1, 1, true, listOf(ModifierOption("option", "Extra", 200, true, false, "ADD")))))
        val selection = Customization("variant", listOf("option"), "Separado")
        val review = reviewRepeatedOrder(order.copy(items = listOf(item.copy(customization = selection))), listOf(configured))
        assertTrue(review.canAdd)
        assertEquals(selection, review.lines.single().customization)
        assertEquals(1700L, review.lines.single().product.unitPrice(selection))
        assertFalse(reviewRepeatedOrder(order, listOf(configured)).canAdd)
        assertFalse(reviewRepeatedOrder(order.copy(items = listOf(item.copy(customization = selection))), listOf(configured.copy(variants = configured.variants.map { it.copy(available = false) }))).canAdd)
    }
    @Test fun `cancelled lines are explicit exclusions remaining quantity is copied`() {
        val review = reviewRepeatedOrder(order.copy(items = listOf(item, item.copy(state = "CANCELLED"))), listOf(product))
        assertEquals(1, review.excluded)
        assertEquals(2, review.lines.single().original.quantity)
        assertTrue(review.canAdd)
        assertFalse(reviewRepeatedOrder(order.copy(items = listOf(item.copy(state = "CANCELLED"))), listOf(product)).canAdd)
    }
    @Test fun `canonical snapshot parsing never guesses configuration from labels`() {
        assertEquals(Customization("v", listOf("o"), "Nota"), historicalCustomization(JSONObject("""{"variant":{"id":"v"},"modifiers":[{"option_id":"o"}],"special_instructions":"Nota"}""")))
        assertEquals(Customization(), historicalCustomization(JSONObject("""{"variant":null,"modifiers":[],"special_instructions":""}""")))
        assertNull(historicalCustomization(JSONObject()))
        assertNull(historicalCustomization(JSONObject("""{"variant":{"name":"Grande"},"modifiers":[],"special_instructions":""}""")))
    }
}
