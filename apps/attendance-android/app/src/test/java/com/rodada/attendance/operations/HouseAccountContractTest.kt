package com.rodada.attendance.operations

import org.json.JSONException
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HouseAccountContractTest {
    private val client = OperationsHttpClient("https://unused.example")
    private fun payload() = JSONObject("""{
        "id":"tab", "display_label":"João", "state":"REQUIRES_ACTION", "version":4,
        "charges_cents":3000, "payments_cents":0, "exposure_cents":3000,
        "effective_limit_cents":3000, "remaining_capacity_cents":0, "percentage_used":100,
        "consumption_blocked":true, "limit_warning":true, "action_reasons":["SPENDING_LIMIT"]
    }""")

    @Test fun `reads canonical blocked capacity and reasons`() {
        val tab = client.tabSummary(payload())
        assertTrue(tab.consumptionBlocked)
        assertEquals(0L, tab.remainingCapacityCents)
        assertEquals(100, tab.percentageUsed)
        assertEquals(listOf("SPENDING_LIMIT"), tab.actionReasons)
    }

    @Test fun `temporary approval uses server effective limit`() {
        val approved = payload().put("effective_limit_cents", 5000).put("remaining_capacity_cents", 2000)
            .put("consumption_blocked", false).put("percentage_used", 60).put("action_reasons", org.json.JSONArray())
        val tab = client.tabSummary(approved)
        assertEquals(5000L, tab.effectiveLimitCents)
        assertEquals(2000L, tab.remainingCapacityCents)
        assertEquals(60, tab.percentageUsed)
    }

    @Test fun `restricted zero limit has no fictional percentage`() {
        val tab = client.tabSummary(payload().put("effective_limit_cents", 0).put("percentage_used", JSONObject.NULL))
        assertNull(tab.percentageUsed)
        assertTrue(tab.consumptionBlocked)
    }

    @Test(expected = JSONException::class) fun `missing canonical limit fails instead of enabling unlimited consumption`() {
        val missing = payload().apply { remove("effective_limit_cents") }
        client.tabSummary(missing)
    }
}
