package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PricingContractTest {
    @Test fun `money input never rounds binary floating point`() {
        assertEquals(3333L, pricingMinorUnits("33,33"))
        assertEquals(1500L, pricingMinorUnits("15.00"))
        assertEquals(null, pricingMinorUnits("1.001"))
        assertEquals(null, pricingMinorUnits("-1"))
        assertEquals(null, pricingMinorUnits("1e5"))
    }

    @Test fun `pricing recovery retains exact command and original requester identity`() {
        val original = RecoveryIntent.Pricing("id", "requester", "venue", "device", "key", 1L,
            RecoveryState.CHECKING, "tab", "{\"kind\":\"TAB_DISCOUNT\",\"value\":100,\"expected_version\":4}")
        val restored = RecoveryIntent.fromJson(original.toJson()) as RecoveryIntent.Pricing
        assertEquals(original, restored)
    }

    @Test fun `bill uses canonical allocated values and retains stale assessment status`() {
        val payload = JSONObject("""{"id":"tab", "display_label":"João", "state":"OPEN", "version":9,
          "charges_cents":10000, "original_subtotal_cents":5000, "discounts_cents":1000,
          "courtesy_cents":500, "service_charge_cents":350, "payable_cents":3850,
          "payments_cents":2000, "refunds_cents":100, "exposure_cents":1950,
          "service_assessment_stale":true, "effective_limit_cents":10000,
          "remaining_capacity_cents":8050, "percentage_used":19,
          "consumption_blocked":false, "limit_warning":false, "action_reasons":[]}""")
        val tab = OperationsHttpClient("https://unused.example").tabSummary(payload)
        assertEquals(5000L, tab.originalSubtotalCents)
        assertEquals(1000L, tab.discountsCents)
        assertEquals(500L, tab.courtesyCents)
        assertEquals(350L, tab.serviceChargeCents)
        assertEquals(3850L, tab.payableCents)
        assertEquals(1950L, tab.exposureCents)
        assertTrue(tab.serviceAssessmentStale)
    }

    @Test fun `recovery preserves original bill version rather than repricing a lost response`() {
        val intent = RecoveryIntent.StartPayment("id", "staff", "venue", "device", "key", 1L,
            RecoveryState.CHECKING, "tab", 200L, PaymentMethod.CASH, "cash", 9)
        val restored = RecoveryIntent.fromJson(intent.toJson()) as RecoveryIntent.StartPayment
        assertEquals(9, restored.expectedVersion)
        assertEquals(200L, restored.amountCents)
        assertEquals("key", restored.idempotencyKey)
    }
}
