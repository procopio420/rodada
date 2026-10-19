package com.rodada.attendance.operations

import com.rodada.attendance.payments.IntegratedPayment
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class IntegratedIntentRecoveryTest {
    private val original = RecoveryIntent.StartPayment("new", "staff", "venue", "device", "new-original-key", 1,
        RecoveryState.CHECKING, "tab", 500, PaymentMethod.PIX, null, 3)

    @Test fun `old confirmed Pix does not replace new lost ACK intent after restart`() = runBlocking {
        val old = IntegratedPayment("old", "tab", 500, "CONFIRMED", method = "PIX")
        val restarted = RecoveryIntent.fromJson(original.toJson()) as RecoveryIntent.StartPayment
        var replayed = false
        val result = recoverIntegratedIntent(restarted, {
            assertEquals("new-original-key", it.idempotencyKey)
            assertEquals(3, it.expectedVersion)
            replayed = true
            old.copy(id = "new-payment", status = "PENDING")
        }, {
            assertTrue(replayed)
            assertEquals("new-payment", it)
            old.copy(id = it)
        })
        assertEquals("new-payment", result.id)
        assertNotEquals(old.id, result.id)
    }

    @Test fun `provider requery must retain original id tab amount and method`() = runBlocking {
        val associated = IntegratedPayment("payment", "tab", 500, "PENDING", method = "PIX")
        listOf(associated.copy(id = "old"), associated.copy(tabId = "foreign"),
            associated.copy(amountCents = 1), associated.copy(method = "TAP_TO_PAY")).forEach { wrong ->
            try {
                recoverIntegratedIntent(original, { associated }, { wrong })
                fail("A different provider receipt cannot resolve the original intent")
            } catch (_: IllegalStateException) { }
        }
    }
}
