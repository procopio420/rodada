package com.rodada.attendance.operations

import kotlinx.coroutines.CancellationException

/** Invalidates delayed financial responses even after an A → B → A session switch. */
internal class FinancialResponseFence {
    private var generation = 0L
    fun invalidate() { generation++ }

    fun capture(current: () -> Boolean, checkpoint: (RecoveryIntent.StartPayment) -> Unit = {}): Guard {
        val originalGeneration = generation
        return Guard({ generation == originalGeneration && current() }, checkpoint)
    }

    class Guard internal constructor(private val current: () -> Boolean,
        private val update: (RecoveryIntent.StartPayment) -> Unit) {
        fun isCurrent(): Boolean = current()
        fun check() { if (!isCurrent()) throw CancellationException("A sessão ou intenção financeira original mudou.") }
        fun checkpoint(intent: RecoveryIntent.StartPayment) { update(intent) }
    }
}
