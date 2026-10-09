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
    fun `served items offer new work without cancellation and terminal items offer none`() {
        val served = listOf(CorrectionAction.REMAKE, CorrectionAction.REPLACEMENT)
        assertEquals(served, correctionActionsFor("PICKED_UP"))
        assertEquals(served, correctionActionsFor("DELIVERED"))
        assertTrue(correctionActionsFor("CANCELLED").isEmpty())
        assertTrue(correctionActionsFor("UNKNOWN").isEmpty())
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
