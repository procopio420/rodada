package com.rodada.attendance.operations

import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.refunds.RefundsRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test

/** Opt-in read-only integration: uses an existing local test session, never creates orders. */
class NativeDraftReadbackTest {
    @Test fun realCanonicalReadsPreserveDraftsAcrossAtoBtoAWithoutSendingOrders() = runBlocking {
        assumeTrue(InstrumentationRegistry.getArguments().getString("readOnlyLocal") == "true")
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val auth = AuthRepository(context)
        val session = auth.restoreSession()
        assumeTrue("An existing authenticated local test session is required", session != null)
        val originalSession = session!!
        val store = PendingMutationIntentStore(context)
        assumeTrue("Do not touch an environment with pending operations", store.loadFor(originalSession).isEmpty())
        val repository = OperationsRepository(auth)
        val tabs = repository.tabs(originalSession).filter { it.state == "OPEN" }
        assumeTrue("Two existing open test Tabs are required", tabs.size >= 2)
        val product = repository.products(originalSession).firstOrNull {
            it.active && it.availability == "AVAILABLE" && it.variants.isEmpty() && it.modifierGroups.isEmpty()
        }
        assumeTrue("An available simple product is required", product != null)
        val before = tabs.take(2).associate { it.id to repository.tabDetail(originalSession, it.id).orders }
        val model = OperationsViewModel(repository, store, auth, CorrectionsRepository(auth), RefundsRepository(auth))
        suspend fun select(id: String) {
            withContext(Dispatchers.Main) { model.selectTab(originalSession, id) }
            repeat(100) {
                if (withContext(Dispatchers.Main) { !model.state.submitting }) return
                delay(100)
            }
            fail("Canonical selection timed out")
        }
        select(tabs[0].id)
        withContext(Dispatchers.Main) { model.addProduct(product!!, Customization(note = "Sem gelo")) }
        val a = withContext(Dispatchers.Main) { model.state.cart.toList() }
        assertEquals(1, a.size)
        withContext(Dispatchers.Main) { model.clearSelection(originalSession) }
        select(tabs[1].id)
        assertTrue(model.state.cart.isEmpty())
        withContext(Dispatchers.Main) { model.addProduct(product!!, Customization(note = "Com gelo")) }
        val b = withContext(Dispatchers.Main) { model.state.cart.toList() }
        withContext(Dispatchers.Main) { model.clearSelection(originalSession) }
        select(tabs[0].id)
        assertEquals(a, model.state.cart)
        withContext(Dispatchers.Main) { model.clearSelection(originalSession) }
        select(tabs[1].id)
        assertEquals(b, model.state.cart)
        assertTrue(store.loadFor(originalSession).isEmpty())
        for ((id, orders) in before) assertEquals(orders, repository.tabDetail(originalSession, id).orders)
    }
}
