package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class LatestHistoryReadTest {
    @Test fun sameTabRetryAndReturnRejectOutOfOrderResults() {
        val reads = LatestHistoryRead()
        val firstA = reads.start()
        reads.start() // Back to list invalidates A.
        val secondA = reads.start()
        assertTrue(reads.isCurrent(secondA))
        assertFalse(reads.isCurrent(firstA)) // Late success or failure must be ignored.
        val retryA = reads.start()
        assertTrue(reads.isCurrent(retryA))
        assertFalse(reads.isCurrent(secondA))
        reads.start() // Dismiss the dialog.
        assertFalse(reads.isCurrent(retryA))
    }
}
