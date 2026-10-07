package com.rodada.attendance.auth

import org.junit.Assert.assertEquals
import org.junit.Test

class AuthModelsTest {
    @Test
    fun replacing_tokens_preserves_actor_and_device_context() {
        val original =
            StoredSession(
                tokens = AuthTokens("a1", "t1", "r1", "rt1"),
                staffId = "staff-1",
                staffDisplayName = "Ana",
                venueId = "venue-1",
                venueSlug = "aderlan",
                venueName = "Bar do Aderlan",
                role = "CASHIER",
                deviceId = "device-1",
                deviceTrustState = "TRUSTED",
            )
        val rotated = original.withTokens(AuthTokens("a2", "t2", "r2", "rt2"))

        assertEquals("a2", rotated.tokens.accessToken)
        assertEquals("r2", rotated.tokens.refreshToken)
        assertEquals(original.staffId, rotated.staffId)
        assertEquals(original.deviceId, rotated.deviceId)
        assertEquals(original.deviceTrustState, rotated.deviceTrustState)
    }
}
