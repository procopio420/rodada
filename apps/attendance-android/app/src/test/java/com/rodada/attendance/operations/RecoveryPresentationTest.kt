package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class RecoveryPresentationTest {
    @Test fun `cash evidence resolves only original shift and hides blocked destination`() {
        val movement = RecoveryIntent.CashMovement("movement", "staff", "venue", "device", "original-key", 42,
            RecoveryState.CHECKING, "closed-original-shift", CashMovementRecoveryKind.WITHDRAWAL, 1234, "Original reason", false, null)
        val close = RecoveryIntent.CashClose("close", "staff", "venue", "device", "original-close-key", 42,
            RecoveryState.CHECKING, "closed-original-shift", 4321, 0, 7)
        listOf(movement, close).forEach { original ->
            val json = original.toJson().toString()
            assertEquals("closed-original-shift", original.evidence().shiftId)
            assertTrue(original.evidence().canOpenContext)
            assertNull(original.evidence(true).shiftId)
            assertFalse(original.evidence(true).canOpenContext)
            assertEquals(json, original.toJson().toString())
        }
    }
    @Test fun `local evidence retains capture and blocked origin without claiming confirmation`() {
        val intent = RecoveryIntent.ConfirmOrder("request", "staff", "venue", "device", "key", 12345, RecoveryState.CHECKING, "tab", emptyList())
        val own = intent.evidence()
        assertEquals("Pedido", own.label)
        assertEquals(12345L, own.capturedAtMillis)
        assertFalse(own.reviewOnly)
        val blocked = intent.evidence(reviewOnly = true)
        assertTrue(blocked.reviewOnly)
        assertEquals(own.id, blocked.id)
        assertEquals("tab", own.tabId)
        assertTrue(own.canOpenContext)
        assertFalse(blocked.canOpenContext)
        assertNull(blocked.tabId)
    }

    @Test fun `payment context preserves original amount method key and command`() {
        val intent = RecoveryIntent.StartPayment("payment", "staff", "venue", "device", "original", 42,
            RecoveryState.CHECKING, "closed-tab", 1234, PaymentMethod.CASH, "point", 7)
        val before = intent.toJson().toString()
        val row = intent.evidence()
        assertEquals("closed-tab", row.tabId)
        assertTrue(row.summary.contains(formatCents(1234)))
        assertTrue(row.summary.contains(PaymentMethod.CASH.label))
        assertEquals(before, intent.toJson().toString())
        assertEquals("original", intent.idempotencyKey)
    }

    @Test fun `delivery and refund resolve only within the original session`() {
        val delivery = RecoveryIntent.CompleteDelivery("delivery", "staff", "venue", "device", "original", 42, RecoveryState.CHECKING, "task")
        assertEquals("task", delivery.evidence().taskId)
        assertTrue(delivery.evidence().canOpenContext)
        assertFalse(delivery.evidence(true).canOpenContext)
        val refund = RecoveryIntent.Refund("refund", "staff", "venue", "device", "original", 42,
            RecoveryState.CHECKING, RefundRecoveryKind.DIRECT, "payment", null, 100, null, null)
        assertTrue(refund.evidence().canOpenContext)
        assertTrue(refund.evidence().needsExceptionalContext)
        assertFalse(refund.evidence(true).canOpenContext)
    }

    @Test fun `queue evidence is deduplicated oldest first and retains blocked records`() {
        val order = RecoveryIntent.ConfirmOrder("order", "staff", "venue", "device", "original", 42, RecoveryState.PENDING, "tab", emptyList())
        val blocked = order.copy(id = "blocked", createdAtMillis = 12).evidence(true)
        val rows = OperationsUiState(recoveryEvidence = listOf(order.evidence(), blocked), queuedOrders = listOf(order)).pendingEvidence()
        assertEquals(listOf("blocked", "order"), rows.map { it.id })
        assertTrue(rows.first().reviewOnly)
    }

    @Test fun `unknown and stale reads do not invent measured queue counts`() {
        assertEquals("—", nowQueueCounts(OperationsUiState())[NowQueue.READY])
        val fresh = OperationsUiState(lastSyncedAtMillis = 42, connectivity = ConnectivityState.ONLINE, serviceRequestsFresh = true, deliveryTasksFresh = true)
        assertEquals("0", nowQueueCounts(fresh)[NowQueue.READY])
        assertEquals("—", nowQueueCounts(fresh.copy(deliveryTasksFresh = false))[NowQueue.READY])
        assertEquals("0", nowQueueCounts(fresh)[NowQueue.CALLS])
        assertEquals("—", nowQueueCounts(fresh.copy(connectivity = ConnectivityState.STALE))[NowQueue.READY])
        assertEquals("—", nowQueueCounts(fresh.copy(connectivity = ConnectivityState.OFFLINE))[NowQueue.CALLS])
    }
}
