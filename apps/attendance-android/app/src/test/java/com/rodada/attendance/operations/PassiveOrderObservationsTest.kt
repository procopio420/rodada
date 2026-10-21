package com.rodada.attendance.operations

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class PassiveOrderObservationsTest {
    private val origin = ObservationOrigin("fixture-venue", "fixture-staff", "fixture-device", "original-session")

    @Test fun hashesIntentAndCorrelatesReplayWithoutPayloadOrTokens() {
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        val received = CopyOnWriteArrayList<String>()
        val completed = CountDownLatch(3)
        server.createContext("/attendance-observations/") { exchange ->
            received.add(exchange.requestBody.bufferedReader().readText())
            assertEquals("original-session", exchange.requestHeaders.getFirst("X-Rodada-Originating-Session"))
            exchange.sendResponseHeaders(204, -1); exchange.close(); completed.countDown()
        }
        server.start()
        try {
            val observer = PassiveOrderObservations("http://127.0.0.1:${server.address.port}", "1.0") { "fixture-access" }
            val key = "original-random-financial-intent"
            observer.intentSaved(origin, key)
            observer.begin(origin, key, false).finish(PassiveOrderObservations.Outcome.UNKNOWN)
            val replay = observer.begin(origin, key, true)
            replay.finish(PassiveOrderObservations.Outcome.CONFIRMED)
            replay.finish(PassiveOrderObservations.Outcome.UNKNOWN)
            assertTrue(completed.await(5, TimeUnit.SECONDS))
            val events = received.map { JSONObject(it).getJSONArray("events").getJSONObject(0) }
            assertEquals(3, received.size)
            assertEquals(1, events.map { it.getString("intent_ref") }.toSet().size)
            assertTrue(events.all { it.getString("intent_ref").matches(Regex("[a-f0-9]{64}")) })
            assertTrue(received.none { it.contains(key) || it.contains("fixture-access") || it.contains("fixture-staff") || it.contains("fixture-device") })
            assertEquals(listOf("UNKNOWN", "CONFIRMED"), events.drop(1).map { it.getString("outcome") })
            assertEquals(listOf(false, true), events.drop(1).map { it.getBoolean("recovery") })
            assertEquals(2, events.drop(1).map { it.getString("attempt_id") }.toSet().size)
        } finally { server.stop(0) }
    }

    @Test fun boundedQueueDoesNotWaitAndDropsOldContextBeforeAnyHttp() {
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        val received = CountDownLatch(1)
        server.createContext("/attendance-observations/") { exchange ->
            exchange.requestBody.close(); exchange.sendResponseHeaders(204, -1); exchange.close(); received.countDown()
        }
        server.start()
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val drained = CountDownLatch(8)
        val current = AtomicBoolean(true)
        try {
            val observer = PassiveOrderObservations("http://127.0.0.1:${server.address.port}", "1.0") {
                entered.countDown(); release.await(5, TimeUnit.SECONDS)
                val accepted = current.get()
                drained.countDown()
                if (accepted) "fixture-access" else null
            }
            observer.intentSaved(origin, "first")
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            // All caller-side calls return while the worker is blocked. Seven
            // queue slots remain; excess observations are dropped, never run here.
            repeat(40) { observer.intentSaved(origin, "queued-$it") }
            current.set(false); release.countDown()
            assertTrue(drained.await(5, TimeUnit.SECONDS))
            assertEquals(1L, received.count)
            current.set(true)
            observer.intentSaved(origin, "current-context")
            assertTrue(received.await(5, TimeUnit.SECONDS))
        } finally { release.countDown(); server.stop(0) }
    }

    @Test fun lostObservationResponseAndRedirectNeverReplayOrRefresh() {
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        val paths = CopyOnWriteArrayList<String>()
        val completed = CountDownLatch(3)
        server.createContext("/") { exchange ->
            paths.add(exchange.requestURI.path)
            exchange.requestBody.readBytes()
            when (paths.size) {
                1 -> exchange.close() // response lost; do not retry this observation
                2 -> { exchange.responseHeaders.add("Location", "/auth/refresh/"); exchange.sendResponseHeaders(307, -1); exchange.close() }
                else -> { exchange.sendResponseHeaders(503, -1); exchange.close() }
            }
            completed.countDown()
        }
        server.start()
        try {
            val observer = PassiveOrderObservations("http://127.0.0.1:${server.address.port}", "1.0") { "fixture-access" }
            repeat(3) { observer.intentSaved(origin, "key-$it") }
            assertTrue(completed.await(5, TimeUnit.SECONDS))
            assertEquals(List(3) { "/attendance-observations/" }, paths.toList())
        } finally { server.stop(0) }
    }
}
