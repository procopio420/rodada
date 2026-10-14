package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class TabIdentityTest {
    private fun tab(id: String, name: String = "", table: String? = null, last: String? = null) =
        TabSummary(
            id = id, displayLabel = name, state = "OPEN", version = 1,
            chargesCents = 0, paymentsCents = 0, exposureCents = 0,
            tableLabel = table, lastTableLabel = last,
        )

    @Test fun mesaIsPrimaryAndTheTabRemainsDistinguishable() {
        val first = tab("aaaaaaaa-first", "João", "Mesa 08")
        val second = tab("bbbbbbbb-second", "João", "Mesa 08")
        assertEquals("Mesa 08", first.operationalLabel())
        assertTrue(first.operationalSubtitle().contains("João"))
        assertTrue(first.operationalSubtitle() != second.operationalSubtitle())
        assertTrue(first.matchesOperationalQuery("08"))
        assertTrue(first.matchesOperationalQuery("João"))
    }

    @Test fun changingTableDoesNotChangeComandaIdentity() {
        val moved = tab("aaaaaaaa-first", "João", "Mesa 12", "Mesa 08")
        assertEquals("Mesa 12", moved.operationalLabel())
        assertTrue(moved.operationalSubtitle().contains("Comanda AAAAAAAA"))
    }

    @Test fun semMesaHasSafeFallbackAndHistoryMayShowLastTable() {
        val unnamed = tab("abcdef01-x", "Comanda sem nome")
        assertEquals("Comanda ABCDEF01", unnamed.operationalLabel())
        assertEquals("Comanda ABCDEF01", unnamed.operationalSubtitle())
        val historical = tab("abcdef01-x", last = "Mesa 05")
        assertEquals("Comanda ABCDEF01", historical.operationalLabel())
        assertEquals("Mesa 05 (última)", historical.operationalLabel(historical = true))
    }
}
