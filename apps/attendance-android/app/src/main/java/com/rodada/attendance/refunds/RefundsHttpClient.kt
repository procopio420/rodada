package com.rodada.attendance.refunds

import com.rodada.attendance.operations.OperationsApiException
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class RefundsHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun create(accessToken: String, command: RefundCommand): RefundResult =
        when (command) {
            is DirectRefundCommand -> request(
                accessToken,
                "/payments/${command.paymentId}/refunds/",
                JSONObject()
                    .put("amount_cents", command.amountCents)
                    .put("reason", command.reason)
                    .put("idempotency_key", command.idempotencyKey)
                    .apply { command.cashPointId?.let { put("cash_point_id", it) } },
            ).let { parseDirect(it) }
            is SettleCorrectionRefundCommand -> request(
                accessToken,
                "/corrections/${command.correctionId}/settle-refund/",
                JSONObject()
                    .put("payment_id", command.paymentId)
                    .put("amount_cents", command.amountCents)
                    .put("refund_idempotency_key", command.idempotencyKey)
                    .apply { command.cashPointId?.let { put("cash_point_id", it) } },
            ).let { parseSettlement(it, command) }
        }

    private fun parseDirect(json: JSONObject) =
        RefundResult(
            id = json.getString("id"), paymentId = json.getString("payment_id"), correctionId = null,
            status = json.getString("status"), amountCents = json.getLong("amount_cents"),
            chargesCents = json.optLong("charges_cents"), paymentsCents = json.optLong("payments_cents"),
            refundsCents = json.optLong("refunds_cents"), exposureCents = json.optLong("exposure_cents"),
        )

    private fun parseSettlement(json: JSONObject, command: SettleCorrectionRefundCommand) =
        RefundResult(
            id = json.getString("refund_id"), paymentId = command.paymentId, correctionId = json.getString("id"),
            status = json.getString("status"), amountCents = command.amountCents,
            chargesCents = json.optLong("charges_cents"), paymentsCents = json.optLong("payments_cents"),
            refundsCents = json.optLong("refunds_cents"), exposureCents = json.optLong("exposure_cents"),
        )

    private fun request(accessToken: String, path: String, body: JSONObject): JSONObject {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = 10_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("Authorization", "Bearer $accessToken")
            connection.setRequestProperty("Content-Type", "application/json")
            connection.doOutput = true
            connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(body.toString()) }
            val status = connection.responseCode
            val raw = (if (status in 200..299) connection.inputStream else connection.errorStream)
                ?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val error = raw.takeIf(String::isNotBlank)?.let(::JSONObject)
                throw OperationsApiException(status, error?.optString("code").orEmpty().ifBlank { "HTTP_$status" }, error?.optString("message").orEmpty().ifBlank { "Falha ao criar estorno." })
            }
            return JSONObject(raw)
        } finally {
            connection.disconnect()
        }
    }
}
