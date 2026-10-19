package com.rodada.attendance.operations

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.CopyOnWriteArrayList
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class TableReleaseContractTest {
    @Test fun releaseCarriesCapturedVisitAndNeverRetriesWithReplacementVisit() {
        val received = CopyOnWriteArrayList<Pair<String, JSONObject>>()
        var activeVisit = "visit-a"
        var generation = 1
        val command = TableReleaseCommand("table-a", activeVisit, generation)
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/") { exchange ->
            val body = JSONObject(exchange.requestBody.bufferedReader().readText())
            received.add(exchange.requestURI.path to body)
            val matches = body.getString("expected_occupancy_id") == activeVisit &&
                body.getInt("expected_generation") == generation
            val reply = (if (matches) "{}" else """{"code":"STALE_OCCUPANCY","detail":"Visit changed"}""").toByteArray()
            exchange.sendResponseHeaders(if (matches) 200 else 409, reply.size.toLong())
            exchange.responseBody.use { it.write(reply) }
        }
        server.start()
        try {
            val client = OperationsHttpClient("http://127.0.0.1:${server.address.port}")
            client.releaseTable("test-access", command)
            activeVisit = "visit-b"
            generation = 2
            val failure = runCatching { client.releaseTable("test-access", command) }.exceptionOrNull()
            assertTrue(failure is OperationsApiException)
            assertEquals(409, (failure as OperationsApiException).status)
            assertEquals("STALE_OCCUPANCY", failure.code)
            assertEquals(2, received.size)
            received.forEach { (path, body) ->
                assertEquals("/hospitality/tables/table-a/release/", path)
                assertEquals(setOf("expected_occupancy_id", "expected_generation"), body.keys().asSequence().toSet())
                assertEquals("visit-a", body.getString("expected_occupancy_id"))
                assertEquals(1, body.getInt("expected_generation"))
            }
        } finally { server.stop(0) }
    }
}
