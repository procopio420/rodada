package com.rodada.attendance.operations

import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.corrections.*
import com.rodada.attendance.refunds.*
import kotlinx.coroutines.*
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.util.UUID

class ExceptionalRecoveryApiTest {
    @Test fun originalCancelledItemRefundAndAppliedSettlementOpenClosedTabWithoutReplaying() = runBlocking {
        assumeTrue(InstrumentationRegistry.getArguments().getString("realRecovery") == "true" && BuildConfig.RODADA_API_BASE_URL.contains(":8126/"))
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        context.getSharedPreferences("rodada_pending_mutation_intents", 0).edit().clear().commit()
        val auth = AuthRepository(context)
        val session = auth.login("web-e2e", "test-manager", "2468")
        val repository = OperationsRepository(auth)
        val corrections = CorrectionsRepository(auth)
        val refunds = RefundsRepository(auth)
        val tab = repository.openTab(session, "Exception recovery fixture", null)
        val product = repository.products(session).first()
        repository.confirmOrder(session, tab.id, listOf(CartLine(product, 1)), UUID.randomUUID().toString())
        val item = repository.tabDetail(session, tab.id).orders.single().items.single()
        val payment = repository.collectPayment(session, tab.id, product.priceCents, PaymentMethod.EXTERNAL_TERMINAL, UUID.randomUUID().toString(), null)
        val correctionKey = UUID.randomUUID().toString()
        val correction = corrections.submit(session, CorrectionCommand(item.id, item.state, CorrectionAction.CANCEL, "WRONG_ENTRY", "Original fixture reason", correctionKey))
        assertEquals("REQUESTED", correction.status)
        auth.reauthenticate(session, "2468")
        val settlementKey = UUID.randomUUID().toString()
        refunds.create(session, SettleCorrectionRefundCommand(correction.id, payment.id, product.priceCents, settlementKey))
        repository.closeTab(session, tab.id)
        val before = repository.tabDetail(session, tab.id)
        assertEquals("CLOSED", before.summary.state)
        assertTrue(before.refundRequiredCorrections.isEmpty())
        val store = PendingMutationIntentStore(context)
        val correctionRecord = RecoveryIntent.Correction("correction-original", session.staffId, session.venueId, session.deviceId,
            correctionKey, 42, RecoveryState.CHECKING, item.id, item.state, CorrectionRecoveryAction.CANCEL, "WRONG_ENTRY", "Original fixture reason", null)
        val directRecord = RecoveryIntent.Refund("refund-original", session.staffId, session.venueId, session.deviceId,
            "direct-original-key", 43, RecoveryState.CHECKING, RefundRecoveryKind.DIRECT, payment.id, null, product.priceCents, "Original refund reason", null)
        val settlementRecord = directRecord.copy(id = "settlement-original", idempotencyKey = settlementKey,
            kind = RefundRecoveryKind.SETTLE_CORRECTION, correctionId = correction.id, reason = null)
        val records = listOf(correctionRecord, directRecord, settlementRecord)
        records.forEach { store.save(it, session) }
        val model = OperationsViewModel(repository, store, auth, corrections, refunds)
        records.forEach { original ->
            withContext(Dispatchers.Main) { model.openRecovery(session, original.id) }
            awaitRead(model)
            assertNull(model.state.errorMessage)
            val read = requireNotNull(model.state.exceptionalRecoveryContext)
            assertEquals(original, read.original)
            assertEquals(before, read.detail)
            assertNull(model.state.selectedTab)
            assertTrue(model.state.cart.isEmpty())
            if (original == settlementRecord) assertEquals("APPLIED", read.target.correctionStatus)
            assertEquals(records, store.loadFor(session))
            assertEquals(before, repository.tabDetail(session, tab.id))
            withContext(Dispatchers.Main) { model.clearExceptionalRecoveryContext() }
        }
        val missing = correctionRecord.copy(id = "missing-target", orderItemId = UUID.randomUUID().toString())
        store.save(missing, session)
        withContext(Dispatchers.Main) { model.openRecovery(session, missing.id) }
        awaitRead(model)
        assertNull(model.state.exceptionalRecoveryContext)
        assertNotNull(model.state.errorMessage)
        assertTrue(store.loadFor(session).contains(missing))
        store.remove(missing.id)
        withContext(Dispatchers.Main) { model.openRecovery(session, settlementRecord.id) }
        awaitRead(model)
        assertNotNull(model.state.exceptionalRecoveryContext)
        val next = auth.login("web-e2e", "test-manager", "2468")
        withContext(Dispatchers.Main) { model.openRecovery(next, settlementRecord.id) }
        awaitRead(model)
        assertNull(model.state.exceptionalRecoveryContext)
        assertNotNull(model.state.errorMessage)
        assertEquals(records, store.blockedFor(next))
        assertEquals(before, repository.tabDetail(next, tab.id))
        records.forEach { store.remove(it.id) }
    }

    private suspend fun awaitRead(model: OperationsViewModel) {
        repeat(100) { if (withContext(Dispatchers.Main) { !model.state.submitting }) return; delay(100) }
        fail("Exceptional context read did not finish")
    }
}
