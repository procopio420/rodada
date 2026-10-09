package com.rodada.attendance.cash

import com.rodada.attendance.auth.AuthApiException
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Thin client for the server-owned CashShift workflow. It does not calculate drawer state. */
class CashHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun cashPoints(accessToken: String): List<CashPointSnapshot> =
        request("GET", "/cash/points/", accessToken = accessToken)
            .getJSONArray("results")
            .toObjects()
            .map(::cashPoint)

    fun activeShift(accessToken: String, cashPointId: String): CashShiftSnapshot =
        cashShift(request("GET", "/cash/points/$cashPointId/active-shift/", accessToken = accessToken))

    fun openShift(accessToken: String, command: OpenCashShiftCommand): CashShiftSnapshot =
        cashShift(
            request(
                "POST",
                "/cash/shifts/",
                JSONObject()
                    .put("cash_point_id", command.cashPointId)
                    .put("opening_float_cents", command.openingFloatCents)
                    .put("business_date", command.businessDate)
                    .put("idempotency_key", command.idempotencyKey),
                accessToken,
            ),
        )

    fun shiftDetail(accessToken: String, shiftId: String): CashShiftDetail {
        val response = request("GET", "/cash/shifts/$shiftId/", accessToken = accessToken)
        return CashShiftDetail(
            shift = cashShift(response),
            movements = response.getJSONArray("movements").toObjects().map(::cashMovement),
        )
    }

    fun supply(accessToken: String, shiftId: String, command: CashMovementCommand): CashMovementSnapshot =
        cashMovement(
            request(
                "POST",
                "/cash/shifts/$shiftId/supply/",
                movementBody(command),
                accessToken,
            ),
        )

    fun withdraw(accessToken: String, shiftId: String, command: CashWithdrawalCommand): CashMovementSnapshot =
        cashMovement(
            request(
                "POST",
                "/cash/shifts/$shiftId/withdrawal/",
                JSONObject()
                    .put("amount_cents", command.amountCents)
                    .put("reason", command.reason)
                    .put("idempotency_key", command.idempotencyKey)
                    .put("allow_negative_expected", command.allowNegativeExpected),
                accessToken,
            ),
        )

    fun startCount(accessToken: String, shiftId: String): CashShiftSnapshot =
        cashShift(request("POST", "/cash/shifts/$shiftId/count/start/", JSONObject(), accessToken))

    fun close(accessToken: String, shiftId: String, command: CloseCashShiftCommand): CashShiftSnapshot =
        cashShift(
            request(
                "POST",
                "/cash/shifts/$shiftId/close/",
                JSONObject()
                    .put("counted_amount_cents", command.countedAmountCents)
                    .put("review_threshold_cents", command.reviewThresholdCents)
                    .apply { command.expectedVersion?.let { put("expected_version", it) } },
                accessToken,
            ),
        )

    fun review(accessToken: String, shiftId: String, reason: String): CashShiftSnapshot =
        cashShift(
            request(
                "POST",
                "/cash/shifts/$shiftId/review/",
                JSONObject().put("reason", reason),
                accessToken,
            ),
        )

    fun lateCorrection(
        accessToken: String,
        shiftId: String,
        command: LateCashCorrectionCommand,
    ): CashMovementSnapshot =
        cashMovement(
            request(
                "POST",
                "/cash/shifts/$shiftId/late-corrections/",
                JSONObject()
                    .put("amount_cents", command.amountCents)
                    .put("reason", command.reason)
                    .put("idempotency_key", command.idempotencyKey)
                    .apply { command.correctionOfId?.let { put("correction_of_id", it) } },
                accessToken,
            ),
        )

    private fun movementBody(command: CashMovementCommand) =
        JSONObject()
            .put("amount_cents", command.amountCents)
            .put("reason", command.reason)
            .put("idempotency_key", command.idempotencyKey)

    private fun cashPoint(json: JSONObject) =
        CashPointSnapshot(
            id = json.getString("id"),
            label = json.getString("label"),
            activeShift = json.optJSONObject("active_shift")?.let(::cashShift),
            pendingReviewShift = json.optJSONObject("pending_review_shift")?.let(::cashShift),
        )

    private fun cashShift(json: JSONObject) =
        CashShiftSnapshot(
            id = json.getString("id"),
            cashPointId = json.getString("cash_point_id"),
            businessDate = json.getString("business_date"),
            status = json.getString("status"),
            openingFloatCents = json.getLong("opening_float_cents"),
            countedAmountCents = json.nullableLong("counted_amount_cents"),
            expectedAmountCentsSnapshot = json.nullableLong("expected_amount_cents_snapshot"),
            discrepancyCents = json.nullableLong("discrepancy_cents"),
            reviewStatus = json.getString("review_status"),
            version = json.getLong("version"),
            expectedCents = json.nullableLong("expected_cents"),
            expectedAtCloseCents = json.nullableLong("expected_at_close_cents"),
            postCloseCorrectionCents = json.nullableLong("post_close_correction_cents"),
            correctedExpectedCents = json.nullableLong("corrected_expected_cents"),
        )

    private fun cashMovement(json: JSONObject) =
        CashMovementSnapshot(
            id = json.getString("id"),
            kind = json.getString("kind"),
            amountCents = json.getLong("amount_cents"),
            paymentId = json.nullableString("payment_id"),
            refundId = json.nullableString("refund_id"),
            actorId = json.getString("actor_id"),
            reason = json.optString("reason"),
            occurredAt = json.getString("occurred_at"),
            recordedAt = json.getString("recorded_at"),
            isPostCloseCorrection = json.optBoolean("is_post_close_correction"),
        )

    private fun JSONObject.nullableLong(name: String): Long? =
        if (has(name) && !isNull(name)) getLong(name) else null

    private fun JSONObject.nullableString(name: String): String? =
        if (has(name) && !isNull(name)) optString(name).ifBlank { null } else null

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
            com.rodada.attendance.auth.OriginatingSessionContext.id.get()?.takeIf { it.isNotBlank() }?.let {
                connection.setRequestProperty("X-Rodada-Originating-Session", it)
            }
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
                val code = json?.optString("code").orEmpty().ifBlank { "HTTP_$status" }
                val message = json?.optString("message").orEmpty().ifBlank { "Falha na operação de caixa." }
                // AuthRepository owns token refresh and understands this exception type.
                if (status == 401 || code == "ACCESS_TOKEN_EXPIRED") throw AuthApiException(status, code, message)
                throw CashApiException(status, code, message)
            }
            return JSONObject(raw)
        } finally {
            connection.disconnect()
        }
    }
}
