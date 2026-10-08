package com.rodada.attendance.corrections

import com.rodada.attendance.operations.OperationsApiException
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class CorrectionsHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun submit(accessToken: String, command: CorrectionCommand): CorrectionResult {
        val path =
            if (command.requiresPostProductionEndpoint()) {
                "/order-items/${command.itemId}/corrections/post-production/"
            } else {
                "/order-items/${command.itemId}/corrections/cancel/"
            }
        val response =
            request(
                "POST",
                path,
                accessToken,
                JSONObject()
                    .put("kind", command.action.apiKind)
                    .put("reason_code", command.reasonCode)
                    .put("reason_text", command.reasonText)
                    .put("idempotency_key", command.idempotencyKey)
                    .apply { command.replacementProductId?.let { put("replacement_product_id", it) } },
            )
        return correctionResult(response, command.action.apiKind)
    }

    private fun correctionResult(json: JSONObject, defaultKind: String) =
        CorrectionResult(
            id = json.getString("id"),
            status = json.getString("status"),
            kind = json.optString("kind", defaultKind),
            financialDisposition = json.getString("financial_disposition"),
            refundRequiredCents = json.optLong("refund_required_cents", 0),
            replacementOrderItemId = json.optString("replacement_order_item_id").ifBlank { null },
            orderItemId = json.getString("order_item_id"),
            orderItemState = json.getString("order_item_state"),
            chargesCents = json.optLong("charges_cents"),
            paymentsCents = json.optLong("payments_cents"),
            refundsCents = json.optLong("refunds_cents"),
            exposureCents = json.optLong("exposure_cents"),
        )

    private fun request(method: String, path: String, accessToken: String, body: JSONObject): JSONObject {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = 10_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("Authorization", "Bearer $accessToken")
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(body.toString()) }
            val status = connection.responseCode
            val raw = (if (status in 200..299) connection.inputStream else connection.errorStream)
                ?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val error = raw.takeIf(String::isNotBlank)?.let(::JSONObject)
                throw OperationsApiException(
                    status,
                    error?.optString("code").orEmpty().ifBlank { "HTTP_$status" },
                    error?.optString("message").orEmpty().ifBlank { "Falha ao corrigir item." },
                )
            }
            return JSONObject(raw)
        } finally {
            connection.disconnect()
        }
    }
}
