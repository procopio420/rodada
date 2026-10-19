package com.rodada.attendance.operations

/** Full settlement can close the Tab on the server even without a local Close request. */
fun OperationsUiState.blocksNewFullPayment(tab: TabSummary, amountCents: Long): Boolean =
    pendingPayment == null && amountCents == tab.exposureCents &&
        (cart.isNotEmpty() || orderIntentId != null || queuedOrders.any { it.tabId == tab.id })
