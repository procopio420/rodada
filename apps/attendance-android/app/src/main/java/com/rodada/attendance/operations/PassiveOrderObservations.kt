package com.rodada.attendance.operations

import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.Executors
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONObject

/** Ephemeral lookup context only. No token, payload or personal data in events. */
data class ObservationOrigin(val venueId: String, val staffId: String, val deviceId: String, val sessionId: String)

class PassiveOrderObservations(
    private val baseUrl: String,
    private val appVersion: String,
    private val accessToken: (ObservationOrigin) -> String?,
) {
    enum class Outcome(val value: String, val reason: String) {
        CONFIRMED("CONFIRMED", ""), REJECTED("REJECTED", "SERVER_REJECTION"),
        UNKNOWN("UNKNOWN", "UNCERTAIN"), AUTH_UNAVAILABLE("PREFLIGHT", "AUTH_UNAVAILABLE"),
        PREPARATION_FAILED("PREFLIGHT", "PREPARATION_FAILED"),
    }

    fun intentSaved(origin: ObservationOrigin, key: String) {
        enqueue(origin, key, mapOf("kind" to "INTENT_SAVED"))
    }

    fun begin(origin: ObservationOrigin, key: String, recovery: Boolean): Attempt =
        Attempt(origin, key, recovery)

    inner class Attempt internal constructor(
        private val origin: ObservationOrigin, private val key: String, private val recovery: Boolean,
    ) {
        private val started = System.nanoTime()
        private val attemptId = UUID.randomUUID().toString()
        private val finished = AtomicBoolean(false)

        fun finish(outcome: Outcome) {
            runCatching {
                if (!finished.compareAndSet(false, true)) return
                val elapsed = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - started)
                enqueue(origin, key, mapOf("kind" to "ATTEMPT_FINISHED", "attempt_id" to attemptId,
                    "outcome" to outcome.value, "reason" to outcome.reason, "recovery" to recovery,
                    "duration_ms" to if (elapsed in 0..3_600_000L) elapsed else JSONObject.NULL))
            }
        }
    }

    private fun enqueue(origin: ObservationOrigin, key: String, fields: Map<String, Any>) {
        runCatching {
            worker.execute {
                runCatching {
                    // Read the current store at execution time, not at enqueue time.
                    val token = accessToken(origin) ?: return@execute
                    val hash = MessageDigest.getInstance("SHA-256").digest(key.toByteArray(Charsets.UTF_8))
                        .joinToString("") { "%02x".format(it.toInt() and 255) }
                    val event = JSONObject(fields).put("event_id", UUID.randomUUID().toString())
                        .put("intent_ref", hash).put("channel", "ANDROID").put("ux_version", "033-ux2")
                        .put("app_version", appVersion)
                    val body = JSONObject().put("origin_venue", origin.venueId)
                        .put("origin_session", origin.sessionId).put("events", org.json.JSONArray().put(event))
                    post(origin, token, body.toString())
                }
            }
        }
    }

    private fun post(origin: ObservationOrigin, token: String, body: String) {
        val connection = URL(baseUrl.trimEnd('/') + "/attendance-observations/").openConnection() as HttpURLConnection
        val deadline = deadlines.schedule({ connection.disconnect() }, 1500, TimeUnit.MILLISECONDS)
        try {
            connection.requestMethod = "POST"
            connection.instanceFollowRedirects = false
            connection.connectTimeout = 750
            connection.readTimeout = 750
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("X-Rodada-Originating-Session", origin.sessionId)
            val bytes = body.toByteArray(Charsets.UTF_8)
            connection.setFixedLengthStreamingMode(bytes.size)
            connection.outputStream.use { it.write(bytes) }
            connection.responseCode // No refresh, retry, body parsing or financial state update.
        } finally {
            deadline.cancel(false)
            connection.disconnect()
        }
    }

    companion object {
        // Shared bounded daemon transport; it never runs work on the caller.
        private val worker = ThreadPoolExecutor(1, 1, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue(7),
            { runnable -> Thread(runnable, "order-observations").apply { isDaemon = true } })
        private val deadlines = Executors.newSingleThreadScheduledExecutor { runnable ->
            Thread(runnable, "order-observation-deadline").apply { isDaemon = true }
        }
    }
}
