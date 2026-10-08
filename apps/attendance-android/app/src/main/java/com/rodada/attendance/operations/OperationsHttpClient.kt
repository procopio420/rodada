package com.rodada.attendance.operations

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class OperationsHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun tabs(accessToken: String, includeClosed: Boolean = false): List<TabSummary> {
        val tabs = mutableListOf<TabSummary>()
        var offset = 0
        while (true) {
            val page = request("GET", "/tabs/?active=${!includeClosed}&offset=$offset", accessToken = accessToken)
            tabs += page.getJSONArray("results").toObjects().map(::tabSummary)
            if (page.isNull("next_offset")) return tabs.distinctBy { it.id }
            offset = page.getInt("next_offset")
        }
    }

    fun openTab(accessToken: String, label: String, customerId: String? = null): TabSummary =
        tabSummary(
            request(
                "POST",
                "/tabs/",
                JSONObject().put("display_label", label).apply { if (customerId != null) put("customer_id", customerId) },
                accessToken,
            ),
        )

    fun customers(accessToken: String, query: String): List<CustomerSummary> =
        request("GET", "/customers/?q=" + java.net.URLEncoder.encode(query, "UTF-8"), accessToken = accessToken)
            .getJSONArray("results").toObjects().map {
                CustomerSummary(it.getString("id"), it.getString("display_name"), it.getString("kind"))
            }

    fun tabDetail(accessToken: String, tabId: String): TabDetail {
        val response = request("GET", "/tabs/$tabId/", accessToken = accessToken)
        val orders =
            response.getJSONArray("orders").toObjects().map { order ->
                TabOrder(
                    id = order.getString("id"),
                    confirmedAt = order.optString("confirmed_at"),
                    items =
                        order.getJSONArray("items").toObjects().map { item ->
                            OrderItem(
                                id = item.getString("id"),
                                productName = item.getString("product_name"),
                                unitPriceCents = item.getLong("unit_price_cents"),
                                quantity = item.getInt("quantity"),
                                lineTotalCents = item.getLong("line_total_cents"),
                                state = item.getString("state"),
                            )
                        },
                )
            }
        val payments = response.optJSONArray("payments")?.toObjects()?.map { payment ->
            TabPayment(
                id = payment.getString("id"),
                amountCents = payment.getLong("amount_cents"),
                method = payment.getString("method"),
                status = payment.getString("status"),
                refundedCents = payment.optLong("refunded_cents"),
            )
        }.orEmpty()
        val refundRequired = response.optJSONArray("refund_required_corrections")?.toObjects()?.map { correction ->
            RefundRequiredCorrection(
                id = correction.getString("id"),
                orderItemId = correction.getString("order_item_id"),
                itemName = correction.getString("item_name"),
                refundRequiredCents = correction.getLong("refund_required_cents"),
            )
        }.orEmpty()
        return TabDetail(tabSummary(response), orders, payments, refundRequired)
    }

    fun products(accessToken: String): List<Product> =
        request("GET", "/catalog/products/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map {
                Product(
                    id = it.getString("id"),
                    name = it.getString("name"),
                    priceCents = it.getLong("price_cents"),
                    active = it.getBoolean("active"),
                    fulfillmentStation = it.getString("fulfillment_station"),
                    availability = it.getString("availability"),
                )
            }

    fun deliveryTasks(accessToken: String): List<DeliveryTask> =
        request("GET", "/dispatch/delivery/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map {
                DeliveryTask(
                    id = it.getString("id"),
                    state = it.getString("state"),
                    destinationLabel = it.optString("destination_label"),
                    productName = it.optString("product_name", "Item pronto"),
                    quantity = it.optInt("quantity", 1),
                    tabLabel = it.optString("tab_label"),
                    ageSeconds = it.optLong("age_seconds", 0),
                )
            }

    fun cashPoints(accessToken: String): List<CashPoint> =
        request("GET", "/cash/points/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map {
                CashPoint(
                    id = it.getString("id"),
                    label = it.getString("label"),
                    activeShiftId = it.optJSONObject("active_shift")?.optString("id")?.ifBlank { null },
                )
            }

    fun tables(accessToken: String): List<TableSummary> =
        request("GET", "/hospitality/tables/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map(::tableSummary)

    fun zones(accessToken: String): List<ZoneSummary> =
        request("GET", "/hospitality/zones/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map { ZoneSummary(it.getString("id"), it.getString("label")) }

    fun occupyTable(accessToken: String, tableId: String, tabId: String?) {
        request(
            "POST",
            "/hospitality/tables/$tableId/occupy/",
            JSONObject().apply { if (tabId != null) put("tab_id", tabId) },
            accessToken,
        )
    }

    fun moveTableToZone(accessToken: String, tableId: String, zoneId: String?) {
        request(
            "POST",
            "/hospitality/tables/$tableId/location/",
            JSONObject().put("zone_id", zoneId),
            accessToken,
        )
    }

    fun attachTabToOccupancy(accessToken: String, occupancyId: String, tabId: String) {
        request("POST", "/hospitality/occupancies/$occupancyId/tabs/", JSONObject().put("tab_id", tabId), accessToken)
    }

    fun releaseTable(accessToken: String, tableId: String) {
        request("POST", "/hospitality/tables/$tableId/release/", JSONObject(), accessToken)
    }

    fun startTableCleaning(accessToken: String, tableId: String) {
        request("POST", "/hospitality/tables/$tableId/cleaning/start/", JSONObject(), accessToken)
    }

    fun completeTableCleaning(accessToken: String, tableId: String) {
        request("POST", "/hospitality/tables/$tableId/cleaning/complete/", JSONObject(), accessToken)
    }

    fun completeDelivery(accessToken: String, taskId: String) {
        request("POST", "/dispatch/delivery/$taskId/complete/", JSONObject(), accessToken)
    }

    fun confirmOrder(
        accessToken: String,
        tabId: String,
        lines: List<CartLine>,
        intentId: String,
    ) {
        val lineJson = JSONArray()
        lines.forEach { line ->
            lineJson.put(
                JSONObject()
                    .put("product_id", line.product.id)
                    .put("quantity", line.quantity),
            )
        }
        // The backend persists this UUID per Tab and returns the existing Order on a retry.
        request(
            "POST",
            "/tabs/$tabId/orders/confirm/",
            JSONObject().put("lines", lineJson).put("idempotency_key", intentId),
            accessToken,
        )
    }

    fun collectPayment(
        accessToken: String,
        tabId: String,
        amountCents: Long,
        method: PaymentMethod,
        idempotencyKey: String,
        cashPointId: String?,
    ): PaymentResult {
        val response =
            request(
                "POST",
                "/tabs/$tabId/payments/",
                JSONObject()
                    .put("amount_cents", amountCents)
                    .put("method", method.apiValue)
                    .put("idempotency_key", idempotencyKey)
                    .apply { if (cashPointId != null) put("cash_point_id", cashPointId) },
                accessToken,
            )
        return PaymentResult(
            id = response.getString("id"),
            method = response.getString("method"),
            chargesCents = response.getLong("charges_cents"),
            paymentsCents = response.getLong("payments_cents"),
            exposureCents = response.getLong("exposure_cents"),
        )
    }

    fun closeTab(accessToken: String, tabId: String) {
        request("POST", "/tabs/$tabId/close/", JSONObject(), accessToken)
    }

    internal fun tabSummary(json: JSONObject) =
        TabSummary(
            id = json.getString("id"),
            displayLabel = json.optString("display_label").ifBlank { "Comanda sem nome" },
            state = json.getString("state"),
            version = json.getInt("version"),
            chargesCents = json.getLong("charges_cents"),
            paymentsCents = json.getLong("payments_cents"),
            exposureCents = json.getLong("exposure_cents"),
            transfersCents = json.optLong("transfers_cents"),
            effectiveLimitCents = json.getLong("effective_limit_cents"),
            remainingCapacityCents = json.getLong("remaining_capacity_cents"),
            percentageUsed = if (json.isNull("percentage_used")) null else json.getInt("percentage_used"),
            consumptionBlocked = json.getBoolean("consumption_blocked"),
            limitWarning = json.getBoolean("limit_warning"),
            actionReasons = json.getJSONArray("action_reasons").let { array -> List(array.length()) { array.getString(it) } },
        )

    fun requestApproval(accessToken: String, tabId: String, reason: String, key: String) {
        request("POST", "/tabs/$tabId/approval-request/", JSONObject().put("reason", reason).put("idempotency_key", key), accessToken)
    }

    fun approveLimit(accessToken: String, tabId: String, limitCents: Long, reason: String, expiresAt: String, key: String) {
        request("POST", "/tabs/$tabId/limit-override/", JSONObject()
            .put("limit_cents", limitCents).put("reason", reason)
            .put("expires_at", expiresAt).put("idempotency_key", key), accessToken)
    }

    private fun tableSummary(json: JSONObject): TableSummary {
        val active = json.optJSONObject("active_occupancy")
        return TableSummary(
            id = json.getString("id"),
            label = json.getString("label"),
            status = json.getString("status"),
            guestOrderingMode = json.optString("guest_ordering_mode"),
            guestOrderingBlocked = json.optBoolean("guest_ordering_blocked"),
            zone = json.optJSONObject("zone")?.let { ZoneSummary(it.getString("id"), it.getString("label")) },
            activeOccupancy = active?.let { occupancy ->
                TableOccupancy(
                    id = occupancy.getString("id"),
                    generation = occupancy.optInt("generation"),
                    tabs = occupancy.getJSONArray("tabs").toObjects().map {
                        TableOccupancyTab(it.getString("id"), it.optString("display_label", "Comanda sem nome"))
                    },
                )
            },
        )
    }

    private fun JSONArray.toObjects(): List<JSONObject> = List(length()) { index -> getJSONObject(index) }

    internal fun request(
        method: String,
        path: String,
        body: JSONObject? = null,
        accessToken: String,
    ): JSONObject {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = 10_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("Authorization", "Bearer $accessToken")
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(body.toString()) }
            }
            val status = connection.responseCode
            val raw = (if (status in 200..299) connection.inputStream else connection.errorStream)
                ?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val json = raw.takeIf { it.isNotBlank() }?.let(::JSONObject)
                throw OperationsApiException(
                    status,
                    json?.optString("code").orEmpty().ifBlank { "HTTP_$status" },
                    json?.optString("message").orEmpty().ifBlank { "Falha na operação." },
                )
            }
            return JSONObject(raw)
        } finally {
            connection.disconnect()
        }
    }
}
