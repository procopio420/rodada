package com.rodada.attendance.operations

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class FinancialResponseFenceTest {
    private val original = RecoveryIntent.StartPayment("a", "staff-a", "venue-a", "device", "key-a", 1,
        RecoveryState.CHECKING, "tab-a", 1200, PaymentMethod.CASH, "cash-a", 7, true)
    private fun detail() = TabDetail(TabSummary("tab-a", "Ana", "OPEN", 8, 1200, 1200, 0),
        emptyList(), listOf(TabPayment("payment-a", 1200, "CASH", "CONFIRMED", 0)))

    @Test fun `session B intent survives delayed session A receipt read and late failure`() = runBlocking {
        val fence = FinancialResponseFence()
        var expected = original
        var pending = original
        val durable = mutableMapOf(original.id to original)
        var submitting = true
        var selected = "tab-a"
        var notices = 0
        var closes = 0
        val guard = fence.capture({ pending == expected && durable[expected.id] == expected }, { expected = it })
        val reading = CompletableDeferred<Unit>()
        val release = CompletableDeferred<Unit>()
        val operation = async {
            try {
                settleReceipt(original, { "payment-a" }, { confirmed ->
                    guard.check(); durable[confirmed.id] = confirmed; pending = confirmed; guard.checkpoint(confirmed)
                }, { reading.complete(Unit); release.await(); detail() }, { closes++ }, { selected = it.summary.id }, guard::check)
                guard.check()
                durable.remove(original.id)
                submitting = false
            } catch (_: CancellationException) {
                // Mirrors ViewModel failure/finally: a stale completion must do nothing.
                if (guard.isCurrent()) { notices++; submitting = false }
            }
        }
        reading.await()
        fence.invalidate() // ensureLoaded(session B)
        val newer = original.copy(id = "b", staffId = "staff-b", venueId = "venue-b", tabId = "tab-b", idempotencyKey = "key-b")
        pending = newer; durable[newer.id] = newer; selected = "tab-b"; submitting = true
        release.complete(Unit)
        operation.await()
        assertEquals("tab-b", selected)
        assertEquals(newer, pending)
        assertTrue(submitting)
        assertEquals(0, notices)
        assertEquals(0, closes)
        assertEquals("payment-a", durable[original.id]?.confirmedPaymentId)
        assertEquals(newer, durable[newer.id])
    }

    @Test fun `late Pix callback cannot pass after A B A or intent replacement`() {
        val fence = FinancialResponseFence()
        var pending = original
        val old = fence.capture({ pending == original })
        fence.invalidate(); fence.invalidate()
        assertFalse(old.isCurrent())
        val current = fence.capture({ pending == original })
        pending = original.copy(id = "new", idempotencyKey = "new-key")
        assertFalse(current.isCurrent())
    }

    @Test fun `storage verification failure still permits current session error presentation`() {
        val fence = FinancialResponseFence()
        val guard = fence.capture(current = { true }, verify = { error("Unreadable encrypted storage") })
        try { guard.check(); fail("Cannot mutate without durable verification") }
        catch (_: IllegalStateException) { }
        assertTrue(guard.isCurrent())
        fence.invalidate()
        assertFalse(guard.isCurrent())
    }

    @Test fun `late collect response cannot checkpoint or close after session changes`() = runBlocking {
        val fence = FinancialResponseFence()
        val guard = fence.capture({ true })
        var checkpoints = 0
        var reads = 0
        try {
            settleReceipt(original, { fence.invalidate(); "payment-a" }, { checkpoints++ },
                { reads++; detail() }, { fail("Must not close") }, {}, guard::check)
            fail("Stale response must stop")
        } catch (_: CancellationException) { }
        assertEquals(0, checkpoints); assertEquals(0, reads)
    }
}
