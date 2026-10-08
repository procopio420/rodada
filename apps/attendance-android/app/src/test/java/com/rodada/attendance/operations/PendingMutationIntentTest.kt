package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PendingMutationIntentTest {
    @Test
    fun `round trips all typed recovery commands without changing their idempotency key`() {
        val intents =
            listOf(
                RecoveryIntent.ConfirmOrder(
                    id = "order-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "order-key",
                    createdAtMillis = 1L,
                    state = RecoveryState.PENDING,
                    tabId = "tab-1",
                    lines = listOf(PendingOrderLine("product-1", 2)),
                ),
                RecoveryIntent.StartPayment(
                    id = "payment-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "payment-key",
                    createdAtMillis = 2L,
                    state = RecoveryState.CHECKING,
                    tabId = "tab-1",
                    amountCents = 1_250L,
                    method = PaymentMethod.CASH,
                    cashPointId = "cash-point-1",
                ),
                RecoveryIntent.Correction(
                    id = "correction-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "correction-key",
                    createdAtMillis = 3L,
                    state = RecoveryState.SAFE_TO_RETRY,
                    orderItemId = "item-1",
                    itemState = "PREPARING",
                    action = CorrectionRecoveryAction.REPLACEMENT,
                    reasonCode = "WRONG_ITEM",
                    reasonText = "Produto errado",
                    replacementProductId = "product-2",
                ),
                RecoveryIntent.Refund(
                    id = "refund-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "refund-key",
                    createdAtMillis = 4L,
                    state = RecoveryState.ACTION_REQUIRED,
                    kind = RefundRecoveryKind.SETTLE_CORRECTION,
                    paymentId = "payment-1",
                    correctionId = "correction-1",
                    amountCents = 700L,
                    reason = null,
                    cashPointId = "cash-point-1",
                ),
                RecoveryIntent.CashMovement(
                    id = "cash-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "cash-key",
                    createdAtMillis = 5L,
                    state = RecoveryState.FAILED_TERMINAL,
                    shiftId = "shift-1",
                    kind = CashMovementRecoveryKind.WITHDRAWAL,
                    amountCents = 2_000L,
                    reason = "Sangria",
                    allowNegativeExpected = true,
                    correctionOfId = "movement-1",
                ),
                RecoveryIntent.CashClose(
                    id = "cash-close-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "cash-close-key",
                    createdAtMillis = 6L,
                    state = RecoveryState.CHECKING,
                    shiftId = "shift-1",
                    countedAmountCents = 8_000L,
                    reviewThresholdCents = 0L,
                    expectedVersion = 4L,
                ),
                RecoveryIntent.CompleteDelivery(
                    id = "delivery-intent",
                    staffId = "staff-1",
                    venueId = "venue-1",
                    deviceId = "device-1",
                    idempotencyKey = "delivery-key",
                    createdAtMillis = 7L,
                    state = RecoveryState.CHECKING,
                    deliveryTaskId = "delivery-1",
                ),
            )

        intents.forEach { intent ->
            val restored = RecoveryIntent.fromJson(intent.toJson())

            assertEquals(intent, restored)
            assertEquals(intent.idempotencyKey, restored?.idempotencyKey)
        }
    }

    @Test
    fun `reads the existing persisted payment shape`() {
        val legacy =
            JSONObject()
                .put("type", "START_PAYMENT")
                .put("id", "payment-intent")
                .put("staff_id", "staff-1")
                .put("venue_id", "venue-1")
                .put("device_id", "device-1")
                .put("idempotency_key", "payment-key")
                .put("created_at_millis", 42L)
                .put("state", "CHECKING")
                .put("tab_id", "tab-1")
                .put("amount_cents", 500L)
                .put("method", "CASH")

        assertEquals(
            RecoveryIntent.StartPayment(
                id = "payment-intent",
                staffId = "staff-1",
                venueId = "venue-1",
                deviceId = "device-1",
                idempotencyKey = "payment-key",
                createdAtMillis = 42L,
                state = RecoveryState.CHECKING,
                tabId = "tab-1",
                amountCents = 500L,
                method = PaymentMethod.CASH,
                cashPointId = null,
            ),
            RecoveryIntent.fromJson(legacy),
        )
    }

    @Test
    fun `drops unknown or malformed recovery commands safely`() {
        assertNull(RecoveryIntent.fromJson(JSONObject().put("type", "UNSUPPORTED")))
        assertNull(RecoveryIntent.fromJson(JSONObject().put("type", "REFUND").put("id", "missing-common-fields")))
    }
}
