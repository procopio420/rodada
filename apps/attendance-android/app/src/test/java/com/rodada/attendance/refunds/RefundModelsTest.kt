package com.rodada.attendance.refunds

import org.junit.Assert.assertEquals
import org.junit.Test

class RefundModelsTest {
    @Test
    fun `refundable amount never becomes negative`() {
        assertEquals(0, PaymentRefundSummary("payment", 1_000, 1_200, "REFUNDED").refundableCents)
        assertEquals(400, PaymentRefundSummary("payment", 1_000, 600, "CONFIRMED").refundableCents)
    }
}
