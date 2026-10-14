package com.rodada.attendance.cash

import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.operations.*
import kotlinx.coroutines.*
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.util.UUID

class CashRecoveryApiTest {
    @Test fun closedOriginalShiftIsReadWithoutReplacingCurrentShiftOrSubmitting() = runBlocking {
        assumeTrue(InstrumentationRegistry.getArguments().getString("realRecovery") == "true" && BuildConfig.RODADA_API_BASE_URL.contains(":8126/"))
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        context.getSharedPreferences("rodada_pending_mutation_intents", 0).edit().clear().commit()
        val auth = AuthRepository(context)
        val session = auth.login("web-e2e", "test-manager", "2468")
        val gateway = CashRepository(auth)
        val point = gateway.cashPoints(session).single()
        point.activeShift?.let { previous ->
            val counting = if (previous.status == "COUNTING") previous else gateway.startCount(session, previous.id)
            gateway.close(session, previous.id, CloseCashShiftCommand(0, 0, counting.version))
        }
        val originalShift = gateway.openShift(session, OpenCashShiftCommand(point.id, 0, "2026-10-12", UUID.randomUUID().toString()))
        val counting = gateway.startCount(session, originalShift.id)
        gateway.close(session, originalShift.id, CloseCashShiftCommand(0, 0, counting.version))
        val currentShift = gateway.openShift(session, OpenCashShiftCommand(point.id, 0, "2026-10-13", UUID.randomUUID().toString()))
        val originalDetail = gateway.shiftDetail(session, originalShift.id)
        val currentDetail = gateway.shiftDetail(session, currentShift.id)
        val store = PendingMutationIntentStore(context)
        val movement = RecoveryIntent.CashMovement("cash-original", session.staffId, session.venueId, session.deviceId,
            "cash-original-key", 42, RecoveryState.CHECKING, originalShift.id, CashMovementRecoveryKind.WITHDRAWAL, 1234, "Original reason", false, null)
        val close = RecoveryIntent.CashClose("close-original", session.staffId, session.venueId, session.deviceId,
            "close-original-key", 42, RecoveryState.CHECKING, originalShift.id, 0, 0, counting.version)
        val model = CashShiftViewModel(gateway, auth, store)
        withContext(Dispatchers.Main) { model.refresh(session) }
        awaitRead { !model.state.loading }
        val operationalBefore = model.state
        assertEquals(currentShift.id, operationalBefore.activeShift?.id)
        store.save(movement, session); store.save(close, session)
        listOf(movement, close).forEach { record ->
            withContext(Dispatchers.Main) { model.openRecovery(session, record.id) }
            awaitRead { !model.recoveryContext.loading }
            assertNull(model.recoveryContext.errorMessage)
            assertEquals(record, model.recoveryContext.original)
            assertEquals(originalDetail, model.recoveryContext.detail)
            assertEquals("CLOSED", model.recoveryContext.detail?.shift?.status)
            assertEquals(operationalBefore, model.state)
            assertEquals(listOf(movement, close), store.loadFor(session))
        }
        withContext(Dispatchers.Main) { model.clearRecoveryContext() }
        assertEquals(operationalBefore, model.state)
        assertNull(model.recoveryContext.intentId)

        val wrongGateway = object : CashGateway by gateway {
            override suspend fun shiftDetail(session: StoredSession, shiftId: String) = currentDetail
        }
        val wrongModel = CashShiftViewModel(wrongGateway, auth, store)
        withContext(Dispatchers.Main) { wrongModel.openRecovery(session, movement.id) }
        awaitRead { !wrongModel.recoveryContext.loading }
        assertNull(wrongModel.recoveryContext.detail)
        assertNotNull(wrongModel.recoveryContext.errorMessage)

        val missing = movement.copy(id = "cash-missing", shiftId = UUID.randomUUID().toString())
        store.save(missing, session)
        withContext(Dispatchers.Main) { model.openRecovery(session, missing.id) }
        awaitRead { !model.recoveryContext.loading }
        assertNull(model.recoveryContext.detail)
        assertNotNull(model.recoveryContext.errorMessage)
        assertTrue(store.loadFor(session).contains(missing))
        store.remove(missing.id)

        val delayedGateway = object : CashGateway by gateway {
            override suspend fun shiftDetail(session: StoredSession, shiftId: String): CashShiftDetail {
                val detail = gateway.shiftDetail(session, shiftId)
                auth.login("web-e2e", "test-manager", "2468")
                return detail
            }
        }
        val delayedModel = CashShiftViewModel(delayedGateway, auth, store)
        withContext(Dispatchers.Main) { delayedModel.openRecovery(session, movement.id) }
        awaitRead { !delayedModel.recoveryContext.loading }
        assertNull(delayedModel.recoveryContext.detail)
        assertNotNull(delayedModel.recoveryContext.errorMessage)
        val next = auth.login("web-e2e", "test-manager", "2468")
        withContext(Dispatchers.Main) { model.openRecovery(next, close.id) }
        awaitRead { !model.recoveryContext.loading }
        assertNull(model.recoveryContext.detail)
        assertNotNull(model.recoveryContext.errorMessage)
        assertEquals(listOf(movement, close), store.blockedFor(next))
        assertEquals(originalDetail, gateway.shiftDetail(next, originalShift.id))
        assertEquals(currentDetail, gateway.shiftDetail(next, currentShift.id))
        store.remove(movement.id); store.remove(close.id)
    }

    private suspend fun awaitRead(done: () -> Boolean) {
        repeat(100) { if (withContext(Dispatchers.Main) { done() }) return; delay(100) }
        fail("Cash context read did not finish")
    }
}
