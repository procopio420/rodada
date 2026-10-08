package com.rodada.attendance.auth

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class AuthHttpClient(baseUrl: String) {
    private val baseUrl = baseUrl.trimEnd('/')

    fun login(request: LoginRequest): StoredSession {
        val response =
            request(
                method = "POST",
                path = "/auth/login/",
                body =
                    JSONObject()
                        .put("venue_slug", request.venueSlug)
                        .put("login_identifier", request.loginIdentifier)
                        .put("pin", request.pin)
                        .put("installation_id", request.installationId)
                        .put("platform", request.platform)
                        .put("friendly_label", request.friendlyLabel),
            ) ?: error("Resposta vazia no login")
        return parseSession(response)
    }

    fun refresh(refreshToken: String): AuthTokens {
        val response =
            request(
                method = "POST",
                path = "/auth/refresh/",
                body = JSONObject().put("refresh_token", refreshToken),
            ) ?: error("Resposta vazia no refresh")
        return parseTokens(response)
    }

    fun me(accessToken: String): MeSnapshot {
        val response =
            request(
                method = "GET",
                path = "/auth/me/",
                accessToken = accessToken,
            ) ?: error("Resposta vazia em /auth/me/")
        val staff = response.getJSONObject("staff")
        val venue = response.getJSONObject("venue")
        val membership = response.getJSONObject("membership")
        val device = response.optJSONObject("device")
        val capabilities = response.optJSONArray("capabilities")

        return MeSnapshot(
            staffId = staff.getString("id"),
            staffDisplayName = staff.getString("display_name"),
            venueId = venue.getString("id"),
            venueSlug = venue.getString("slug"),
            venueName = venue.getString("name"),
            role = membership.getString("role"),
            deviceTrustState = device?.optString("trust_state").orEmpty(),
            capabilities = capabilities?.let { json ->
                buildSet { for (index in 0 until json.length()) add(json.getString(index)) }
            }.orEmpty(),
        )
    }

    fun lock(accessToken: String) {
        request(method = "POST", path = "/auth/lock/", accessToken = accessToken, body = JSONObject())
    }

    fun logout(accessToken: String) {
        request(method = "POST", path = "/auth/logout/", accessToken = accessToken, body = JSONObject())
    }

    fun switchOperator(
        accessToken: String,
        loginIdentifier: String,
        pin: String,
    ): StoredSession {
        val response =
            request(
                method = "POST",
                path = "/auth/switch-operator/",
                accessToken = accessToken,
                body =
                    JSONObject()
                        .put("login_identifier", loginIdentifier)
                        .put("pin", pin),
            ) ?: error("Resposta vazia na troca de operador")
        return parseSession(response)
    }

    fun reauthenticate(accessToken: String, pin: String): ReauthReceipt {
        val response =
            request(
                method = "POST",
                path = "/auth/reauthenticate/",
                accessToken = accessToken,
                body = JSONObject().put("pin", pin),
            ) ?: error("Resposta vazia na reautenticação")

        return ReauthReceipt(
            reauthenticatedAt = response.getString("reauthenticated_at"),
            validUntil = response.getString("valid_until"),
        )
    }

    fun invalidationEvents(
        accessToken: String,
        after: Long,
    ): AccessInvalidationFeed {
        val response =
            request(
                method = "GET",
                path = "/auth/invalidation-events/?after=" + after,
                accessToken = accessToken,
            ) ?: error("Resposta vazia no feed de invalidação")
        val resultsJson = response.getJSONArray("results")
        val results =
            buildList {
                for (index in 0 until resultsJson.length()) {
                    val item = resultsJson.getJSONObject(index)
                    add(
                        AccessInvalidationEvent(
                            id = item.getLong("id"),
                            eventType = item.getString("event_type"),
                        ),
                    )
                }
            }
        return AccessInvalidationFeed(
            cursor = response.getLong("cursor"),
            results = results,
        )
    }

    private fun parseSession(response: JSONObject): StoredSession {
        val staff = response.getJSONObject("staff")
        val venue = response.optJSONObject("venue")
        val device = response.getJSONObject("device")

        return StoredSession(
            tokens = parseTokens(response),
            staffId = staff.getString("id"),
            staffDisplayName = staff.getString("display_name"),
            venueId = venue?.optString("id").orEmpty(),
            venueSlug = venue?.optString("slug").orEmpty(),
            venueName = venue?.optString("name").orEmpty(),
            role = response.getString("role"),
            deviceId = device.getString("id"),
            deviceTrustState = device.getString("trust_state"),
            capabilities = response.optJSONArray("capabilities")?.let { json ->
                buildSet { for (index in 0 until json.length()) add(json.getString(index)) }
            }.orEmpty(),
        )
    }

    private fun parseTokens(response: JSONObject): AuthTokens =
        AuthTokens(
            accessToken = response.getString("access_token"),
            accessExpiresAt = response.getString("access_expires_at"),
            refreshToken = response.getString("refresh_token"),
            refreshExpiresAt = response.getString("refresh_expires_at"),
        )

    private fun request(
        method: String,
        path: String,
        body: JSONObject? = null,
        accessToken: String? = null,
    ): JSONObject? {
        val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = 10_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Accept", "application/json")
            if (accessToken != null) {
                connection.setRequestProperty("Authorization", "Bearer " + accessToken)
            }

            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.bufferedWriter(Charsets.UTF_8).use {
                    it.write(body.toString())
                }
            }

            val status = connection.responseCode
            val stream =
                if (status in 200..299) connection.inputStream else connection.errorStream
            val raw = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()

            if (status !in 200..299) {
                val json = raw.takeIf { it.isNotBlank() }?.let(::JSONObject)
                throw AuthApiException(
                    status = status,
                    code = json?.optString("code").orEmpty().ifBlank { "HTTP_" + status },
                    message = json?.optString("message").orEmpty().ifBlank { "Falha de autenticação." },
                )
            }

            if (status == 204 || raw.isBlank()) return null
            return JSONObject(raw)
        } finally {
            connection.disconnect()
        }
    }
}
