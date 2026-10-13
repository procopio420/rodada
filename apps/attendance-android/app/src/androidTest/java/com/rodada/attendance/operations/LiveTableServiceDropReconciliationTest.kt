package com.rodada.attendance.operations

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthHttpClient
import com.rodada.attendance.auth.LoginRequest
import com.rodada.attendance.auth.SecureSessionStore
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.io.IOException
import java.util.UUID

/** Production HTTP, committed Django response dropped, process death, encrypted replay. */
@RunWith(AndroidJUnit4::class)
class LiveTableServiceDropReconciliationTest {
    private val args get() = InstrumentationRegistry.getArguments()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val base get() = args.getString("baseUrl", "http://10.0.2.2:8000/").also {
        require(it.startsWith("http://") && !it.contains("rodada.ai") && !it.contains("up.railway.app"))
    }
    private val sessions get() = SecureSessionStore(context)
    private val queue get() = PendingMutationIntentStore(context)
    private val client get() = OperationsHttpClient(base)

    @Test fun stage() {
        val phase = args.getString("phase")
        assumeTrue("Isolated table-service fault runner only", phase in setOf("capture", "offline", "replay"))
        val mode = args.getString("tableAction") ?: error("Missing action")
        val tableId = args.getString("tableId") ?: error("Missing table")
        if (phase == "capture") {
            val session = sessions.load() ?: AuthHttpClient(base).login(LoginRequest(
                venueSlug = "android-post-drop-ci", loginIdentifier = "android-post-drop-operator",
                pin = "2468", installationId = "android-post-drop-ci-device",
            )).also { sessions.save(it) }
            val table = client.tables(session.tokens.accessToken).single { it.id == tableId }
            val key = UUID.randomUUID().toString()
            val path = if (mode == "start") "/hospitality/tables/$tableId/service/start/"
                else "/hospitality/occupancies/${table.activeOccupancy!!.id}/tabs/open/"
            val payload = JSONObject().put("idempotency_key", key)
            if (mode == "open") payload.put("expected_generation", table.activeOccupancy!!.generation).put("display_label", "Response loss 027")
            val intent = RecoveryIntent.TableService(key, session.staffId, session.venueId, session.deviceId,
                key, System.currentTimeMillis(), RecoveryState.CHECKING, path, payload.toString())
            queue.save(intent, session)
            try {
                client.tableService(session.tokens.accessToken, path, payload)
                fail("Committed response must never reach Android before force-stop")
            } catch (_: IOException) { /* Real TCP reset, keep original encrypted command. */ }
            assertEquals(intent, queue.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().single())
            return
        }
        val session = sessions.load() ?: error("Session lost after process death")
        val intent = queue.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().single()
        assertEquals(RecoveryState.CHECKING, intent.state)
        assertEquals(intent.idempotencyKey, JSONObject(intent.commandJson).getString("idempotency_key"))
        assertEquals(session.venueId, intent.venueId)
        assertEquals(session.staffId, intent.staffId)
        assertTrue(queue.loadFor(session.copy(sessionId = UUID.randomUUID().toString())).isEmpty())
        if (phase == "offline") return // No HTTP permitted here.
        val before = client.tables(session.tokens.accessToken).single { it.id == tableId }.activeOccupancy!!
        assertEquals(session.staffId, before.responsibleStaffId)
        assertEquals(if (mode == "start") 0 else 1, before.tabs.size)
        val result = client.tableService(session.tokens.accessToken, intent.path, JSONObject(intent.commandJson))
        assertTrue(result.getBoolean("replayed"))
        val after = client.tables(session.tokens.accessToken).single { it.id == tableId }.activeOccupancy!!
        assertEquals(before.id, after.id)
        assertEquals(before.generation, after.generation)
        assertEquals(before.tabs.map { it.id }, after.tabs.map { it.id })
        if (mode == "open") {
            val detail = client.tabDetail(session.tokens.accessToken, after.tabs.single().id)
            assertEquals(0L, detail.summary.chargesCents)
            assertEquals(0L, detail.summary.paymentsCents)
            assertTrue(detail.orders.isEmpty())
        }
        queue.remove(intent.id)
        assertTrue(queue.loadFor(session).filterIsInstance<RecoveryIntent.TableService>().isEmpty())
    }
}
