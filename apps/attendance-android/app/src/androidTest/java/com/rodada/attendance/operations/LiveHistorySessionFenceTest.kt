package com.rodada.attendance.operations

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.lifecycle.viewModelScope
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.*
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import kotlinx.coroutines.Job
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class LiveHistorySessionFenceTest {
    @get:Rule val compose = createComposeRule()
    private val args get() = InstrumentationRegistry.getArguments()
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val upstream = "http://10.0.2.2:18134/"
    private fun login(operator: String,pin: String) = AuthHttpClient(upstream).login(LoginRequest(
        args.getString("venue")!!,operator,pin,"history-fence-${UUID.randomUUID()}"))
    private fun control(action: String,mode: String="success"): JSONObject {
        val connection=URL("http://10.0.2.2:18140/__history_fence/$action").openConnection() as HttpURLConnection
        connection.requestMethod="POST";connection.doOutput=true;connection.connectTimeout=5000;connection.readTimeout=5000
        connection.outputStream.use { it.write(JSONObject().put("mode",mode).toString().toByteArray()) }
        return try { JSONObject(connection.inputStream.bufferedReader().readText()) } finally { connection.disconnect() }
    }
    private fun loaded(vm: OperationsViewModel,pending: Job?=null)=compose.waitUntil(30_000) {
        !vm.state.loading && vm.state.lastSyncedAtMillis != null &&
            vm.viewModelScope.coroutineContext[Job]!!.children.none { it.isActive && it !== pending }
    }
    @Test fun lateHistorySuccessAndFailureCannotFinishNewHistoryAcrossSessionGenerations() {
        assumeTrue(args.getString("liveHistorySessionFence")=="true")
        check(BuildConfig.RODADA_API_BASE_URL=="http://10.0.2.2:18140/")
        for(returnToA in listOf(false,true)) for(failure in listOf(false,true)) {
            val a=login(args.getString("operator")!!,args.getString("testPin")!!)
            val sessions=SecureSessionStore(context);sessions.save(a)
            val auth=AuthRepository(context)
            val vm=OperationsViewModel(OperationsRepository(auth),PendingMutationIntentStore(context),auth,CorrectionsRepository(auth),RefundsRepository(auth))
            compose.runOnUiThread { vm.ensureLoaded(a) };loaded(vm)
            control("arm",if(failure) "failure" else "success")
            lateinit var oldJob: Job
            compose.runOnUiThread {
                val existing=vm.viewModelScope.coroutineContext[Job]!!.children.toSet()
                vm.loadTabHistory(a)
                oldJob=vm.viewModelScope.coroutineContext[Job]!!.children.single { it !in existing }
            }
            compose.waitUntil(20_000) { control("status").getBoolean("heldOld") }
            val b=login(args.getString("operatorB")!!,args.getString("testPinB")!!)
            sessions.save(b);compose.runOnUiThread { vm.ensureLoaded(b) };loaded(vm,oldJob)
            val beforeForeignCall=vm.state
            compose.runOnUiThread {
                vm.loadTabHistory(a)
                vm.inspectHistory(a, "foreign-session-must-not-read")
            }
            compose.waitForIdle()
            assertEquals(beforeForeignCall,vm.state)
            assertEquals(1,control("status").getInt("historyReads"))
            val current=if(returnToA) { sessions.save(a);compose.runOnUiThread { vm.ensureLoaded(a) };loaded(vm,oldJob);a } else b
            control("captureCurrent")
            compose.runOnUiThread { vm.loadTabHistory(current) }
            compose.waitUntil(20_000) { control("status").getBoolean("heldCurrent") }
            val before=vm.state;assertTrue(before.historyLoading)
            control("releaseOld");compose.waitUntil(20_000) { !oldJob.isActive };compose.waitForIdle()
            assertEquals(before,vm.state)
            control("releaseCurrent")
            compose.waitUntil(30_000) { !vm.state.historyLoading }
            assertTrue(vm.state.historyLoaded);assertNull(vm.state.historyError)
            val expected=OperationsHttpClient(upstream).tabs(current.tokens.accessToken,true).filter { it.state in setOf("CLOSED","CANCELLED") }
            assertEquals(expected,vm.state.historyTabs)
            assertEquals(2,control("status").getInt("historyReads"))
        }
    }
}
