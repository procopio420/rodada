package com.rodada.attendance.operations

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthTokens
import com.rodada.attendance.auth.StoredSession
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Run each method in a different instrumentation process with adb force-stop
 * between stages. No fixture uses a live merchant or a network request.
 */
@RunWith(AndroidJUnit4::class)
class ForceStopOrderRecoveryTest {
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val session = StoredSession(
        AuthTokens("test-access", "", "test-refresh", ""),
        "force-stop-staff", "Offline waiter", "force-stop-venue", "force-stop-venue",
        "Offline test", "STAFF", "force-stop-device", "UNTRUSTED",
        sessionId = "force-stop-original-session",
    )
    private val key = "force-stop-order-original-key"
    private val intent get() = RecoveryIntent.ConfirmOrder(
        id = key, staffId = session.staffId, venueId = session.venueId, deviceId = session.deviceId,
        idempotencyKey = key, createdAtMillis = 123456789L, state = RecoveryState.PENDING,
        tabId = "test-tab", lines = listOf(PendingOrderLine("test-product", 2)),
    )

    private val tableKey = "force-stop-table-open-original-key"
    private val tableIntent get() = RecoveryIntent.TableService(
        tableKey, session.staffId, session.venueId, session.deviceId, tableKey,
        123456789L, RecoveryState.CHECKING,
        "/hospitality/occupancies/test-visit/tabs/open/",
        """{"idempotency_key":"force-stop-table-open-original-key","expected_generation":3,"display_label":"Ana"}""",
    )

    @Test fun stagedRecovery() {
        val phase = InstrumentationRegistry.getArguments().getString("phase")
        assumeTrue("Explicit multi-process smoke only; see scripts/android-force-stop-recovery.sh",
            phase in setOf("prepare", "offline", "ambiguous"))
        when (phase) {
            "prepare" -> prepareEncryptedPendingOrder()
            "offline" -> verifySurvivesForceStopWhileNetworkUnavailable()
            "ambiguous" -> verifyAmbiguousIntentSurvivesSecondForceStop()
        }
    }

    private fun prepareEncryptedPendingOrder() {
        val store = PendingMutationIntentStore(context)
        store.remove(key)
        store.remove(tableKey)
        store.save(intent, session)
        store.save(tableIntent, session)
        assertEquals(intent, store.orderQueue(session).single { it.id == key })
        val ciphertext = context.getSharedPreferences("rodada_pending_mutation_intents", 0)
            .getString("encrypted_intents", "")!!
        assertTrue(ciphertext.startsWith("v1:"))
        assertFalse(ciphertext.contains("test-product"))
        assertFalse(ciphertext.contains("test-access"))
        assertFalse(ciphertext.contains(key))
        assertFalse(ciphertext.contains(tableKey))
    }

    private fun verifySurvivesForceStopWhileNetworkUnavailable() {
        // This method MUST run after adb force-stop in a fresh instrumentation process.
        val store = PendingMutationIntentStore(context)
        val restoredTable = store.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().single { it.id == tableKey }
        assertEquals(tableIntent, restoredTable)
        assertFalse(store.loadFor(session.copy(sessionId = "second-login")).any { it.id == tableKey })
        assertTrue(store.blockedFor(session.copy(sessionId = "second-login")).any { it.id == tableKey })
        val restored = store.orderQueue(session).single { it.id == key }
        assertEquals(intent, restored)
        assertEquals(key, restored.idempotencyKey)
        assertEquals("test-tab", restored.tabId)
        assertEquals(RecoveryState.PENDING, restored.state)
        assertEquals(2, restored.lines.single().quantity)
        assertTrue(OrderRecoveryPolicy.canReplay(restored,
            SessionBoundRecoveryIntent(restored, session.sessionId), session))
        assertFalse(store.orderQueue(session.copy(sessionId = "second-login")).any { it.id == key })
        assertTrue(store.blockedFor(session.copy(sessionId = "second-login")).any { it.id == key })
        store.updateOrderState(restored, session, RecoveryState.CHECKING)
    }

    private fun verifyAmbiguousIntentSurvivesSecondForceStop() {
        // Simulates kill after POST could have committed but before acknowledgement.
        val store = PendingMutationIntentStore(context)
        val original = store.orderQueue(session).single { it.id == key }
        assertEquals(RecoveryState.CHECKING, original.state)
        assertEquals(key, original.idempotencyKey)
        assertEquals(intent.lines, original.lines)
        assertTrue(OrderRecoveryPolicy.canReplay(original,
            SessionBoundRecoveryIntent(original, session.sessionId), session))
        store.updateOrderState(original, session, RecoveryState.ACTION_REQUIRED)
        assertTrue(OrderRecoveryPolicy.awaitingReconciliation(store.orderQueue(session)).isEmpty())
        assertEquals(RecoveryState.ACTION_REQUIRED, store.orderQueue(session).single { it.id == key }.state)
        assertEquals(tableIntent, store.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().single { it.id == tableKey })
        store.remove(tableKey)
        store.remove(key) // Clean up only after proving all three independently launched stages.
    }
}
