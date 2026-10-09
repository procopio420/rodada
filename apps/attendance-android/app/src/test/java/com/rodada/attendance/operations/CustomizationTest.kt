package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class CustomizationTest {
    private val burger = Product("burger", "Hambúrguer", 2000, true, "KITCHEN", "AVAILABLE",
        listOf(ProductVariant("simple", "Simples", 2000, true, true), ProductVariant("double", "Duplo", 3000, true, false)),
        listOf(ModifierGroup("cooking", "Ponto", 1, 1, true, listOf(ModifierOption("medium", "Ao ponto", 0, true, false, "CHOICE"), ModifierOption("rare", "Malpassado", 0, true, false, "CHOICE"))),
            ModifierGroup("extras", "Adicionais", 0, 2, false, listOf(ModifierOption("bacon", "Bacon", 500, true, false, "ADD"), ModifierOption("cheese", "Queijo", 300, true, false, "ADD"), ModifierOption("onion", "Sem cebola", 0, true, false, "REMOVE")))))
    private val selection = Customization("double", listOf("medium", "bacon", "cheese"), "Molho separado")

    @Test fun `same canonical burger cents as guest and server`() {
        assertEquals(3800L, burger.unitPrice(selection))
        assertEquals(7600L, CartLine(burger, 2, selection).let { it.quantity * it.unitPriceCents })
        assertNull(burger.customizationError(selection))
        assertTrue(burger.configurationText(selection).contains("+ Bacon"))
        assertTrue(burger.configurationText(selection).contains("Observação: Molho separado"))
    }
    @Test fun `required single and multi constraints reject stale choices`() {
        assertNotNull(burger.customizationError(Customization()))
        assertNotNull(burger.customizationError(Customization("double")))
        assertNotNull(burger.customizationError(selection.copy(optionIds = listOf("medium", "rare"))))
        assertNotNull(burger.customizationError(selection.copy(optionIds = listOf("medium", "bacon", "cheese", "onion"))))
        val stale = burger.copy(modifierGroups = burger.modifierGroups.map { g -> g.copy(options = g.options.map { if (it.id == "bacon") it.copy(available = false) else it }) })
        assertNotNull(stale.customizationError(selection))
    }
    @Test fun `recovery keeps full immutable intent through restart`() {
        val intent = RecoveryIntent.ConfirmOrder("intent", "staff", "venue", "device", "key", 1L, RecoveryState.PENDING, "tab", listOf(PendingOrderLine("burger", 2, selection)))
        assertEquals(intent, RecoveryIntent.fromJson(intent.toJson()))
    }
    @Test fun `simple products still quick add in integer cents`() {
        val water = Product("water", "Água", 501, true, "BAR", "AVAILABLE")
        assertNull(water.customizationError(water.defaults()))
        assertEquals(1503L, CartLine(water, 3).let { it.unitPriceCents * it.quantity })
    }
}
