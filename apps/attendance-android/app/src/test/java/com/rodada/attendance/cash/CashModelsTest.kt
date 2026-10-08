package com.rodada.attendance.cash

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class CashModelsTest {
    @Test
    fun `cash commands preserve signed cents and optimistic version without floating point`() {
        val withdrawal = CashWithdrawalCommand(
            amountCents = 12_345,
            reason = "Cofre",
            idempotencyKey = "withdrawal-1",
        )
        val close = CloseCashShiftCommand(
            countedAmountCents = 98_765,
            reviewThresholdCents = 100,
            expectedVersion = 7,
        )

        assertEquals(12_345, withdrawal.amountCents)
        assertFalse(withdrawal.allowNegativeExpected)
        assertEquals(7, close.expectedVersion)
    }

    @Test
    fun `late correction keeps optional original movement reference explicit`() {
        val correction = LateCashCorrectionCommand(
            amountCents = -100,
            reason = "Sangria histórica omitida",
            idempotencyKey = "correction-1",
        )

        assertEquals(-100, correction.amountCents)
        assertNull(correction.correctionOfId)
    }
}
