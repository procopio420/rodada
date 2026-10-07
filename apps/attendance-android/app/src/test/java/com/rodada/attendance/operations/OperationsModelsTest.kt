package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class OperationsModelsTest {
    @Test
    fun `parses brazilian payment amounts as integer cents`() {
        assertEquals(1_234_56L, parseCents("1.234,56"))
        assertEquals(2_500L, parseCents("25"))
        assertEquals(50L, parseCents(",5"))
    }

    @Test
    fun `rejects fractions beyond cents`() {
        assertNull(parseCents("12,345"))
    }

    @Test
    fun `formats money without floating point`() {
        assertEquals("R$ 1.234,56", formatCents(123_456))
        assertEquals("-R$ 0,01", formatCents(-1))
    }
}
