package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class CartQuantitiesTest {
    private val product = Product("fixture-product", "Produto do catálogo", 800, true, "BAR", "AVAILABLE")
    @Test fun addsChosenQuantityOnceAndKeepsLineIdentityWhenAggregating() {
        val first = addDraftQuantity(emptyList(), product, Customization(), 3)!!
        assertEquals(3, first.single().quantity)
        val next = addDraftQuantity(first, product, Customization(), 2)!!
        assertEquals(5, next.single().quantity)
        assertEquals(first.single().lineId, next.single().lineId)
        assertEquals(4000L, next.single().unitPriceCents * next.single().quantity)
    }
    @Test fun configurationsRemainSeparateAndOptionOrderDoesNotDuplicate() {
        val a = Customization(optionIds = listOf("a", "b"))
        val first = addDraftQuantity(emptyList(), product, a, 2)!!
        val second = addDraftQuantity(first, product, a.copy(optionIds = listOf("b", "a")), 1)!!
        assertEquals(3, second.single().quantity)
        val next = addDraftQuantity(second, product, a.copy(note = "Separado"), 2)!!
        assertEquals(listOf(3, 2), next.map { it.quantity })
    }
    @Test fun rejectsInvalidOrExcessQuantityWithoutTruncation() {
        val first = addDraftQuantity(emptyList(), product, Customization(), 98)!!
        assertNull(addDraftQuantity(first, product, Customization(), 2))
        assertNull(addDraftQuantity(first, product, Customization(), 0))
        assertNull(addDraftQuantity(first, product, Customization(), 100))
        assertEquals(98, first.single().quantity)
        assertEquals(99, addDraftQuantity(first, product, Customization(), 1)!!.single().quantity)
    }
    @Test fun quantityAndConfigurationEditsCannotBypassTheLimit() {
        val a = addDraftQuantity(emptyList(), product, Customization(), 60)!!
        val cart = addDraftQuantity(a, product, Customization(note = "Separado"), 60)!!
        assertNull(editDraftConfiguration(cart, cart.last().lineId, product, Customization()))
        assertEquals(listOf(60, 60), cart.map { it.quantity })
        val maximum = addDraftQuantity(emptyList(), product, Customization(), 99)!!
        assertNull(changeDraftQuantity(maximum, maximum.single().lineId, 1))
        assertEquals(98, changeDraftQuantity(maximum, maximum.single().lineId, -1)!!.single().quantity)
    }
}
