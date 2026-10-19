package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class PaymentPreparationPolicyTest {
    private val tab = TabSummary("tab", "Visita", "OPEN", 1, 2400, 0, 2400)
    private val draft = listOf(CartLine(Product("p", "Água", 500, true, "BAR", "AVAILABLE"), 1))
    private val order = RecoveryIntent.ConfirmOrder("order", "staff", "venue", "device", "original-order-key", 1,
        RecoveryState.CHECKING, "tab", listOf(PendingOrderLine("p", 1)))

    @Test fun fullSettlementRequiresCurrentOrderToBeResolvedButPartialDoesNot() {
        for (state in listOf(OperationsUiState(cart = draft), OperationsUiState(orderIntentId = "unknown"),
            OperationsUiState(queuedOrders = listOf(order)))) {
            assertTrue(state.blocksNewFullPayment(tab, 2400))
            assertFalse(state.blocksNewFullPayment(tab, 1200))
        }
        assertFalse(OperationsUiState().blocksNewFullPayment(tab, 2400))
        assertFalse(OperationsUiState(queuedOrders = listOf(order.copy(tabId = "other"))).blocksNewFullPayment(tab, 2400))
    }

    @Test fun originalPaymentRecoveryRemainsAvailableWithRestoredDraft() {
        val intent = RecoveryIntent.StartPayment("payment", "staff", "venue", "device", "original-payment-key", 1,
            RecoveryState.CHECKING, "tab", 2400, PaymentMethod.CASH, "cash", 1, true)
        val state = OperationsUiState(cart = draft, orderIntentId = "unknown", queuedOrders = listOf(order), pendingPayment = intent)
        assertFalse(state.blocksNewFullPayment(tab, intent.amountCents))
        assertSame(intent, state.pendingPayment)
        assertEquals("original-payment-key", state.pendingPayment!!.idempotencyKey)
    }
}
