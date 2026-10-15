package com.rodada.attendance.operations

/** Unsubmitted work only. Submitted intents remain in the encrypted recovery store. */
internal class TabDraftContexts {
    private var scope: String? = null
    private val drafts = mutableMapOf<String, List<CartLine>>()

    fun enterSession(sessionKey: String) {
        if (scope != sessionKey) { drafts.clear(); scope = sessionKey }
    }

    fun save(tabId: String, lines: List<CartLine>) {
        if (lines.isEmpty()) drafts.remove(tabId) else drafts[tabId] = lines.toList()
    }

    fun read(tabId: String): List<CartLine> = drafts[tabId].orEmpty().toList()
}

/** Navigation cannot detach a submitted or ambiguous operation from its original target. */
internal fun OperationsUiState.canLeaveTabContext(): Boolean =
    !loading && !submitting && orderIntentId == null && paymentIntentId == null &&
        pendingPayment == null && pendingTableService == null && pendingTabOperation == null &&
        integratedPayment?.blocksNewCharge != true &&
        queuedOrders.none { it.tabId == selectedTab?.summary?.id }

/** Cached badges do not authorize or permanently block navigation after reconciliation. */
internal fun OperationsUiState.canLeaveWithRecords(records: List<RecoveryIntent>): Boolean =
    canLeaveTabContext() && (selectedTab == null || records.none { it.targetsContext(selectedTab) })

internal fun RecoveryIntent.targetsContext(tab: TabDetail): Boolean = when (this) {
    is RecoveryIntent.Correction -> tab.orders.any { order -> order.items.any { it.id == orderItemId } }
    is RecoveryIntent.Refund -> tab.payments.any { it.id == paymentId } || tab.refundRequiredCorrections.any { it.id == correctionId }
    else -> evidence().tabId == tab.summary.id
}
