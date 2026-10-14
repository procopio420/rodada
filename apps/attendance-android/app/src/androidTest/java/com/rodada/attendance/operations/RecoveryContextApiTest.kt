package com.rodada.attendance.operations

import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test

class RecoveryContextApiTest {
    @Test fun originalOrderOpensByCanonicalIdAndNewSessionCannotAdoptIt() = runBlocking {
        assumeTrue("Requires isolated test API on 8126 and explicit instrumentation opt-in",
            InstrumentationRegistry.getArguments().getString("realRecovery") == "true" && BuildConfig.RODADA_API_BASE_URL.contains(":8126/"))
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        context.getSharedPreferences("rodada_pending_mutation_intents", 0).edit().clear().commit()
        val auth = AuthRepository(context)
        val session = auth.login("web-e2e", "test-manager", "2468")
        val repository = OperationsRepository(auth)
        val tab = repository.openTab(session, "Recovery context test", null)
        val store = PendingMutationIntentStore(context)
        val original = RecoveryIntent.ConfirmOrder("context-original", session.staffId, session.venueId, session.deviceId,
            "context-original-key", 42, RecoveryState.ACTION_REQUIRED, tab.id, listOf(PendingOrderLine("original-product-id", 2, Customization(note = "Original note"))))
        store.save(original, session)
        val model = OperationsViewModel(repository, store, auth, CorrectionsRepository(auth), RefundsRepository(auth))
        withContext(Dispatchers.Main) { model.openRecovery(session, original.id) }
        awaitIdle(model)
        assertNull(model.state.errorMessage)
        assertEquals(tab.id, model.state.selectedTab?.summary?.id)
        assertEquals(original.idempotencyKey, model.state.orderIntentId)
        assertEquals(original, store.loadFor(session).single())
        assertTrue(repository.tabDetail(session, tab.id).orders.isEmpty())
        withContext(Dispatchers.Main) { model.clearSelection() }
        val next = auth.login("web-e2e", "test-manager", "2468")
        assertNotEquals(session.sessionId, next.sessionId)
        withContext(Dispatchers.Main) { model.openRecovery(next, original.id) }
        awaitIdle(model)
        assertNull(model.state.selectedTab)
        assertTrue(model.state.errorMessage!!.contains("sessão original"))
        assertEquals(original, store.blockedFor(next).single())
        assertTrue(repository.tabDetail(next, tab.id).orders.isEmpty())
        store.remove(original.id)
    }

    private suspend fun awaitIdle(model: OperationsViewModel) {
        repeat(100) {
            if (withContext(Dispatchers.Main) { !model.state.submitting }) return
            kotlinx.coroutines.delay(100)
        }
        fail("Recovery context did not finish its canonical read")
    }
}
