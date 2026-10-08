package com.rodada.attendance.operations

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class OperationsHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun tabs(accessToken: String): List<TabSummary> =
        request("GET", "/tabs/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map(::tabSummary)

    fun openTab(accessToken: String, label: String): TabSummary =
        tabSummary(
            request(
                "POST",
                "/tabs/",
                JSONObject().put("display_label", label),
                accessToken,
            ),
        )

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
        return TabDetail(tabSummary(response), orders)
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
    ): PaymentResult {
        val response =
            request(
                "POST",
                "/tabs/$tabId/payments/",
                JSONObject()
                    .put("amount_cents", amountCents)
                    .put("method", method.apiValue)
                    .put("idempotency_key", idempotencyKey),
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

    private fun tabSummary(json: JSONObject) =
        TabSummary(
            id = json.getString("id"),
            displayLabel = json.optString("display_label").ifBlank { "Comanda sem nome" },
            state = json.getString("state"),
            version = json.getInt("version"),
            chargesCents = json.getLong("charges_cents"),
            paymentsCents = json.getLong("payments_cents"),
            exposureCents = json.getLong("exposure_cents"),
        )

    private fun JSONArray.toObjects(): List<JSONObject> = List(length()) { index -> getJSONObject(index) }

    private fun request(
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
