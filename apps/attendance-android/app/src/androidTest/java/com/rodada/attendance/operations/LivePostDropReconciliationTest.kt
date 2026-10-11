package com.rodada.attendance.operations

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthHttpClient
import com.rodada.attendance.auth.LoginRequest
import com.rodada.attendance.auth.SecureSessionStore
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.IOException
import java.util.UUID

/**
 * True network integration: emulator -> 10.0.2.2 TCP fault proxy -> Django ->
 * disposable PostgreSQL. The proxy waits for HTTP 201 from Django (commit)
 * before RSTing the Android socket WITHOUT sending the result.
 *
 * Stages run in independent instrumentation processes separated by a REAL
 * adb force-stop. No mock HTTP client, fake server or real financial payment.
 */
@RunWith(AndroidJUnit4::class)
class LivePostDropReconciliationTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val base = "http://10.0.2.2:8000/"
    private val authClient get() = AuthHttpClient(base)
    private val orders get() = OperationsHttpClient(base)
    private val sessions get() = SecureSessionStore(context)
    private val queue get() = PendingMutationIntentStore(context)

    @Test fun stage() {
        val phase = instrumentation.arguments.getString("phase")
        assumeTrue("Run only through scripts/android-live-post-drop.sh",
            phase == "capture" || phase == "offline" || phase == "replay")
        when (phase) {
            "capture" -> captureCommittedButLostResponse()
            "offline" -> inspectPendingWithoutNetwork()
            "replay" -> reconcileWithExactlyTheOriginalIntent()
        }
    }

    private fun capturedOrder(): Pair<com.rodada.attendance.auth.StoredSession, RecoveryIntent.ConfirmOrder> {
        val session = sessions.load() ?: error("Session did not survive process death")
        val record = queue.orderQueue(session).singleOrNull()
            ?: error("Encrypted order intent lost after process death")
        assertEquals(RecoveryState.CHECKING, record.state)
        assertEquals(record.id, record.idempotencyKey)
        assertEquals(session.staffId, record.staffId)
        assertEquals(session.venueId, record.venueId)
        assertEquals(session.deviceId, record.deviceId)
        assertTrue(OrderRecoveryPolicy.canReplay(
            record, SessionBoundRecoveryIntent(record, session.sessionId), session))
        assertTrue(queue.orderQueue(session.copy(sessionId = UUID.randomUUID().toString())).isEmpty())
        return session to record
    }

    private fun cart(record: RecoveryIntent.ConfirmOrder) =
        record.lines.map { line ->
            // Id/quantity/customization are the *exact encrypted original payload*.
            // Price is not trusted by Django; it locks/reprices products from Postgres.
            CartLine(
                Product(line.productId, "Isolated CI test product", 700, true, "BAR", "AVAILABLE"),
                line.quantity, line.customization
            )
        }

    private fun captureCommittedButLostResponse() {
        val productId = instrumentation.arguments.getString("productId") ?: error("Missing Postgres product ID")
        val session = authClient.login(LoginRequest(
            venueSlug = "android-post-drop-ci",
            loginIdentifier = "android-post-drop-operator",
            pin = "2468",
            installationId = "android-post-drop-ci-device",
        ))
        assertTrue(session.sessionId.isNotBlank())
        sessions.save(session)
        val tab = orders.openTab(session.tokens.accessToken, "Android TCP reset acceptance")
        val key = UUID.randomUUID().toString()
        val command = RecoveryIntent.ConfirmOrder(
            id = key, staffId = session.staffId, venueId = session.venueId,
            deviceId = session.deviceId, idempotencyKey = key,
            createdAtMillis = System.currentTimeMillis(), state = RecoveryState.PENDING,
            tabId = tab.id, lines = listOf(PendingOrderLine(productId, 1)),
        )
        // Durable BEFORE opening HTTP connection.
        queue.save(command, session)
        queue.updateOrderState(command, session, RecoveryState.CHECKING)
        val exact = queue.orderQueue(session).single()
        assertEquals(command.copy(state = RecoveryState.CHECKING), exact)
        try {
            orders.confirmOrder(session.tokens.accessToken, exact.tabId, cart(exact), exact.idempotencyKey)
            fail("The fault proxy incorrectly returned a response after Django committed")
        } catch (lost: IOException) {
            assertTrue(lost.message.orEmpty().isNotBlank() || lost is java.net.SocketException)
        }
        // Still CHECKING, NOT locally acknowledged or cleared.
        assertEquals(RecoveryState.CHECKING, queue.orderQueue(session).single().state)
    }

    private fun inspectPendingWithoutNetwork() {
        // Runner has disabled Wi-Fi/mobile data and killed the process beforehand.
        val (session, exact) = capturedOrder()
        assertEquals(1, exact.lines.size)
        assertEquals(1, exact.lines.single().quantity)
        assertEquals(RecoveryState.CHECKING, queue.orderQueue(session).single().state)
        // No POST/DELETE/Payment attempt is permitted in the offline phase.
    }

    private fun reconcileWithExactlyTheOriginalIntent() {
        val (session, exact) = capturedOrder()
        // First healthy canonical read proves the original command was committed
        // despite Android never receiving its first POST response.
        val canonicalBefore = orders.tabDetail(session.tokens.accessToken, exact.tabId)
        assertEquals(1, canonicalBefore.orders.size)
        assertEquals(1, canonicalBefore.orders.single().items.size)
        val originalOrderId = canonicalBefore.orders.single().id
        val originalBalance = canonicalBefore.summary.chargesCents
        assertEquals(700L, originalBalance)

        // Production OperationsHttpClient, original encrypted idempotency key +
        // original lines. Backend must return the existing order (HTTP 200).
        orders.confirmOrder(session.tokens.accessToken, exact.tabId, cart(exact), exact.idempotencyKey)
        val canonicalAfter = orders.tabDetail(session.tokens.accessToken, exact.tabId)
        assertEquals(1, canonicalAfter.orders.size)
        assertEquals(originalOrderId, canonicalAfter.orders.single().id)
        assertEquals(originalBalance, canonicalAfter.summary.chargesCents)
        assertEquals(1, canonicalAfter.orders.single().items.size)
        assertEquals(0L, canonicalAfter.summary.paymentsCents)

        // Remove only after the canonical response AND canonical reread succeeded.
        queue.remove(exact.id)
        assertTrue(queue.orderQueue(session).isEmpty())
    }
}
