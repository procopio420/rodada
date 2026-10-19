package com.rodada.attendance.operations

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException

class DeliveryRecoveryTest {
    private fun read(state: String = "OPEN", item: String = "READY", id: String = "item") = DeliveryRecoveryRead("task", id, state, item)

    @Test fun `committed lost ACK then reconstructed recovery reads DONE without another POST`() = runBlocking {
        var canonical = read()
        var posts = 0
        val durableTaskId = "task"
        try {
            reconcileDelivery(durableTaskId, true, { canonical }, { posts++; canonical = read("DONE", "DELIVERED"); throw IOException("ACK lost") }, {})
            fail("Unknown ACK must retain original intent")
        } catch (_: IOException) { }
        val recovered = reconcileDelivery(durableTaskId, false, { canonical }, { posts++ }, {})
        assertTrue(recovered.confirmed)
        assertEquals(1, posts)
    }

    @Test fun `success requires exact terminal item evidence and same identities`() = runBlocking {
        for (after in listOf(read("DONE", "READY"), read("OPEN", "DELIVERED"), read("DONE", "DELIVERED", "other"))) {
            var reads = 0
            try {
                reconcileDelivery("task", true, { if (reads++ == 0) read() else after }, {}, {})
                fail("Mismatched or nonterminal evidence must stay pending")
            } catch (_: IllegalStateException) { }
        }
    }

    @Test fun `cancelled unknown and unreadable task never submit or imply completion`() = runBlocking {
        for (state in listOf("CANCELLED", "FUTURE_STATE")) {
            var posts = 0
            val observed = reconcileDelivery("task", false, { read(state) }, { posts++ }, {})
            assertFalse(observed.confirmed)
            try { reconcileDelivery("task", true, { read(state) }, { posts++ }, {}); fail("Not deliverable") }
            catch (_: IllegalStateException) { }
            assertEquals(0, posts)
        }
        try { reconcileDelivery("task", false, { throw IOException("Read unavailable") }, { fail("No mutation") }, {}); fail("Unknown") }
        catch (_: IOException) { }
    }

    @Test fun `late read after A B A cannot mutate durable intent or presentation`() = runBlocking {
        val fence = FinancialResponseFence()
        val guard = fence.capture({ true })
        val started = CompletableDeferred<Unit>(); val release = CompletableDeferred<Unit>()
        var removed = false; var published = false; var posts = 0
        val operation = async {
            try {
                reconcileDelivery("task", true, { started.complete(Unit); release.await(); read("DONE", "DELIVERED") }, { posts++ }, guard::check)
                guard.check(); removed = true; published = true
            } catch (_: CancellationException) { if (guard.isCurrent()) published = true }
        }
        started.await(); fence.invalidate(); fence.invalidate(); release.complete(Unit); operation.await()
        assertFalse(removed); assertFalse(published); assertEquals(0, posts)
    }

    @Test fun `late failed read after session change cannot publish error`() = runBlocking {
        val fence = FinancialResponseFence(); val guard = fence.capture({ true })
        var published = false
        try {
            reconcileDelivery("task", true, { fence.invalidate(); throw IOException("late A failure") }, {}, guard::check)
        } catch (_: IOException) { if (guard.isCurrent()) published = true }
        assertFalse(published)
    }

    @Test fun `successful POST with readback unavailable remains recoverable without another mutation`() = runBlocking {
        var canonical = read(); var posts = 0; var reads = 0
        try {
            reconcileDelivery("task", true, { if (reads++ > 0) throw IOException("Readback lost") else canonical },
                { posts++; canonical = read("DONE", "DELIVERED") }, {})
            fail("Missing readback cannot confirm")
        } catch (_: IOException) { }
        assertTrue(reconcileDelivery("task", true, { canonical }, { posts++ }, {}).confirmed)
        assertEquals(1, posts)
    }

    @Test fun `picked up item completes using same task and exact terminal read`() = runBlocking {
        var canonical = read(item = "PICKED_UP"); var posts = 0
        val result = reconcileDelivery("task", true, { canonical }, { posts++; canonical = read("DONE", "DELIVERED") }, {})
        assertTrue(result.confirmed); assertEquals(1, posts)
    }

    @Test fun `terminal parser accepts DONE but rejects wrong type id and absent item`() {
        val json = JSONObject().put("id", "task").put("task_type", "DELIVERY").put("order_item_id", "item").put("state", "DONE").put("item_state", "DELIVERED")
        assertTrue(DeliveryRecoveryRead.fromJson(json, "task").confirmed)
        for (changed in listOf(JSONObject(json.toString()).put("id", "other"), JSONObject(json.toString()).put("task_type", "BILL_REQUEST"), JSONObject(json.toString()).put("order_item_id", JSONObject.NULL))) {
            assertThrows(Exception::class.java) { DeliveryRecoveryRead.fromJson(changed, "task") }
        }
    }
}
