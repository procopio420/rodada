package com.rodada.attendance.operations

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.viewModelScope
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.*
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import kotlinx.coroutines.Job
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Actual ViewModel, encrypted session store and committed PostgreSQL service requests. */
class LiveServiceRequestSessionFenceTest {
    @get:Rule val compose = createComposeRule()
    private val args get() = InstrumentationRegistry.getArguments()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val upstream = "http://10.0.2.2:18134/"
    private fun login(operator: String, pin: String) = AuthHttpClient(upstream).login(LoginRequest(
        args.getString("venue")!!, operator, pin, "session-fence-${UUID.randomUUID()}"))
    private fun control(action: String, payload: JSONObject = JSONObject()): JSONObject {
        val connection = URL("http://10.0.2.2:18137/__session_fence/$action").openConnection() as HttpURLConnection
        connection.requestMethod = "POST"; connection.doOutput = true
        connection.connectTimeout = 5000; connection.readTimeout = 5000
        connection.outputStream.use { it.write(payload.toString().toByteArray()) }
        return try { JSONObject(connection.inputStream.bufferedReader().readText()) } finally { connection.disconnect() }
    }
    private fun loaded(vm: OperationsViewModel) = compose.waitUntil(30_000) {
        !vm.state.loading && vm.state.lastSyncedAtMillis != null && vm.state.serviceRequestsFresh
    }

    @Test fun committedLateServiceCallbacksCannotReplaceCurrentSessionTaskOrBusyState() {
        assumeTrue(args.getString("liveServiceSessionFence") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:18137/")
        val pairs = JSONArray(args.getString("serviceTaskPairs")!!)
        assertEquals(4, pairs.length())
        var index = 0
        for (returnToA in listOf(false,true)) for (failure in listOf(false,true)) {
            val pair = pairs.getJSONObject(index++)
            val x = pair.getString("x"); val y = pair.getString("y")
            val a = login(args.getString("operator")!!,args.getString("testPin")!!)
            val sessions = SecureSessionStore(context); sessions.save(a)
            val store = PendingMutationIntentStore(context)
            val auth = AuthRepository(context)
            val vm = OperationsViewModel(OperationsRepository(auth),store,auth,CorrectionsRepository(auth),RefundsRepository(auth))
            compose.runOnUiThread { vm.ensureLoaded(a) }; loaded(vm)
            val originalRecords = store.loadFor(a)
            control("arm",JSONObject().put("x",x).put("y",y).put("mode",if(failure) "failure" else "success"))
            compose.runOnUiThread { vm.updateServiceRequest(a,x,false) }
            compose.waitUntil(20_000) { control("status").getBoolean("heldX") }
            val oldJob = vm.viewModelScope.coroutineContext[Job]!!.children.single { it.isActive }
            val b = login(args.getString("operatorB")!!,args.getString("testPinB")!!)
            assertNotEquals(a.staffId,b.staffId)
            sessions.save(b); compose.runOnUiThread { vm.ensureLoaded(b) }; loaded(vm)
            val current = if(returnToA) {
                sessions.save(a); compose.runOnUiThread { vm.ensureLoaded(a) }; loaded(vm); a
            } else b
            compose.runOnUiThread { vm.updateServiceRequest(current,y,false) }
            compose.waitUntil(20_000) { control("status").getBoolean("heldY") }
            val before = vm.state
            assertTrue(before.submitting); assertNull(before.pendingServiceAction)
            control("releaseX")
            compose.waitUntil(20_000) { !oldJob.isActive }; compose.waitForIdle()
            assertEquals(before,vm.state)
            assertEquals(originalRecords,store.loadFor(a))
            assertEquals(listOf(x,y),control("status").getJSONArray("posts").let { List(it.length()) { n -> it.getString(n) } })
            control("releaseY")
            compose.waitUntil(30_000) { !vm.state.submitting }
            assertNull(vm.state.pendingServiceAction); assertNull(vm.state.errorMessage)
            assertEquals("Chamada assumida.",vm.state.noticeMessage)
            val api = OperationsHttpClient(upstream)
            val canonicalX = api.request("GET","/dispatch/tasks/$x/",accessToken=a.tokens.accessToken)
            val canonicalY = api.request("GET","/dispatch/tasks/$y/",accessToken=current.tokens.accessToken)
            assertEquals(a.staffId,canonicalX.getString("claimed_by_id"))
            assertEquals(current.staffId,canonicalY.getString("claimed_by_id"))
            assertEquals(originalRecords,store.loadFor(a))
            control("arm")
        }
    }
}
