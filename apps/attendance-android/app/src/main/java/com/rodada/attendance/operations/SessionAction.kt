package com.rodada.attendance.operations

/** Shared action completion boundary: a stale callback cannot release another session's busy state. */
internal suspend fun runSessionAction(
    guard: FinancialResponseFence.Guard,
    block: suspend FinancialResponseFence.Guard.() -> Unit,
    onSuccess: () -> Unit,
    onFailure: (Throwable) -> Unit,
) {
    runCatching { guard.check(); guard.block(); guard.check() }
        .onSuccess { onSuccess() }
        .onFailure { if (guard.isCurrent()) onFailure(it) }
}
