package com.rodada.attendance.operations

import java.util.Locale

data class CustomerSummary(val id: String, val displayName: String, val kind: String)

data class TabSummary(
    val id: String,
    val displayLabel: String,
    val state: String,
    val version: Int,
    val chargesCents: Long,
    val paymentsCents: Long,
    val exposureCents: Long,
    val originalSubtotalCents: Long = chargesCents,
    val discountsCents: Long = 0,
    val courtesyCents: Long = 0,
    val serviceChargeCents: Long = 0,
    val correctionsCents: Long = 0,
    val refundsCents: Long = 0,
    val payableCents: Long = chargesCents,
    val serviceAssessmentStale: Boolean = false,
    val transfersCents: Long = 0,
    val effectiveLimitCents: Long = 3000,
    val remainingCapacityCents: Long = 3000,
    val percentageUsed: Int? = null,
    val consumptionBlocked: Boolean = false,
    val limitWarning: Boolean = false,
    val actionReasons: List<String> = emptyList(),
)

data class OrderItem(
    val id: String,
    val productName: String,
    val unitPriceCents: Long,
    val quantity: Int,
    val lineTotalCents: Long,
    val state: String,
    val customizationText: String = "",
)

data class TabOrder(
    val id: String,
    val confirmedAt: String,
    val items: List<OrderItem>,
)

data class TabDetail(
    val summary: TabSummary,
    val orders: List<TabOrder>,
    val payments: List<TabPayment> = emptyList(),
    val refundRequiredCorrections: List<RefundRequiredCorrection> = emptyList(),
)

data class TabPayment(
    val id: String,
    val amountCents: Long,
    val method: String,
    val status: String,
    val refundedCents: Long,
    val simulated: Boolean = false,
)

data class RefundRequiredCorrection(
    val id: String,
    val orderItemId: String,
    val itemName: String,
    val refundRequiredCents: Long,
)

data class Product(
    val id: String,
    val name: String,
    val priceCents: Long,
    val active: Boolean,
    val fulfillmentStation: String,
    val availability: String,
    val variants: List<ProductVariant> = emptyList(),
    val modifierGroups: List<ModifierGroup> = emptyList(),
)

/** Server-authoritative READY work; it is never synthesized from a local order cart. */
data class DeliveryTask(
    val id: String,
    val state: String,
    val destinationLabel: String,
    val productName: String,
    val quantity: Int,
    val tabLabel: String,
    val ageSeconds: Long,
)

data class CartLine(
    val product: Product,
    val quantity: Int,
    val customization: Customization = Customization(),
    val lineId: String = java.util.UUID.randomUUID().toString(),
) {
    val unitPriceCents: Long get() = product.unitPrice(customization)
}

enum class ConnectivityState {
    ONLINE,
    RECONNECTING,
    STALE,
    OFFLINE,
}

enum class PaymentMethod(val apiValue: String, val label: String) {
    TAP_CREDIT("TAP_TO_PAY", "Aproximação crédito"),
    TAP_DEBIT("TAP_TO_PAY", "Aproximação débito"),
    PIX("PIX", "Pix integrado"),
    CASH("CASH", "Dinheiro"),
    EXTERNAL_TERMINAL("EXTERNAL_TERMINAL", "Terminal externo"),
}

data class CashPoint(val id: String, val label: String, val activeShiftId: String?)

data class ZoneSummary(val id: String, val label: String)

/** Physical context only: balances and payments continue to belong to each Tab. */
data class TableSummary(
    val id: String,
    val label: String,
    val status: String,
    val guestOrderingMode: String,
    val guestOrderingBlocked: Boolean,
    val zone: ZoneSummary?,
    val activeOccupancy: TableOccupancy?,
)

data class TableOccupancy(
    val id: String,
    val generation: Int,
    val tabs: List<TableOccupancyTab>,
)

data class TableOccupancyTab(val id: String, val displayLabel: String)

data class PaymentResult(
    val id: String,
    val method: String,
    val chargesCents: Long,
    val paymentsCents: Long,
    val exposureCents: Long,
)

class OperationsApiException(
    val status: Int,
    val code: String,
    override val message: String,
) : Exception(message)

fun formatCents(cents: Long): String {
    val absolute = kotlin.math.abs(cents)
    val sign = if (cents < 0) "-" else ""
    return String.format(Locale("pt", "BR"), "%sR$ %,d,%02d", sign, absolute / 100, absolute % 100)
}

/** Parses a Brazilian user-entered amount to integer cents without ever using floating point. */
fun parseCents(raw: String): Long? {
    val normalized = raw.trim().replace("R$", "", ignoreCase = true).replace(" ", "")
    if (normalized.isBlank()) return null
    val comma = normalized.lastIndexOf(',')
    val dot = normalized.lastIndexOf('.')
    val separator = maxOf(comma, dot)
    val digits = normalized.filter { it.isDigit() }
    if (digits.isEmpty()) return null
    val centsDigits =
        if (separator >= 0) {
            val fraction = normalized.substring(separator + 1).filter { it.isDigit() }
            when {
                fraction.length > 2 -> return null
                else -> fraction.padEnd(2, '0')
            }
        } else {
            "00"
        }
    val whole =
        if (separator >= 0) normalized.substring(0, separator).filter { it.isDigit() }
        else digits
    return (whole.ifBlank { "0" }.toLongOrNull()?.times(100))?.plus(centsDigits.toLong())
}
