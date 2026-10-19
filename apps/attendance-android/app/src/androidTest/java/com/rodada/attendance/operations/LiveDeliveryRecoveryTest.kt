package com.rodada.attendance.operations

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.*
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Real ViewModel + encrypted storage + isolated Django/PostgreSQL; external loopback fault proxy. */
class LiveDeliveryRecoveryTest {
    @get:Rule val compose = createComposeRule()
    private val args get() = InstrumentationRegistry.getArguments()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val upstream get() = "http://10.0.2.2:18134/"
    private val store get() = PendingMutationIntentStore(context)
    private val sessions get() = SecureSessionStore(context)
    private val api get() = OperationsHttpClient(upstream)
    private fun login(suffix: String): StoredSession = AuthHttpClient(upstream).login(LoginRequest(
        args.getString("venue")!!, args.getString("operator")!!, args.getString("testPin")!!, "delivery-$suffix-${UUID.randomUUID()}"))
    private fun model(): OperationsViewModel {
        val auth = AuthRepository(context)
        return OperationsViewModel(OperationsRepository(auth), store, auth, CorrectionsRepository(auth), RefundsRepository(auth))
    }
    private fun waitLoaded(vm: OperationsViewModel) = compose.waitUntil(30_000) { !vm.state.loading && vm.state.lastSyncedAtMillis != null }
    private fun control(action: String, task: String = "", mode: String = "off"): JSONObject {
        val connection = URL("http://10.0.2.2:18135/__delivery_fault/$action").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"; connection.doOutput = true
        connection.outputStream.use { it.write(JSONObject().put("task",task).put("mode",mode).toString().toByteArray()) }
        return try { JSONObject(connection.inputStream.bufferedReader().readText()) } finally { connection.disconnect() }
    }
    private fun fixture(session: StoredSession): String {
        val token = session.tokens.accessToken
        val product = api.products(token).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..3000 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        val tab = api.openTab(token,"Recovery delivery ${UUID.randomUUID()}")
        api.confirmOrder(token,tab.id,listOf(CartLine(product,1)),UUID.randomUUID().toString())
        val item = api.tabDetail(token,tab.id).orders.single().items.single()
        for (state in listOf("PREPARING","READY")) api.request("POST","/order-items/${item.id}/transition/",JSONObject().put("state",state),token)
        return api.deliveryTasks(token).single { it.orderItemId == item.id }.id
    }
    private fun requireRunner() {
        assumeTrue(args.getString("liveDeliveryRecovery") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18135/")
    }

    @Test fun committedLostAckReconstructedViewModelReadsTerminalWithoutSecondPost() {
        requireRunner(); val session=login("ack");sessions.save(session)
        val task=fixture(session);var vm=model()
        compose.runOnUiThread { vm.ensureLoaded(session) };waitLoaded(vm)
        control("arm",task,"drop")
        compose.runOnUiThread { vm.completeDelivery(session,task) }
        compose.waitUntil(30_000) { !vm.state.submitting && vm.state.errorMessage != null }
        val original=store.loadFor(session).filterIsInstance<RecoveryIntent.CompleteDelivery>().single { it.deliveryTaskId==task }
        val canonical=api.request("GET","/dispatch/tasks/$task/",accessToken=session.tokens.accessToken)
        assertEquals("DONE",canonical.getString("state"));assertEquals("DELIVERED",canonical.getString("item_state"))
        val item=canonical.getString("order_item_id")
        vm=model();compose.runOnUiThread { vm.ensureLoaded(session) };waitLoaded(vm)
        assertEquals(original,store.loadFor(session).single { it.id==original.id })
        compose.runOnUiThread { vm.openRecovery(session,original.id) }
        compose.waitUntil(30_000) { !vm.state.submitting && store.loadFor(session).none { it.id==original.id } }
        assertEquals("Entrega concluída.",vm.state.noticeMessage)
        assertEquals(1,control("status").getInt("posts"))
        val after=api.request("GET","/dispatch/tasks/$task/",accessToken=session.tokens.accessToken)
        assertEquals(item,after.getString("order_item_id"));assertEquals(canonical.getString("completed_at"),after.getString("completed_at"))
        control("arm")
    }

    @Test fun lateSuccessAndFailureCannotReplaceNewSessionOrDeleteOriginalIntent() {
        requireRunner()
        for(mode in listOf("hold","hold-fail")) {
            val a=login("a");sessions.save(a);val task=fixture(a);val vm=model()
            compose.runOnUiThread { vm.ensureLoaded(a) };waitLoaded(vm)
            control("arm",task,mode)
            compose.runOnUiThread { vm.completeDelivery(a,task) }
            compose.waitUntil(20_000) { control("status").getBoolean("held") }
            val original=store.loadFor(a).filterIsInstance<RecoveryIntent.CompleteDelivery>().single { it.deliveryTaskId==task }
            val b=login("b");sessions.save(b)
            compose.runOnUiThread { vm.ensureLoaded(b) };waitLoaded(vm)
            val before=vm.state
            control("release")
            // Observe the real delayed HTTP callback completing; the state must remain B's.
            compose.waitUntil(20_000) { vm.viewModelScope.coroutineContext[Job]!!.children.none { it.isActive } };compose.waitForIdle()
            assertEquals(before,vm.state)
            assertEquals(original,store.loadFor(a).single { it.id==original.id })
            assertTrue(store.loadFor(b).none { it.id==original.id })
            control("arm")
        }
    }
}
