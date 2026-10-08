package com.rodada.attendance.cash

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CashShiftPresentationTest {
    @Test
    fun `cash input uses cents without floating point rounding`() {
        assertEquals(123_456L, parseCashInput("1.234,56"))
        assertEquals(1_050L, parseCashInput("10.50"))
        assertEquals(0L, parseCashInput("0"))
        assertNull(parseCashInput("R$ abc"))
    }

    @Test
    fun `formatted cash remains brazilian operational currency`() {
        assertEquals("R$ 1.234,56", formatCashCents(123_456L))
        assertEquals("-R$ 20,00", formatCashCents(-2_000L))
    }
}
