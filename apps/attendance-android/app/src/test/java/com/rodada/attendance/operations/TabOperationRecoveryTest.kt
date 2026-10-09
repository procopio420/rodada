package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class TabOperationRecoveryTest {
    @Test fun originalCommandSurvivesRecoveryWithoutChangingVersionsOrKey() {
        val command = JSONObject().put("kind", "SPLIT").put("expected_version", 8)
            .put("destination_tab_id", "destination").put("destination_version", 12)
            .put("idempotency_key", "original-key").put("lines", org.json.JSONArray()
                .put(JSONObject().put("charge_id", "charge").put("amount_cents", 1501)))
        val intent = RecoveryIntent.TabStructure("intent", "staff", "venue", "device", "original-key", 1,
            RecoveryState.PENDING, "source", command.toString())
        val recovered = RecoveryIntent.fromJson(intent.toJson()) as RecoveryIntent.TabStructure
        assertEquals(intent, recovered)
        val body = JSONObject(recovered.commandJson)
        assertEquals(8, body.getInt("expected_version"))
        assertEquals(12, body.getInt("destination_version"))
        assertEquals("original-key", body.getString("idempotency_key"))
        assertEquals(1501L, body.getJSONArray("lines").getJSONObject(0).getLong("amount_cents"))
    }
}

class TabOperationPresentationTest {
    private val capabilities = setOf("tab.move", "tab.transfer", "tab.cancel_empty", "tab.reopen")

    @Test fun closedAndCancelledTabsDoNotOfferFinancialTransfers() {
        assertEquals(listOf("REOPEN"), tabOperationOptions(capabilities, "CLOSED").map { it.first })
        assertTrue(tabOperationOptions(capabilities, "CANCELLED").isEmpty())
        assertTrue(tabOperationOptions(capabilities, "SETTLING").isEmpty())
        assertTrue(tabOperationOptions(emptySet(), "CLOSED").isEmpty())
        assertEquals(5, tabOperationOptions(capabilities, "OPEN").size)
    }

    @Test fun refreshFailurePreservesTheOriginalServerRejection() = kotlinx.coroutines.runBlocking {
        val rejection = OperationsApiException(409, "VERSION_CONFLICT", "Confira a seleção.")
        val refreshFailure = java.io.IOException("Read timed out")
        try {
            refreshAfterTabOperationRejection(rejection) { throw refreshFailure }
            fail("Must surface the original rejection")
        } catch (caught: OperationsApiException) {
            assertSame(rejection, caught)
            assertEquals("VERSION_CONFLICT", caught.code)
            assertSame(refreshFailure, caught.suppressed.single())
        }
    }
}
