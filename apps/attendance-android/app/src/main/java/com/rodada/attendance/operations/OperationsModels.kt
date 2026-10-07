package com.rodada.attendance.operations

import java.util.Locale

data class TabSummary(
    val id: String,
    val displayLabel: String,
    val state: String,
    val version: Int,
    val chargesCents: Long,
    val paymentsCents: Long,
    val exposureCents: Long,
)

data class OrderItem(
    val id: String,
    val productName: String,
    val unitPriceCents: Long,
    val quantity: Int,
    val lineTotalCents: Long,
    val state: String,
)

data class TabOrder(
    val id: String,
    val confirmedAt: String,
    val items: List<OrderItem>,
)

data class TabDetail(
    val summary: TabSummary,
    val orders: List<TabOrder>,
)

data class Product(
    val id: String,
    val name: String,
    val priceCents: Long,
    val active: Boolean,
    val fulfillmentStation: String,
    val availability: String,
)

data class CartLine(
    val product: Product,
    val quantity: Int,
)

enum class PaymentMethod(val apiValue: String, val label: String) {
    CASH("CASH", "Dinheiro"),
    CARD("CARD", "Cartão manual"),
    EXTERNAL_TERMINAL("EXTERNAL_TERMINAL", "Terminal externo"),
    PIX("PIX", "Pix"),
    OTHER("OTHER", "Pagamento externo"),
}

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
