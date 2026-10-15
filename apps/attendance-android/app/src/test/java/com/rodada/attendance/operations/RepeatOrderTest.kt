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

    @Test fun `direct repeat uses current product and leaves manual draft untouched`() {
        val draft = CartLine(product, 1)
        val original = state.copy(cart = listOf(draft))
        val review = reviewRepeatedOrder(order, state.products)
        val lines = original.repeatedOrderLines(tab.id, review, mapOf(item.id to 2))
        assertEquals(listOf(PendingOrderLine(product.id, 2, Customization())), lines)
        assertEquals(listOf(draft), original.cart)
        assertEquals(order, original.selectedTab!!.orders.single())
        assertNull(original.orderIntentId)
    }
    @Test fun `stale review and operational guards reject without editing the cart`() {
        val review = reviewRepeatedOrder(order, state.products)
        assertNull(state.copy(products = listOf(product.copy(priceCents = 1100)))
            .repeatedOrderLines(tab.id, review, mapOf(item.id to 2)))
        listOf(state.copy(loading = true), state.copy(submitting = true), state.copy(orderIntentId = "pending"),
            state.copy(connectivity = ConnectivityState.OFFLINE), state.copy(selectedTab = TabDetail(tab.copy(state = "CLOSED"), listOf(order))))
            .forEach { assertNull(it.repeatedOrderLines(tab.id, review, mapOf(item.id to 2))) }
        assertNull(state.repeatedOrderLines("other-tab", review, mapOf(item.id to 2)))
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

    @Test fun `selective repeat excludes unchecked lines and edits quantity without touching history`() {
        val second = Product("second", "Suco", 900, true, "BAR", "AVAILABLE")
        val another = item.copy(id = "second-item", productId = second.id, productName = "Suco", quantity = 3)
        val historical = order.copy(items = listOf(item, another))
        val current = state.copy(products = listOf(product, second), selectedTab = TabDetail(tab, listOf(historical)))
        val review = reviewRepeatedOrder(historical, current.products)
        val chosen = current.repeatedOrderLines(tab.id, review, mapOf(item.id to 1, another.id to 0))
        assertEquals(listOf(PendingOrderLine(product.id, 1, Customization())), chosen)
        assertTrue(current.cart.isEmpty())
        assertEquals(historical, current.selectedTab!!.orders.single())
        assertNull(current.orderIntentId)
    }

    @Test fun `empty invalid or unknown selection cannot mutate draft`() {
        val review = reviewRepeatedOrder(order, state.products)
        for (invalid in listOf(emptyMap(), mapOf(item.id to 0), mapOf(item.id to -1),
            mapOf(item.id to 1000), mapOf("other-item" to 1), mapOf(item.id to 1, "other-item" to 1))) {
            assertNull(selectedRepeatedLines(review, invalid))
            assertNull(state.repeatedOrderLines(tab.id, review, invalid))
            assertTrue(state.cart.isEmpty())
        }
        assertEquals(4, state.repeatedOrderLines(tab.id, review, mapOf(item.id to 4))!!.single().quantity)
    }

    @Test fun `durable repeat intent preserves direct origin and legacy draft compatibility`() {
        val repeat = RecoveryIntent.ConfirmOrder(
            "new-intent", "staff", "venue", "device", "new-intent", 123L, RecoveryState.PENDING,
            "tab", listOf(PendingOrderLine(product.id, 2, Customization())), clearCartOnConfirmation = false,
        )
        assertEquals(repeat, RecoveryIntent.fromJson(repeat.toJson()))
        assertFalse((RecoveryIntent.fromJson(repeat.toJson()) as RecoveryIntent.ConfirmOrder).clearCartOnConfirmation)
        val legacy = repeat.toJson().apply { remove("clear_cart_on_confirmation") }
        assertTrue((RecoveryIntent.fromJson(legacy) as RecoveryIntent.ConfirmOrder).clearCartOnConfirmation)
        assertTrue(state.cart.isEmpty())
    }

    @Test fun `canonical snapshot parsing never guesses configuration from labels`() {
        assertEquals(Customization("v", listOf("o"), "Nota"), historicalCustomization(JSONObject("""{"variant":{"id":"v"},"modifiers":[{"option_id":"o"}],"special_instructions":"Nota"}""")))
        assertEquals(Customization(), historicalCustomization(JSONObject("""{"variant":null,"modifiers":[],"special_instructions":""}""")))
        assertNull(historicalCustomization(JSONObject()))
        assertNull(historicalCustomization(JSONObject("""{"variant":{"name":"Grande"},"modifiers":[],"special_instructions":""}""")))
    }
}
