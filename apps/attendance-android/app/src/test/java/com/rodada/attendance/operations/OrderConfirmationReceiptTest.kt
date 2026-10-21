package com.rodada.attendance.operations

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicReference
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class OrderConfirmationReceiptTest {
    private val tab = "11111111-1111-4111-8111-111111111111"
    private val order = "22222222-2222-4222-8222-222222222222"
    private val other = "33333333-3333-4333-8333-333333333333"
    private val key = "44444444-4444-4444-8444-444444444444"

    private fun detail(tabId: String = tab, orderIds: List<String> = listOf(order)) = TabDetail(
        TabSummary(tabId, "Same label", "OPEN", 1, 1200, 0, 1200),
        orderIds.map { TabOrder(it, "2026-10-21T00:00:00Z", emptyList()) },
    )

    private fun requireUnverified(action: () -> Unit) {
        val error = runCatching(action).exceptionOrNull()
        assertTrue(error is OperationsApiException)
        assertEquals(502, (error as OperationsApiException).status)
        assertEquals("ORDER_CONFIRMATION_UNVERIFIED", error.code)
    }

    @Test fun successfulHttpWithoutMatchingReceiptIsStillUnknownAndDoesNotChangePayload() {
        val response = AtomicReference("{}")
        val received = CopyOnWriteArrayList<String>()
        val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/tabs/$tab/orders/confirm/") { exchange ->
            received.add(exchange.requestBody.bufferedReader().readText())
            val bytes = response.get().toByteArray()
            exchange.sendResponseHeaders(200, bytes.size.toLong())
            exchange.responseBody.use { it.write(bytes) }
        }
        server.start()
        try {
            val client = OperationsHttpClient("http://127.0.0.1:${server.address.port}")
            val lines = listOf(CartLine(Product(other, "Fixture", 1200, true, "BAR", "AVAILABLE"), 1))
            for (invalid in listOf("{}", """{"id":"$order"}""",
                """{"id":"$order","tab_id":"$other"}""", """{"id":"invalid","tab_id":"$tab"}""")) {
                response.set(invalid)
                requireUnverified { client.confirmOrder("test-access", tab, lines, key) }
            }
            response.set("""{"id":"$order","tab_id":"$tab"}""")
            val first = client.confirmOrder("test-access", tab, lines, key)
            val replay = client.confirmOrder("test-access", tab, lines, key)
            assertEquals(OrderConfirmationReceipt(order, tab), first)
            assertEquals(first, replay)
            assertEquals(6, received.size)
            assertEquals(1, received.toSet().size)
            assertEquals(key, JSONObject(received.first()).getString("idempotency_key"))
        } finally { server.stop(0) }
    }

    @Test fun staleReadWithoutReturnedOrderCannotClearIntent() {
        requireUnverified { OrderConfirmationReceipt(order, tab).requireReadback(detail(orderIds = listOf(other))) }
    }

    @Test fun readOfAnotherTabCannotConfirmOrderEvenWithSameLabelAndOrderId() {
        requireUnverified { OrderConfirmationReceipt(order, tab).requireReadback(detail(tabId = other)) }
    }

    @Test fun matchingOrderNeedNotBeTheLastOrderInCanonicalReadback() {
        OrderConfirmationReceipt(order, tab).requireReadback(detail(orderIds = listOf(order, other)))
    }
}
