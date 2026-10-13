package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class ExceptionalRecoveryTest {
    private val correction = RecoveryIntent.Correction("record", "staff", "venue", "device", "original-key", 42,
        RecoveryState.CHECKING, "item", "NEW", CorrectionRecoveryAction.CANCEL, "WRONG_ENTRY", "Original reason", null)
    private val refund = RecoveryIntent.Refund("record", "staff", "venue", "device", "original-key", 42,
        RecoveryState.CHECKING, RefundRecoveryKind.DIRECT, "payment", null, 1234, "Original reason", null)
    private val settlement = refund.copy(kind = RefundRecoveryKind.SETTLE_CORRECTION, correctionId = "correction")
    private val detail = TabDetail(TabSummary("closed-tab", "Original tab", "CLOSED", 7, 100, 100, 0),
        listOf(TabOrder("order", "", listOf(OrderItem("item", "Original item", 100, 1, 100, "CANCELLED")))),
        listOf(TabPayment("payment", 100, "CASH", "REFUNDED", 100)))

    @Test fun `closed tab cancelled item and applied correction remain investigable without changing command`() {
        val target = ExceptionalRecoveryTarget("closed-tab", "item", "payment", "correction", "APPLIED")
        val before = settlement.toJson().toString()
        target.validate(settlement); target.validate(detail)
        assertEquals(before, settlement.toJson().toString())
        assertTrue(detail.refundRequiredCorrections.isEmpty())
    }

    @Test fun `incorrect target identifiers cannot redirect recovery`() {
        val cases = listOf(
            ExceptionalRecoveryTarget("closed-tab", "other-item") to correction,
            ExceptionalRecoveryTarget("closed-tab", paymentId = "other-payment") to refund,
            ExceptionalRecoveryTarget("closed-tab", "item", "payment", "other-correction", "APPLIED") to settlement,
            ExceptionalRecoveryTarget("closed-tab", "item", "other-payment", "correction", "APPLIED") to settlement,
            ExceptionalRecoveryTarget("", "item") to correction)
        cases.forEach { (target, original) -> assertThrows(IllegalArgumentException::class.java) { target.validate(original) } }
    }

    @Test fun `valid reference still requires exact target in canonical tab snapshot`() {
        listOf(ExceptionalRecoveryTarget("other-tab", "item"), ExceptionalRecoveryTarget("closed-tab", "missing-item"),
            ExceptionalRecoveryTarget("closed-tab", paymentId = "missing-payment")).forEach { target ->
            assertThrows(IllegalArgumentException::class.java) { target.validate(detail) }
        }
    }

    @Test fun `settlement without original correction or with unrecognized status remains blocked`() {
        assertFalse(settlement.copy(correctionId = null).evidence().canOpenContext)
        assertThrows(IllegalArgumentException::class.java) { ExceptionalRecoveryTarget("closed-tab", "item", "payment", "correction", "UNKNOWN").validate(settlement) }
        assertFalse(correction.evidence(true).canOpenContext)
    }
}
