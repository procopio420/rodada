package com.rodada.attendance.operations

/** Closing, retrying or selecting invalidates every earlier history response. */
internal class LatestHistoryRead {
    private var generation = 0L
    fun start(): Long = ++generation
    fun isCurrent(read: Long): Boolean = read == generation
}
