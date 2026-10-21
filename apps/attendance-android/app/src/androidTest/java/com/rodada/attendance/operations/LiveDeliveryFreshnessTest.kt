package com.rodada.attendance.operations

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.flowOf
import com.rodada.attendance.realtime.OperationalRealtime
import com.rodada.attendance.realtime.RealtimeSignal
import androidx.test.platform.app.InstrumentationRegistry
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

/** Real HTTP/PG core with only queue reads failed; no mock order/ledger or SSE connection. */
class LiveDeliveryFreshnessTest {
    @get:Rule val compose = createComposeRule()
    private val args get() = InstrumentationRegistry.getArguments()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val direct = OperationsHttpClient("http://10.0.2.2:18134/")
    private fun login() = AuthHttpClient("http://10.0.2.2:18134/").login(LoginRequest(
        args.getString("venue")!!, args.getString("operator")!!, args.getString("testPin")!!, "freshness-${UUID.randomUUID()}"))
    private fun control(queue: Boolean = false, core: Boolean = false, hold: Boolean = false, action: String = "arm", service: Boolean = false): JSONObject {
        val c = URL("http://10.0.2.2:18136/__freshness/$action").openConnection() as HttpURLConnection
        c.requestMethod = "POST"; c.doOutput = true
        c.outputStream.use { it.write(JSONObject().put("queue",queue).put("core",core).put("hold",hold).put("service",service).toString().toByteArray()) }
        return try { JSONObject(c.inputStream.bufferedReader().readText()) } finally { c.disconnect() }
    }
    private fun model(): OperationsViewModel {
        val auth = AuthRepository(context)
        return OperationsViewModel(OperationsRepository(auth), PendingMutationIntentStore(context), auth,
            CorrectionsRepository(auth), RefundsRepository(auth), object : OperationalRealtime {
                override fun subscribe(session: StoredSession) = flowOf(RealtimeSignal.Connected)
            })
    }
    private fun refresh(vm: OperationsViewModel, s: StoredSession) {
        compose.runOnUiThread { vm.refresh(s) }
        compose.waitUntil(30_000) { !vm.state.loading && !vm.state.deliveryTasksLoading }
    }
    private fun requireRunner() {
        assumeTrue(args.getString("liveDeliveryFreshness") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18136/")
        check(args.getString("venue")!!.startsWith("spec033-"))
    }

    @Test fun queue503PreservesSnapshotAndRealOrderWhileCoreFailureStaysBlocked() {
        requireRunner(); control()
        val s = login(); SecureSessionStore(context).save(s)
        val token = s.tokens.accessToken
        val product = direct.products(token).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..3000 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        val tab = direct.openTab(token,"Freshness ${UUID.randomUUID()}")
        direct.confirmOrder(token,tab.id,listOf(CartLine(product,1)),UUID.randomUUID().toString())
        val item = direct.tabDetail(token,tab.id).orders.single().items.single()
        for (state in listOf("PREPARING","READY")) direct.request("POST","/order-items/${item.id}/transition/",JSONObject().put("state",state),token)
        val vm = model()
        compose.runOnUiThread { vm.ensureLoaded(s) }
        compose.waitUntil(30_000) { !vm.state.loading && !vm.state.deliveryTasksLoading }
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity) // no startRealtime: HTTP fallback
        assertTrue(vm.state.deliveryTasksFresh)
        val original = vm.state.deliveryTasks
        assertTrue(original.any { it.orderItemId == item.id })
        control(queue = true); refresh(vm,s)
        assertEquals(original,vm.state.deliveryTasks); assertFalse(vm.state.deliveryTasksFresh)
        assertNotNull(vm.state.deliveryTasksError); assertEquals("—",nowQueueCounts(vm.state)[NowQueue.READY])
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity); assertNull(vm.state.errorMessage)
        compose.runOnUiThread { vm.selectTab(s,tab.id) }
        compose.waitUntil(30_000) { !vm.state.submitting && vm.state.selectedTab?.summary?.id == tab.id }
        compose.runOnUiThread { vm.addProduct(product);vm.confirmOrder(s) }
        compose.waitUntil(30_000) { !vm.state.submitting && vm.state.queuedOrders.isEmpty() }
        val after = direct.tabDetail(token,tab.id)
        assertEquals(2,after.orders.size);assertEquals(product.priceCents*2,after.summary.chargesCents)
        assertFalse(vm.state.deliveryTasksFresh)
        control(core = true);refresh(vm,s)
        assertTrue(vm.state.deliveryTasksFresh);assertNotEquals(ConnectivityState.ONLINE,vm.state.connectivity)
        assertNotNull(vm.state.errorMessage)
        compose.runOnUiThread { vm.startRealtime(s) };compose.waitForIdle()
        assertNotEquals(ConnectivityState.ONLINE,vm.state.connectivity) // Connected signal cannot bless a failed core read
        compose.runOnUiThread { vm.releaseTable(s,TableReleaseCommand(UUID.randomUUID().toString(),UUID.randomUUID().toString(),1)) }
        compose.waitUntil(10_000) { !vm.state.submitting }
        assertTrue(vm.state.errorMessage!!.contains("Atualize as entregas"))
        control();refresh(vm,s)
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity);assertTrue(vm.state.deliveryTasksFresh)
        assertNull(vm.state.deliveryTasksError);assertEquals(vm.state.deliveryTasks.size.toString(),nowQueueCounts(vm.state)[NowQueue.READY])
    }

    @Test fun canceledRefreshAcrossABAReentryCannotPublishOldQueueFailure() {
        requireRunner();control()
        val a=login();SecureSessionStore(context).save(a);val vm=model()
        compose.runOnUiThread { vm.ensureLoaded(a) };compose.waitUntil(30_000) { !vm.state.loading && !vm.state.deliveryTasksLoading }
        control(queue=true,hold=true)
        compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(20_000) { control(action="status").getBoolean("held") }
        compose.waitUntil(20_000) { !vm.state.loading }
        assertTrue(vm.state.deliveryTasksLoading)
        assertFalse(vm.state.deliveryTasksFresh)
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity) // slow queue cannot hold core hostage
        val added = direct.openTab(a.tokens.accessToken,"Held queue core refresh ${UUID.randomUUID()}")
        compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(15_000) { !vm.state.loading && vm.state.tabs.any { it.id == added.id } }
        assertTrue(vm.state.deliveryTasksLoading)
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity)
        control(action="configure") // future reads healthy; keep original failed A response held
        val b=login();SecureSessionStore(context).save(b)
        // Switch twice before releasing the old A HTTP response: identity equality alone is insufficient.
        compose.runOnUiThread { vm.ensureLoaded(b) }
        SecureSessionStore(context).save(a)
        compose.runOnUiThread { vm.ensureLoaded(a) }
        control(action="release")
        compose.waitUntil(30_000) { !vm.state.loading && !vm.state.deliveryTasksLoading && vm.state.deliveryTasksFresh }
        compose.waitUntil(30_000) { vm.viewModelScope.coroutineContext[Job]!!.children.none { it.isActive } }
        assertEquals(ConnectivityState.ONLINE,vm.state.connectivity)
        assertNull(vm.state.deliveryTasksError);assertNull(vm.state.errorMessage)
    }
    @Test fun heldServiceQueueDoesNotBlockCoreOrdersOrPublishAcrossABA() {
        requireRunner(); control()
        val a = login(); SecureSessionStore(context).save(a); val vm = model()
        compose.runOnUiThread { vm.ensureLoaded(a) }
        compose.waitUntil(30_000) { !vm.state.loading && vm.state.serviceRequestsFresh }
        val original = vm.state.serviceRequests
        val product = direct.products(a.tokens.accessToken).first { it.active && it.availability == "AVAILABLE" && it.priceCents in 1..1500 && it.variants.isEmpty() && it.modifierGroups.isEmpty() }
        val tab = direct.openTab(a.tokens.accessToken, "Slow service ${UUID.randomUUID()}")
        control(queue = true, hold = true, service = true)
        compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(20_000) { control(action = "status").getBoolean("held") }
        compose.waitUntil(10_000) { !vm.state.loading && vm.state.tabs.any { it.id == tab.id } }
        assertEquals(ConnectivityState.ONLINE, vm.state.connectivity)
        assertFalse(vm.state.serviceRequestsFresh)
        assertEquals(original, vm.state.serviceRequests)
        compose.runOnUiThread { vm.selectTab(a, tab.id) }
        compose.waitUntil(15_000) { !vm.state.submitting && vm.state.selectedTab?.summary?.id == tab.id }
        compose.runOnUiThread { vm.addProduct(product); vm.confirmOrder(a) }
        compose.waitUntil(15_000) { !vm.state.submitting && vm.state.queuedOrders.isEmpty() }
        val after = direct.tabDetail(a.tokens.accessToken, tab.id)
        assertEquals(1, after.orders.size)
        assertEquals(product.priceCents, after.summary.chargesCents)
        val added = direct.openTab(a.tokens.accessToken, "Second core refresh ${UUID.randomUUID()}")
        compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(10_000) { !vm.state.loading && vm.state.tabs.any { it.id == added.id } }
        assertFalse(vm.state.serviceRequestsFresh)
        control(service = true, action = "configure")
        val b = login(); SecureSessionStore(context).save(b)
        compose.runOnUiThread { vm.ensureLoaded(b) }
        SecureSessionStore(context).save(a)
        compose.runOnUiThread { vm.ensureLoaded(a) }
        control(action = "release")
        compose.waitUntil(30_000) { !vm.state.loading && vm.state.serviceRequestsFresh }
        compose.waitUntil(30_000) { vm.viewModelScope.coroutineContext[Job]!!.children.none { it.isActive } }
        assertNull(vm.state.serviceRequestsError)
        assertNull(vm.state.errorMessage)
        assertEquals(ConnectivityState.ONLINE, vm.state.connectivity)
        control(queue = true, service = true)
        compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(15_000) { !vm.state.loading && vm.state.serviceRequestsError != null }
        assertFalse(vm.state.serviceRequestsFresh)
        assertEquals(ConnectivityState.ONLINE, vm.state.connectivity)
        compose.runOnUiThread { vm.updateServiceRequest(a, UUID.randomUUID().toString(), false) }
        compose.waitUntil(10_000) { !vm.state.submitting }
        assertTrue(vm.state.errorMessage!!.contains("Atualize as chamadas"))
        control(); compose.runOnUiThread { vm.refresh(a) }
        compose.waitUntil(15_000) { !vm.state.loading && vm.state.serviceRequestsFresh }
        assertNull(vm.state.serviceRequestsError)
    }

}
