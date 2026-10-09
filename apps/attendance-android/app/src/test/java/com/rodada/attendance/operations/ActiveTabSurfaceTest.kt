package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Test

class ActiveTabSurfaceTest {
    @Test fun financialCloseLeavesHistoryInAccountsButNotAgora() {
        val open = TabSummary("open", "Aberta", "OPEN", 1, 1000, 0, 1000)
        val action = open.copy(id = "attention", state = "REQUIRES_ACTION")
        val closed = open.copy(id = "closed", state = "CLOSED", paymentsCents = 1000, exposureCents = 0)
        val snapshot = listOf(closed, open, action)
        assertEquals(listOf(open, action), tabsForSurface(snapshot, true))
        assertEquals(snapshot, tabsForSurface(snapshot, false))
        assertEquals("CLOSED", closed.state)
    }
}
