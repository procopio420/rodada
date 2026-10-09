package com.rodada.attendance.realtime

import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.StoredSession
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlin.random.Random

/** Signals invalidate read models only. They never apply commands or settle pending payments. */
sealed interface RealtimeSignal {
    data object Connected : RealtimeSignal
    data object Reconnecting : RealtimeSignal
    data object Refresh : RealtimeSignal
    data class Revalidate(val accepted: CompletableDeferred<Boolean>) : RealtimeSignal
}

interface OperationalRealtime {
    fun subscribe(session: StoredSession): Flow<RealtimeSignal>
}

/** Reject duplicates and reordered invalidations without assuming contiguous authorized events. */
class CursorGate {
    var cursor: String? = null
        private set
    fun accept(value: String): Boolean {
        if (cursor != null && cursorSequence(value) <= cursorSequence(cursor!!)) return false
        cursor = value
        return true
    }
    fun reset(value: String) { cursor = value }
    suspend fun acceptAfterRevalidation(value: String, revalidate: suspend () -> Unit): Boolean {
        if (cursor != null && cursorSequence(value) <= cursorSequence(cursor!!)) return false
        revalidate()
        return accept(value)
    }
}

fun cursorSequence(cursor: String): Long = cursor.substringAfterLast(':').toLongOrNull() ?: -1

data class SseFrame(val event: String, val id: String?, val data: String)

/** SSE framing handles comments, CRLF and multiline data without buffering the whole stream. */
class SseFrames {
    private var event = "message"
    private var id: String? = null
    private val data = mutableListOf<String>()
    fun line(line: String): SseFrame? {
        if (line.isEmpty()) {
            val result = SseFrame(event, id, data.joinToString("\n"))
                .takeIf { data.isNotEmpty() || id != null || event != "message" }
            event = "message"; id = null; data.clear()
            return result
        }
        if (line.startsWith(":")) return null
        val key = line.substringBefore(':')
        val value = line.substringAfter(':', "").removePrefix(" ")
        when (key) {
            "event" -> event = value
            "id" -> id = value.takeIf { it.isNotBlank() }
            "data" -> data.add(value)
        }
        return null
    }
}

class SseOperationalRealtime(
    baseUrl: String,
    private val auth: AuthRepository,
) : OperationalRealtime {
    private val base = baseUrl.trimEnd('/')

    override fun subscribe(session: StoredSession): Flow<RealtimeSignal> = channelFlow {
        var connection: HttpURLConnection? = null
        val worker = launch(Dispatchers.IO) {
            val gate = CursorGate()
            var cursor: String? = null
            var attempts = 0
            var lastFallback = 0L
            suspend fun revalidate() {
                val accepted = CompletableDeferred<Boolean>()
                send(RealtimeSignal.Revalidate(accepted))
                if (!accepted.await()) throw IOException("Canonical refresh failed; retain resume cursor")
            }
            while (true) {
                try {
                    if (cursor == null) {
                        val baseline = auth.withAuthorizedAccess(session) { token ->
                            val snapshot = open("/realtime/snapshot/", token)
                            try {
                                checkStatus(snapshot)
                                JSONObject(snapshot.inputStream.bufferedReader().use { it.readText() }).getString("cursor")
                            } finally { snapshot.disconnect() }
                        }
                        revalidate()
                        cursor = baseline
                        gate.reset(baseline)
                    }
                    auth.withAuthorizedAccess(session) { token ->
                        val stream = open("/realtime/stream/?cursor=$cursor", token)
                        connection = stream
                        try {
                            checkStatus(stream)
                            stream.inputStream.bufferedReader().use { reader ->
                                val frames = SseFrames()
                                while (true) {
                                    val line = reader.readLine() ?: throw IOException("Realtime disconnected")
                                    val frame = frames.line(line) ?: continue
                                    when (frame.event) {
                                        "reset" -> { cursor = null; throw IOException("Replay gap") }
                                        "revoked" -> throw AuthApiException(403, "AUTH_REVOKED", "Realtime authorization revoked")
                                        "ready", "heartbeat" -> { attempts = 0; trySend(RealtimeSignal.Connected) }
                                        "change" -> {
                                            val next = frame.id ?: continue
                                            if (gate.acceptAfterRevalidation(next) { revalidate() }) {
                                                // Only invalidation crosses this transport boundary.
                                                cursor = next
                                            }
                                        }
                                    }
                                }
                            }
                        } finally { stream.disconnect(); connection = null }
                    }
                } catch (error: kotlinx.coroutines.CancellationException) { throw error
                } catch (error: Exception) {
                    send(RealtimeSignal.Reconnecting)
                    if (error is AuthApiException && error.status in listOf(401, 403) && error.code != "ACCESS_TOKEN_EXPIRED") return@launch
                    val now = System.currentTimeMillis()
                    if (now - lastFallback >= 30_000) {
                        send(RealtimeSignal.Refresh)
                        lastFallback = now
                    }
                    val cap = (1000L shl attempts.coerceAtMost(5)).coerceAtMost(30_000)
                    attempts++
                    delay(cap / 2 + Random.nextLong(cap / 2 + 1))
                }
            }
        }
        awaitClose { connection?.disconnect(); worker.cancel() }
    }

    private fun open(path: String, token: String): HttpURLConnection =
        (URL(base + path).openConnection() as HttpURLConnection).apply {
            connectTimeout = 10_000
            readTimeout = 45_000
            setRequestProperty("Authorization", "Bearer $token")
            setRequestProperty("Accept", if (path.contains("stream")) "text/event-stream" else "application/json")
        }

    private fun checkStatus(connection: HttpURLConnection) {
        val status = connection.responseCode
        if (status !in 200..299) {
            val raw = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
            val body = runCatching { JSONObject(raw) }.getOrNull()
            throw AuthApiException(status, body?.optString("code").orEmpty(), "Realtime HTTP $status")
        }
    }
}
