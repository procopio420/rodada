package com.rodada.attendance.operations

import com.rodada.attendance.auth.AuthTokens
import com.rodada.attendance.auth.StoredSession
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SessionBoundRecoveryIntentTest {
    private val session = StoredSession(AuthTokens("access", "", "refresh", ""), "staff", "Operator",
        "venue", "venue", "Venue", "STAFF", "device", "TRUSTED", sessionId = "original-session")
    private val intent = RecoveryIntent.ConfirmOrder("intent", "staff", "venue", "device", "original-key",
        42L, RecoveryState.PENDING, "tab", listOf(PendingOrderLine("product", 2)))

    @Test fun `process recreation retains original command key and provenance`() {
        val payload = JSONArray().put(intent.toJson().put("originating_session_id", session.sessionId)).toString()
        val restored = SessionBoundRecoveryIntent.decode(payload).single()
        assertEquals(intent, restored.intent)
        assertEquals("original-key", restored.intent.idempotencyKey)
        assertTrue(restored.canReplay(session))
        assertTrue(restored.canReplay(session.withTokens(session.tokens.copy(accessToken = "rotated"))))
    }

    @Test fun `new login by same operator cannot adopt original command`() {
        val envelope = SessionBoundRecoveryIntent(intent, session.sessionId)
        assertFalse(envelope.canReplay(session.copy(sessionId = "new-session")))
        assertTrue(envelope.sameContext(session.copy(sessionId = "new-session")))
        assertFalse(envelope.canReplay(session.copy(staffId = "another-staff")))
        assertFalse(envelope.canReplay(session.copy(venueId = "another-venue")))
        assertFalse(envelope.canReplay(session.copy(deviceId = "another-device")))
    }

    @Test fun `legacy intent remains available for review but never replay`() {
        val restored = SessionBoundRecoveryIntent.decode(JSONArray().put(intent.toJson()).toString()).single()
        assertEquals(intent, restored.intent)
        assertTrue(restored.sameContext(session))
        assertFalse(restored.canReplay(session))
        assertFalse(restored.canReplay(session.copy(sessionId = "")))
    }

    @Test fun `malformed sibling prevents partial collection overwrite`() {
        val payload = JSONArray().put(intent.toJson()).put(JSONObject().put("type", "UNSUPPORTED")).toString()
        try {
            SessionBoundRecoveryIntent.decode(payload)
            fail("Unreadable history must require review, never appear as a writable partial collection")
        } catch (_: IllegalArgumentException) { }
    }
}
