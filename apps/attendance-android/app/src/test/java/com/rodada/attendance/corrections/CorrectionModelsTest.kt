package com.rodada.attendance.corrections

import org.junit.Assert.assertFalse
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CorrectionModelsTest {
    @Test
    fun `only early cancellation uses non privileged endpoint`() {
        val early = CorrectionCommand("item", "NEW", CorrectionAction.CANCEL, "DUPLICATE", "", "key")
        val preparing = early.copy(itemState = "PREPARING")
        val remake = early.copy(action = CorrectionAction.REMAKE)

        assertFalse(early.requiresPostProductionEndpoint())
        assertTrue(preparing.requiresPostProductionEndpoint())
        assertTrue(remake.requiresPostProductionEndpoint())
    }

    @Test
    fun `early items expose only the correction the API accepts`() {
        assertEquals(listOf(CorrectionAction.CANCEL), correctionActionsFor("NEW"))
        assertEquals(listOf(CorrectionAction.CANCEL), correctionActionsFor("ACCEPTED"))
        assertEquals(CorrectionAction.entries, correctionActionsFor("PREPARING"))
        assertEquals(CorrectionAction.entries, correctionActionsFor("READY"))
    }

    @Test
    fun `served items allow authorized wrong entry correction and terminal items offer none`() {
        val served = CorrectionAction.entries
        assertEquals(served, correctionActionsFor("PICKED_UP"))
        assertEquals(served, correctionActionsFor("DELIVERED"))
        assertTrue(correctionActionsFor("CANCELLED").isEmpty())
        assertTrue(correctionActionsFor("UNKNOWN").isEmpty())
    }

    @Test fun `explicit cancellation quantity uses authorized wrong entry endpoint without changing legacy`() {
        val original = CorrectionCommand("item", "NEW", CorrectionAction.CANCEL, "WRONG_ENTRY", "Motivo", "key")
        assertFalse(original.requiresPostProductionEndpoint())
        assertEquals("CANCEL_ITEM", original.apiKind)
        val selected = original.copy(quantity = 2)
        assertTrue(selected.requiresPostProductionEndpoint())
        assertEquals("WRONG_ITEM_ENTERED", selected.apiKind)
        assertEquals(2, selected.quantity)
    }

    @Test
    fun `replacement consequence states the canonical positive delta`() {
        val result = CorrectionResult(
            id = "correction",
            status = "APPLIED",
            kind = CorrectionAction.REPLACEMENT.apiKind,
            financialDisposition = "REVERSE_OPEN_RESPONSIBILITY",
            refundRequiredCents = 0,
            replacementOrderItemId = "replacement",
            orderItemId = "item",
            orderItemState = "CANCELLED",
            financialDeltaCents = 500,
            chargesCents = 1_900,
            paymentsCents = 0,
            refundsCents = 0,
            exposureCents = 2_400,
        )

        assertEquals("Diferença a cobrar: + R$ 5,00.", correctionConsequence(result))
    }
}
