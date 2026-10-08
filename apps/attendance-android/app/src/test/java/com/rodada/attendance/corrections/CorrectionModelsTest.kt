package com.rodada.attendance.corrections

import org.junit.Assert.assertFalse
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
}
