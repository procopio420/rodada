package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.*
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Real disposable PostgreSQL ledger. External-terminal fixture is NOT PSP settlement evidence. */
class LiveUx2ReceiptRecoveryTest {
    @get:Rule val compose = createComposeRule()

    @Test fun committedPaymentAndCloseLostAckSurviveControllerRestartWithoutDuplicateReceipt() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue(args.getString("liveUx2Receipt") == "true")
        val upstream = requireNotNull(args.getString("upstreamUrl"))
        check(upstream.matches(Regex("""http://10\.0\.2\.2:[0-9]{4,5}/""")))
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18131/")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val session = AuthHttpClient(upstream).login(LoginRequest("android-post-drop-ci", "android-post-drop-operator", "2468", "receipt-" + UUID.randomUUID()))
        SecureSessionStore(context).save(session)
        val api = OperationsHttpClient(upstream)
        val cashPoint = api.cashPoints(session.tokens.accessToken).firstOrNull { it.activeShiftId != null }
        val method = if (cashPoint != null) PaymentMethod.CASH else PaymentMethod.EXTERNAL_TERMINAL
        val auth = AuthRepository(context)
        val queue = PendingMutationIntentStore(context)
        check(queue.loadFor(session).isEmpty())
        val product = api.products(session.tokens.accessToken).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..1000 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        var model by mutableStateOf<OperationsViewModel?>(null)
        compose.setContent { RodadaTheme { Surface {
            model?.let { vm -> vm.state.selectedTab?.let { tab ->
                Ux2ReceiptPage(vm.state, tab, {}, { amount, method, cash, close -> vm.collectPayment(session, amount, method, cash, close) },
                    { vm.recoverReceipt(session) }, { vm.keepPaidTabOpen(session) })
            } }
        } } }
        for (fault in listOf("payment", "close")) {
            val tab = api.openTab(session.tokens.accessToken, "Receipt $fault " + UUID.randomUUID().toString().take(6))
            api.confirmOrder(session.tokens.accessToken, tab.id, listOf(CartLine(product, 1)), UUID.randomUUID().toString())
            compose.runOnUiThread {
                model = OperationsViewModel(OperationsRepository(auth), queue, auth, CorrectionsRepository(auth), RefundsRepository(auth))
                model!!.selectTab(session, tab.id)
            }
            compose.waitUntil(30_000) { model!!.state.selectedTab?.summary?.id == tab.id && !model!!.state.loading }
            val amount = model!!.state.selectedTab!!.summary.exposureCents
            control("arm-$fault")
            compose.runOnUiThread { model!!.collectPayment(session, amount, method, cashPoint?.id, true) }
            compose.waitUntil(45_000) { !model!!.state.submitting && model!!.state.pendingPayment != null }
            val original = queue.loadFor(session).filterIsInstance<RecoveryIntent.StartPayment>().single()
            assertEquals(amount, original.amountCents)
            assertTrue(original.closeRequested)
            if (fault == "close") assertNotNull(original.confirmedPaymentId)
            val committed = api.tabDetail(session.tokens.accessToken, tab.id)
            assertEquals(1, committed.payments.size)
            assertEquals(amount, committed.payments.single().amountCents)
            assertEquals(0L, committed.summary.exposureCents)
            captureCriticalEvidence(compose, "receipt-$fault-unknown", compose.onRoot())
            control("disarm")
            compose.runOnUiThread {
                model = OperationsViewModel(OperationsRepository(auth), queue, auth, CorrectionsRepository(auth), RefundsRepository(auth))
                model!!.selectTab(session, tab.id)
            }
            compose.waitUntil(30_000) { model!!.state.selectedTab?.summary?.id == tab.id && model!!.state.pendingPayment?.id == original.id && !model!!.state.loading }
            compose.runOnUiThread { model!!.recoverReceipt(session) }
            compose.waitUntil(45_000) { !model!!.state.submitting && model!!.state.pendingPayment == null }
            val final = api.tabDetail(session.tokens.accessToken, tab.id)
            assertEquals("CLOSED", final.summary.state)
            assertEquals(1, final.payments.size)
            assertEquals(committed.payments.single().id, final.payments.single().id)
            assertEquals(amount, final.summary.paymentsCents)
            assertTrue(queue.loadFor(session).isEmpty())
        }
    }

    @Test fun delayedReceiptReadCannotReplaceNewSessionTabOrRemoveItsPendingIntent() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue(args.getString("liveUx2Receipt") == "true")
        val upstream = requireNotNull(args.getString("upstreamUrl"))
        check(upstream.matches(Regex("""http://10\.0\.2\.2:[0-9]{4,5}/""")))
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18131/")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val authClient = AuthHttpClient(upstream)
        fun login() = authClient.login(LoginRequest("android-post-drop-ci", "android-post-drop-operator", "2468", "session-fence-" + UUID.randomUUID()))
        val sessionA = login()
        val sessionB = login()
        val store = SecureSessionStore(context)
        store.save(sessionA)
        val api = OperationsHttpClient(upstream)
        val cashPoint = requireNotNull(api.cashPoints(sessionA.tokens.accessToken).firstOrNull { it.activeShiftId != null })
        val product = api.products(sessionA.tokens.accessToken).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..1000 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        val tabA = api.openTab(sessionA.tokens.accessToken, "Session A " + UUID.randomUUID().toString().take(6))
        val tabB = api.openTab(sessionB.tokens.accessToken, "Session B " + UUID.randomUUID().toString().take(6))
        api.confirmOrder(sessionA.tokens.accessToken, tabA.id, listOf(CartLine(product, 1)), UUID.randomUUID().toString())
        val queue = PendingMutationIntentStore(context)
        check(queue.loadFor(sessionA).isEmpty() && queue.loadFor(sessionB).isEmpty())
        val auth = AuthRepository(context)
        lateinit var model: OperationsViewModel
        compose.runOnUiThread {
            model = OperationsViewModel(OperationsRepository(auth), queue, auth, CorrectionsRepository(auth), RefundsRepository(auth))
            model.ensureLoaded(sessionA)
        }
        compose.waitUntil(30_000) { !model.state.loading }
        compose.runOnUiThread { model.selectTab(sessionA, tabA.id) }
        compose.waitUntil(30_000) { model.state.selectedTab?.summary?.id == tabA.id && !model.state.submitting }
        val amount = model.state.selectedTab!!.summary.exposureCents
        control("hold-tab-read/" + tabA.id)
        compose.runOnUiThread { model.collectPayment(sessionA, amount, PaymentMethod.CASH, cashPoint.id, true) }
        compose.waitUntil(15_000) { model.state.pendingPayment?.confirmedPaymentId != null && faultStatus().contains("\"read_holding\": true") }
        val original = queue.loadFor(sessionA).filterIsInstance<RecoveryIntent.StartPayment>().single()
        lateinit var originalRequest: Job
        compose.runOnUiThread { originalRequest = model.viewModelScope.coroutineContext[Job]!!.children.single() }
        val id = UUID.randomUUID().toString()
        val pendingB = RecoveryIntent.StartPayment(id, sessionB.staffId, sessionB.venueId, sessionB.deviceId,
            id, System.currentTimeMillis(), RecoveryState.CHECKING, tabB.id, 1, PaymentMethod.CASH, cashPoint.id, tabB.version)
        queue.save(pendingB, sessionB)
        store.save(sessionB)
        compose.runOnUiThread { model.ensureLoaded(sessionB) }
        compose.waitUntil(15_000) { !model.state.loading }
        compose.runOnUiThread { model.selectTab(sessionB, tabB.id) }
        compose.waitUntil(15_000) { model.state.selectedTab?.summary?.id == tabB.id && model.state.pendingPayment == pendingB && !model.state.submitting }
        val messageB = model.state.noticeMessage
        control("release-tab-read")
        // Wait for the exact original ViewModel coroutine, including its failure/finally callbacks.
        compose.waitUntil(15_000) { !faultStatus().contains("\"read_holding\": true") }
        compose.waitUntil(15_000) { originalRequest.isCompleted }
        androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().waitForIdleSync()
        compose.runOnUiThread {
            assertEquals(tabB.id, model.state.selectedTab?.summary?.id)
            assertEquals(pendingB, model.state.pendingPayment)
            assertEquals(messageB, model.state.noticeMessage)
            assertFalse(model.state.submitting)
        }
        assertEquals(original, queue.loadFor(sessionA).filterIsInstance<RecoveryIntent.StartPayment>().single())
        assertEquals(pendingB, queue.loadFor(sessionB).filterIsInstance<RecoveryIntent.StartPayment>().single())
        val canonical = api.tabDetail(sessionA.tokens.accessToken, tabA.id)
        assertEquals("OPEN", canonical.summary.state)
        assertEquals(1, canonical.payments.size)
        assertEquals(original.confirmedPaymentId, canonical.payments.single().id)
        // Remove only this disposable test's retained records after all assertions.
        queue.remove(original.id); queue.remove(pendingB.id)
        api.closeTab(sessionA.tokens.accessToken, tabA.id)
    }

    private fun faultStatus(): String {
        val connection = URL(BuildConfig.RODADA_API_BASE_URL + "__fault/status").openConnection() as HttpURLConnection
        try { return connection.inputStream.bufferedReader().use { it.readText() } } finally { connection.disconnect() }
    }

    private fun control(action: String) {
        val connection = URL(BuildConfig.RODADA_API_BASE_URL + "__fault/$action").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        try { assertEquals(200, connection.responseCode) } finally { connection.disconnect() }
    }
}
