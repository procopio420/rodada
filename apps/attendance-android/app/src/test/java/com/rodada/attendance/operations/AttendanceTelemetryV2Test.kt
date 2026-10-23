package com.rodada.attendance.operations

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.security.MessageDigest
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class AttendanceTelemetryV2Test {
    @Test fun sendsHashNotFinancialIdAndPreservesObservedSteps() {
        val received = CopyOnWriteArrayList<String>()
        val auth = CopyOnWriteArrayList<String>()
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/attendance/telemetry/") { exchange ->
            auth.add(exchange.requestHeaders.getFirst("Authorization") ?: "")
            received.add(exchange.requestBody.bufferedReader().readText())
            val reply = "{\"accepted\":true}".toByteArray()
            exchange.responseHeaders.add("Content-Type", "application/json")
            exchange.sendResponseHeaders(202, reply.size.toLong())
            exchange.responseBody.use { it.write(reply) }
        }
        server.start()
        try {
            val client = OperationsHttpClient("http://127.0.0.1:${server.address.port}")
            val key = "random-financial-intent-123"
            client.sendAttendanceTelemetry("token", "intent_started", "origin-session", key)
            client.sendAttendanceTelemetry("token", "confirm_acknowledged", "origin-session", key, 1250, 3)
            assertEquals(2, received.size)
            assertEquals(listOf("Bearer token", "Bearer token"), auth)
            val started = JSONObject(received[0])
            val ack = JSONObject(received[1])
            val expected = MessageDigest.getInstance("SHA-256").digest(key.toByteArray())
                .joinToString("") { "%02x".format(it.toInt() and 255) }
            assertEquals(expected, started.getString("intent_ref"))
            assertEquals(expected, ack.getString("intent_ref"))
            assertEquals("origin-session", ack.getString("origin_session"))
            assertEquals(2, ack.getInt("version"))
            assertEquals("ANDROID", ack.getString("platform"))
            assertEquals("confirm_acknowledged", ack.getString("event"))
            assertEquals(1250, ack.getInt("duration_ms"))
            assertEquals(3, ack.getInt("essential_steps"))
            assertFalse(started.has("essential_steps"))
            assertFalse(started.has("duration_ms"))
            assertFalse(ack.toString().contains(key))
            assertFalse(ack.has("staff_id"))
            assertFalse(ack.has("tab_id"))
            assertFalse(ack.has("order_id"))
            assertNotEquals(started.getString("event_id"), ack.getString("event_id"))
        } finally {
            server.stop(0)
        }
    }

    @Test fun telemetryDoesNotFollowCrossHostRedirectOrForwardAccessToken() {
        val redirected = AtomicInteger(0)
        val target = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        target.createContext("/trap") { exchange ->
            redirected.incrementAndGet()
            exchange.sendResponseHeaders(200, -1)
            exchange.close()
        }
        target.start()
        val origin = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        origin.createContext("/attendance/telemetry/") { exchange ->
            exchange.requestBody.close()
            exchange.responseHeaders.add("Location", "http://127.0.0.1:${target.address.port}/trap")
            exchange.sendResponseHeaders(302, -1)
            exchange.close()
        }
        origin.start()
        try {
            val client = OperationsHttpClient("http://127.0.0.1:${origin.address.port}")
            try {
                client.sendAttendanceTelemetry("secret", "intent_started", "original-session", "random-key")
                fail("Observer must reject redirects")
            } catch (expected: OperationsApiException) {
                assertEquals(302, expected.status)
            }
            assertEquals(0, redirected.get())
        } finally {
            origin.stop(0)
            target.stop(0)
        }
    }
}
