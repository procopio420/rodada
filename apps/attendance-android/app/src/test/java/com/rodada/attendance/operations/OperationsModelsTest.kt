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

    @Test fun `parses comma dot currency and exact long boundary`() {
        assertEquals(300L, parseCents("3.00"))
        assertEquals(300L, parseCents("3,00"))
        assertEquals(123456L, parseCents(" R$ 1.234,56 "))
        assertEquals(50L, parseCents(".5"))
        assertEquals(0L, parseCents("0,00"))
        assertEquals(Long.MAX_VALUE, parseCents("92233720368547758.07"))
    }

    @Test fun `invalid text and overflow never become positive money`() {
        listOf("-3,00", "+3,00", "abc3,00", "3abc", "3,", "3.0.0", "1,234.56",
            "12,345", "1.234", "3 00", "92233720368547758.08", "999999999999999999999999")
            .forEach { assertNull(it, parseCents(it)) }
    }

    @Test
    fun `formats money without floating point`() {
        assertEquals("R$ 1.234,56", formatCents(123_456))
        assertEquals("-R$ 0,01", formatCents(-1))
    }
}
