package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class TableServiceRecoveryTest {
    @Test fun tableIntentRoundtripKeepsFrozenDestinationAndKey() {
        val original = RecoveryIntent.TableService("intent", "staff", "venue", "device", "same-key", 12L,
            RecoveryState.CHECKING, "/hospitality/occupancies/visit/tabs/open/",
            """{"idempotency_key":"same-key","expected_generation":3,"display_label":"João"}""")
        val restored = RecoveryIntent.fromJson(original.toJson())
        assertEquals(original, restored)
        assertTrue(original.evidence().label.contains("mesa"))
    }
}
