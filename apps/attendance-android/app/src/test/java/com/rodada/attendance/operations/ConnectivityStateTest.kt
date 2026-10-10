package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Test

class ConnectivityStateTest {
    @Test fun apiOfflineSurvivesRealtimeReconnectRegardlessOfFreshness() {
        for (lastRead in listOf(null, 99_999L, 1L)) {
            assertEquals(ConnectivityState.OFFLINE, ConnectivityState.OFFLINE.onRealtimeReconnect(lastRead, 100_000L))
        }
    }

    @Test fun otherStatesKeepTheCanonicalThirtySecondFreshnessBoundary() {
        for (state in ConnectivityState.entries.filter { it != ConnectivityState.OFFLINE }) {
            assertEquals(ConnectivityState.RECONNECTING, state.onRealtimeReconnect(null, 100_000L))
            assertEquals(ConnectivityState.RECONNECTING, state.onRealtimeReconnect(70_001L, 100_000L))
            assertEquals(ConnectivityState.STALE, state.onRealtimeReconnect(70_000L, 100_000L))
            assertEquals(ConnectivityState.STALE, state.onRealtimeReconnect(1L, 100_000L))
        }
    }
}
