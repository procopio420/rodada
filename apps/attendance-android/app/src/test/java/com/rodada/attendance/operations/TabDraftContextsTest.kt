package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class TabDraftContextsTest {
    private val product = Product("product", "Produto", 700, true, "BAR", "AVAILABLE")

    @Test fun switchingTabsPreservesOriginalLineIdentityAndCustomization() {
        val drafts = TabDraftContexts()
        drafts.enterSession("session-a")
        val a = listOf(CartLine(product, 2, Customization(note = "Sem gelo"), "line-a"))
        val b = listOf(CartLine(product, 1, Customization(note = "Com gelo"), "line-b"))
        drafts.save("tab-a", a)
        drafts.save("tab-b", b)
        assertEquals(a, drafts.read("tab-a"))
        assertEquals(b, drafts.read("tab-b"))
        drafts.enterSession("session-a")
        assertEquals(a, drafts.read("tab-a"))
        drafts.save("tab-a", emptyList())
        assertTrue(drafts.read("tab-a").isEmpty())
        assertEquals(b, drafts.read("tab-b"))
    }

    @Test fun newSessionNeverAdoptsDraftsEvenForTheSameTab() {
        val drafts = TabDraftContexts()
        drafts.enterSession("session-a")
        drafts.save("tab", listOf(CartLine(product, 2)))
        drafts.enterSession("session-b")
        assertTrue(drafts.read("tab").isEmpty())
        drafts.enterSession("session-a")
        assertTrue(drafts.read("tab").isEmpty())
    }

    @Test fun onlyUnsubmittedDraftCanLeaveContext() {
        val state = OperationsUiState(cart = listOf(CartLine(product, 2)))
        assertTrue(state.canLeaveTabContext())
        assertFalse(state.copy(loading = true).canLeaveTabContext())
        assertFalse(state.copy(submitting = true).canLeaveTabContext())
        assertFalse(state.copy(orderIntentId = "original-order-key").canLeaveTabContext())
        assertFalse(state.copy(paymentIntentId = "original-payment-key").canLeaveTabContext())
        assertTrue(state.copy(contextRecoveryPending = true).canLeaveTabContext())
        assertTrue(state.copy(recoveryEvidence = listOf(RecoveryEvidence("cash", "Caixa", 1, false))).canLeaveTabContext())
    }

    @Test fun unrelatedExceptionalRecoveryDoesNotTrapAnOpenTab() {
        val tab = TabDetail(TabSummary("tab-b", "Comanda B", "OPEN", 1, 0, 0, 0), emptyList())
        val state = OperationsUiState(selectedTab = tab, recoveryEvidence = listOf(
            RecoveryEvidence("correction-a", "Correção", 1, false, needsExceptionalContext = true)))
        assertTrue(state.canLeaveTabContext())
        assertTrue(state.copy(recoveryEvidence = listOf(RecoveryEvidence("payment-b", "Recebimento", 1, false, tabId = "tab-b"))).canLeaveWithRecords(emptyList()))
    }

    @Test fun reconciledLocalRecordUnblocksWithoutWaitingForRealtime() {
        val tab = TabDetail(TabSummary("tab", "Comanda", "OPEN", 1, 0, 0, 0), emptyList())
        val state = OperationsUiState(selectedTab = tab, contextRecoveryPending = true,
            recoveryEvidence = listOf(RecoveryEvidence("original", "Ajuste", 1, false, tabId = "tab")))
        val record = RecoveryIntent.Pricing("original", "staff", "venue", "device", "original-key", 1, RecoveryState.CHECKING, "tab", "{}")
        assertFalse(state.canLeaveWithRecords(listOf(record)))
        assertTrue(state.canLeaveWithRecords(emptyList()))
    }
}
