package com.rodada.attendance.operations

import com.rodada.attendance.auth.AuthTokens
import com.rodada.attendance.auth.StoredSession
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Test

class OrderRecoveryPolicyTest {
    private val session = StoredSession(
        AuthTokens("access", "", "refresh", ""), "staff", "Worker", "venue", "venue",
        "Venue", "STAFF", "device", "UNTRUSTED", sessionId = "session-a",
    )
    private fun order(key: String, time: Long = 1, state: RecoveryState = RecoveryState.PENDING) =
        RecoveryIntent.ConfirmOrder(
            id = key, staffId = "staff", venueId = "venue", deviceId = "device",
            idempotencyKey = key, createdAtMillis = time, state = state,
            tabId = "tab", lines = listOf(PendingOrderLine("product", 2)),
        )

    @Test fun encryptedEnvelopeRetainsOriginalOrderKeyAcrossProcessRepresentation() {
        val pending = order("original-key")
        val serialized = JSONArray().put(pending.toJson().put("originating_session_id", session.sessionId))
        val restored = SessionBoundRecoveryIntent.decode(serialized.toString()).single()
        assertEquals(pending, restored.intent)
        assertTrue(OrderRecoveryPolicy.canReplay(pending, restored, session))
        assertEquals("original-key", (restored.intent as RecoveryIntent.ConfirmOrder).idempotencyKey)
        assertFalse(OrderRecoveryPolicy.canReplay(pending, restored, session.copy(sessionId = "fresh-login")))
        assertFalse(OrderRecoveryPolicy.canReplay(pending, restored, session.copy(venueId = "other")))
        assertFalse(OrderRecoveryPolicy.canReplay(pending, restored, session.copy(staffId = "other")))
        assertFalse(OrderRecoveryPolicy.canReplay(pending, restored, session.copy(deviceId = "other")))
        assertTrue(OrderRecoveryPolicy.canReplay(pending, restored, session.withTokens(session.tokens.copy(accessToken = "rotated"))))
    }

    @Test fun uncertainPostCommitCanReplaySameKeyButConflictCannot() {
        val checking = order("post-timeout", state = RecoveryState.CHECKING)
        assertTrue(OrderRecoveryPolicy.canReplay(checking, SessionBoundRecoveryIntent(checking, session.sessionId), session))
        val conflict = checking.copy(state = RecoveryState.ACTION_REQUIRED)
        assertFalse(OrderRecoveryPolicy.canReplay(conflict, SessionBoundRecoveryIntent(conflict, session.sessionId), session))
        val terminal = checking.copy(state = RecoveryState.FAILED_TERMINAL)
        assertFalse(OrderRecoveryPolicy.canReplay(terminal, SessionBoundRecoveryIntent(terminal, session.sessionId), session))
    }

    @Test fun durableOrderQueueIsOldestFirstAndExcludesPayments() {
        val second = order("second", time = 200)
        val first = order("first", time = 100)
        val review = order("review", time = 50, state = RecoveryState.ACTION_REQUIRED)
        val payment = RecoveryIntent.StartPayment(
            "pay", "staff", "venue", "device", "pay", 25L,
            RecoveryState.CHECKING, "tab", 1000L, PaymentMethod.CASH, null,
        )
        val queue = listOf<RecoveryIntent>(second, payment, first, review)
        assertEquals(listOf("first", "second"), OrderRecoveryPolicy.awaitingReconciliation(queue).map { it.id })
        assertEquals(listOf("review", "first", "second"), OrderRecoveryPolicy.displayQueue(queue).map { it.id })
        assertEquals("review", OrderRecoveryPolicy.nextForTab(queue, "tab")?.id)
    }

    @Test fun malformedOrEmptyCommandsAreNeverReplayed() {
        val empty = order("empty").copy(lines = emptyList())
        assertFalse(OrderRecoveryPolicy.canReplay(empty, SessionBoundRecoveryIntent(empty, session.sessionId), session))
        val invalidQuantity = order("quantity").copy(lines = listOf(PendingOrderLine("p", 0)))
        assertFalse(OrderRecoveryPolicy.canReplay(invalidQuantity, SessionBoundRecoveryIntent(invalidQuantity, session.sessionId), session))
    }
}
