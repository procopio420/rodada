package com.rodada.attendance.operations

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class ReceiptSettlementTest {
    private val intent = RecoveryIntent.StartPayment("intent", "staff", "venue", "device", "original-key", 1,
        RecoveryState.CHECKING, "tab", 1200, PaymentMethod.CASH, "cash", 7, true)
    private fun detail(balance: Long = 0, state: String = "OPEN", confirmed: Boolean = true) = TabDetail(
        TabSummary("tab", "Ana", state, 8, 1200, 1200, balance), emptyList(),
        if (confirmed) listOf(TabPayment("payment", 1200, "CASH", "CONFIRMED", 0)) else emptyList())

    @Test fun `checkpoint survives restart and close lost ACK without another payment`() = runBlocking {
        var durable = intent
        var posts = 0
        var closes = 0
        var closed = false
        val collect: suspend (RecoveryIntent.StartPayment) -> String = {
            posts++; assertEquals("original-key", it.idempotencyKey); "payment"
        }
        try {
            settleReceipt(durable, collect, { durable = it }, { detail(state = if (closed) "CLOSED" else "OPEN") },
                { closes++; closed = true; error("ACK lost") }, {})
            fail("Expected lost ACK")
        } catch (_: IllegalStateException) { }
        val restarted = RecoveryIntent.fromJson(durable.toJson()) as RecoveryIntent.StartPayment
        val result = settleReceipt(restarted, collect, {}, { detail(state = "CLOSED") }, { closes++ }, {})
        assertEquals("CLOSED", result.summary.state)
        assertEquals(1, posts); assertEquals(1, closes)
    }

    @Test fun `checkpoint failure prohibits closing and original command remains unchanged`() = runBlocking {
        var closes = 0
        try {
            settleReceipt(intent, { "payment" }, { error("disk full") }, { detail() }, { closes++ }, {})
            fail("Expected storage failure")
        } catch (_: IllegalStateException) { }
        assertEquals(0, closes)
        assertNull(intent.confirmedPaymentId)
        assertEquals(7, intent.expectedVersion)
    }

    @Test fun `partial receipt never closes and concurrent consumption preserves paid checkpoint`() = runBlocking {
        var closes = 0
        val partial = intent.copy(closeRequested = false)
        assertEquals(500L, settleReceipt(partial, { "payment" }, {}, { detail(500) }, { closes++ }, {}).summary.exposureCents)
        var durable = intent
        try {
            settleReceipt(intent, { "payment" }, { durable = it }, { detail(500) }, { closes++ }, {})
            fail("Expected new balance to prevent closing")
        } catch (_: IllegalStateException) { }
        assertEquals("payment", durable.confirmedPaymentId)
        assertEquals(0, closes)
    }

    @Test fun `missing canonical payment cannot trigger close`() = runBlocking {
        var closes = 0
        try {
            settleReceipt(intent, { "payment" }, {}, { detail(confirmed = false) }, { closes++ }, {})
            fail("Expected missing payment")
        } catch (_: IllegalStateException) { }
        assertEquals(0, closes)
    }

    @Test fun `payment ACK lost reuses exact command and close failure retries only close`() = runBlocking {
        var durable = intent
        val keys = mutableListOf<String>()
        var first = true
        val collect: suspend (RecoveryIntent.StartPayment) -> String = {
            keys += it.idempotencyKey
            assertEquals(7, it.expectedVersion)
            if (first) { first = false; error("Payment committed response lost") }
            "payment"
        }
        try { settleReceipt(durable, collect, { durable = it }, { detail() }, {}, {}); fail() }
        catch (_: IllegalStateException) { }
        try { settleReceipt(durable, collect, { durable = it }, { detail() }, { error("Close 503") }, {}); fail() }
        catch (_: IllegalStateException) { }
        assertEquals("payment", durable.confirmedPaymentId)
        var closed = false
        settleReceipt(durable, { error("Must never collect confirmed payment") }, {},
            { detail(state = if (closed) "CLOSED" else "OPEN") }, { closed = true }, {})
        assertEquals(listOf("original-key", "original-key"), keys)
        assertTrue(closed)
    }

    @Test fun `foreign tab and pending or simulated payment cannot close`() = runBlocking {
        val valid = detail()
        val invalid = listOf(valid.copy(summary = valid.summary.copy(id = "foreign")),
            valid.copy(payments = valid.payments.map { it.copy(status = "PENDING") }),
            valid.copy(payments = valid.payments.map { it.copy(simulated = true) }),
            valid.copy(payments = valid.payments.map { it.copy(amountCents = 1) }),
            valid.copy(payments = valid.payments.map { it.copy(method = "PIX") }))
        invalid.forEach { snapshot ->
            var closed = false
            try { settleReceipt(intent, { "payment" }, {}, { snapshot }, { closed = true }, {}); fail() }
            catch (_: IllegalStateException) { }
            assertFalse(closed)
        }
    }

    @Test fun `legacy payment envelope defaults to no automatic closing`() {
        val json = intent.copy(closeRequested = false).toJson().apply { remove("close_requested"); remove("confirmed_payment_id") }
        val restored = RecoveryIntent.fromJson(json) as RecoveryIntent.StartPayment
        assertFalse(restored.closeRequested); assertNull(restored.confirmedPaymentId)
        assertEquals(intent.idempotencyKey, restored.idempotencyKey)
        assertEquals(intent.amountCents, restored.amountCents)
    }
}
