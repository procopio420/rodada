package com.rodada.attendance.operations

import java.util.Locale
import java.math.BigDecimal

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
    val tableLabel: String? = null,
    val lastTableLabel: String? = null,
    val relationshipSnapshot: String? = null,
)

/** Mesa atual é uma projeção operacional; nunca substitui o ID da comanda. */
fun TabSummary.operationalReference(): String = "Comanda ${id.take(8).uppercase()}"

private fun TabSummary.optionalName(): String? =
    displayLabel.takeIf { it.isNotBlank() && it != "Comanda sem nome" }

fun TabSummary.operationalLabel(historical: Boolean = false): String =
    tableLabel?.takeIf { it.isNotBlank() }
        ?: (if (historical) lastTableLabel?.let { "$it (última)" } else null)
        ?: optionalName()
        ?: operationalReference()

fun TabSummary.operationalSubtitle(historical: Boolean = false): String {
    val locationShown = !tableLabel.isNullOrBlank() || (historical && !lastTableLabel.isNullOrBlank())
    return listOfNotNull(if (locationShown) optionalName() else null, operationalReference()).joinToString(" · ")
}

fun TabSummary.matchesOperationalQuery(query: String): Boolean =
    listOfNotNull(displayLabel, tableLabel, lastTableLabel, operationalReference())
        .any { it.contains(query, ignoreCase = true) }


data class OrderItem(
    val id: String,
    val productName: String,
    val unitPriceCents: Long,
    val quantity: Int,
    val lineTotalCents: Long,
    val state: String,
    val customizationText: String = "",
    val productId: String? = null,
    val customization: Customization? = null,
    val fulfillmentStationSnapshot: String? = null,
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
    val category: String = "Outros",
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
    val target: StaffTaskTarget = StaffTaskTarget.Unavailable,
    val fulfillmentStation: String? = null,
    val orderItemId: String? = null,
    val orderId: String? = null,
    val claimedById: String? = null,
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

/** SSE reconnect cannot erase a failed canonical API read. */
internal fun ConnectivityState.onRealtimeReconnect(lastSyncedAtMillis: Long?, nowMillis: Long): ConnectivityState =
    when {
        this == ConnectivityState.OFFLINE -> ConnectivityState.OFFLINE
        lastSyncedAtMillis == null || nowMillis - lastSyncedAtMillis < 30_000 -> ConnectivityState.RECONNECTING
        else -> ConnectivityState.STALE
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
    val tableServiceEnabled: Boolean = true,
)

data class TableOccupancy(
    val id: String,
    val generation: Int,
    val tabs: List<TableOccupancyTab>,
    val responsibleStaffId: String? = null,
    val responsibleStaffName: String? = null,
    val responsibilityVersion: Int = 0,
    val serviceAttention: String = "NONE",
    val guestOrderCount: Int = 0,
    val oldestGuestOrderAt: String? = null,
)

data class TableOccupancyTab(val id: String, val displayLabel: String, val state: String = "OPEN", val openedAt: String = "", val displayReference: String = "")

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
    return String.format(Locale.forLanguageTag("pt-BR"), "%sR$ %,d,%02d", sign, absolute / 100, absolute % 100)
}

/** Parses a Brazilian user-entered amount to integer cents without ever using floating point. */
fun parseCents(raw: String): Long? {
    val input = raw.trim().replace(Regex("^R\\$\\s*", RegexOption.IGNORE_CASE), "")
    if (!Regex("(?:[0-9]+|[0-9]*[.,][0-9]{1,2}|[0-9]{1,3}(?:\\.[0-9]{3})+,[0-9]{1,2})").matches(input)) return null
    val normalized = if (',' in input) input.replace(".", "").replace(',', '.') else input
    return try {
        BigDecimal(normalized).movePointRight(2).longValueExact()
    } catch (_: ArithmeticException) {
        null
    } catch (_: NumberFormatException) {
        null
    }
}

internal fun tabsForSurface(tabs: List<TabSummary>, agora: Boolean): List<TabSummary> =
    if (agora) tabs.filter { it.state != "CLOSED" } else tabs


/** API supplies the canonical oldest timestamp; the client formats elapsed time only. */
fun serviceOrderAgeLabel(timestamp: String?): String = runCatching {
    val seconds = java.time.Duration.between(java.time.Instant.parse(timestamp), java.time.Instant.now()).seconds.coerceAtLeast(0)
    if (seconds < 60) "Há menos de 1 min" else "Há ${seconds / 60} min"
}.getOrDefault("Tempo não informado")

/** Canonical table projections may already include their human-readable prefix. */
internal fun attendanceTableLocation(label: String): String =
    if (label.startsWith("Mesa ", ignoreCase = true)) label else "Mesa $label"
