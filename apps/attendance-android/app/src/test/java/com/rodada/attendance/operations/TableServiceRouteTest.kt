package com.rodada.attendance.operations

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.CopyOnWriteArrayList
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class TableServiceRouteTest {
    @Test fun freeTableOpenAndReplayReachHttpWithOriginalBody() {
        val received = CopyOnWriteArrayList<Pair<String, String>>()
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/") { exchange ->
            received.add(exchange.requestURI.path to exchange.requestBody.bufferedReader().readText())
            val reply = "{\"tab_id\":\"test-tab\",\"replayed\":${received.size > 1}}".toByteArray()
            exchange.responseHeaders.add("Content-Type", "application/json")
            exchange.sendResponseHeaders(200, reply.size.toLong())
            exchange.responseBody.use { it.write(reply) }
        }
        server.start()
        try {
            val client = OperationsHttpClient("http://127.0.0.1:${server.address.port}")
            val path = "/hospitality/tables/test-table/service/open-tab/"
            val body = JSONObject().put("display_label", "").put("idempotency_key", "test-original-key")
            assertEquals("test-tab", client.tableService("test-access", path, body).getString("tab_id"))
            assertTrue(client.tableService("test-access", path, JSONObject(body.toString())).getBoolean("replayed"))
            assertEquals(2, received.size)
            assertEquals(path, received[0].first)
            assertEquals(body.toString(), received[0].second)
            assertEquals(received[0], received[1])
            for (invalid in listOf("/hospitality/tables/test-table/release/", "/tabs/test-tab/payments/", "/hospitality/tables/test-table/service/open-tab/extra")) {
                assertTrue(runCatching { client.tableService("test-access", invalid, body) }.exceptionOrNull() is IllegalArgumentException)
            }
            assertEquals(2, received.size)
        } finally { server.stop(0) }
    }
}
