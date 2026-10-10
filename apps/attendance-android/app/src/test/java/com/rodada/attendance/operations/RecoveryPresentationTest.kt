package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class RecoveryPresentationTest {
    @Test fun `local evidence retains capture and blocked origin without claiming confirmation`() {
        val intent = RecoveryIntent.ConfirmOrder("request", "staff", "venue", "device", "key", 12345, RecoveryState.CHECKING, "tab", emptyList())
        val own = intent.evidence()
        assertEquals("Pedido", own.label)
        assertEquals(12345L, own.capturedAtMillis)
        assertFalse(own.reviewOnly)
        val blocked = intent.evidence(reviewOnly = true)
        assertTrue(blocked.reviewOnly)
        assertEquals(own.id, blocked.id)
    }
}
