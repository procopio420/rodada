package com.rodada.attendance.auth

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.corrections.CorrectionAction
import com.rodada.attendance.corrections.CorrectionCommand
import com.rodada.attendance.corrections.CorrectionsHttpClient
import com.rodada.attendance.operations.OperationsApiException
import com.rodada.attendance.operations.OperationsHttpClient
import com.rodada.attendance.refunds.DirectRefundCommand
import com.rodada.attendance.refunds.RefundsHttpClient
import java.net.ServerSocket
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class OperationalAuthRefreshTest {
    @Test fun operationalClientsClassifyExpiryAndPreserveDomainDenials() {
        for (status in listOf(401, 403)) {
            Fixture(status, if (status == 401) "ACCESS_TOKEN_EXPIRED" else "FORBIDDEN").use { fixture ->
                val requests = listOf<() -> Unit>(
                    { OperationsHttpClient(fixture.url).tabs("test-only-access"); Unit },
                    { CorrectionsHttpClient(fixture.url).submit("test-only-access", CorrectionCommand(
                        "item", "NEW", CorrectionAction.CANCEL, "WRONG_ENTRY", "", "test-only-key")); Unit },
                    { RefundsHttpClient(fixture.url).create("test-only-access", DirectRefundCommand(
                        "payment", 300, "test-only reason", "test-only-key")); Unit },
                )
                requests.forEach { request ->
                    val error = runCatching(request).exceptionOrNull()
                    if (status == 401) {
                        assertTrue(error is AuthApiException)
                        assertEquals("ACCESS_TOKEN_EXPIRED", (error as AuthApiException).code)
                    } else {
                        assertTrue(error is OperationsApiException)
                    }
                }
                assertEquals(3, fixture.requests.get())
            }
        }
    }

    @Test fun parallelExpiryRotatesOnceWithinOriginatingSession() = runBlocking {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val store = SecureSessionStore(context)
        val previous = store.load()
        val session = StoredSession(
            AuthTokens("test-only-old", "", "test-only-refresh", ""),
            "staff", "Test fixture", "venue", "fixture", "Fixture", "OWNER",
            "device", "TRUSTED", sessionId = "test-only-session",
        )
        try {
            store.save(session)
            Fixture(200, "").use { fixture ->
                val repository = AuthRepository(context, AuthHttpClient(fixture.url))
                val barrier = CyclicBarrier(2)
                val attempts = AtomicInteger()
                val results = coroutineScope {
                    (1..2).map {
                        async {
                            repository.withAuthorizedAccess(session) { token ->
                                attempts.incrementAndGet()
                                assertEquals(session.sessionId, OriginatingSessionContext.id.get())
                                if (token == "test-only-old") {
                                    barrier.await(10, TimeUnit.SECONDS)
                                    throw AuthApiException(401, "ACCESS_TOKEN_EXPIRED", "Expired fixture")
                                }
                                token
                            }
                        }
                    }.awaitAll()
                }
                assertEquals(listOf("test-only-new", "test-only-new"), results)
                assertEquals(4, attempts.get())
                assertEquals(1, fixture.requests.get())
                assertEquals(session.sessionId, store.load()?.sessionId)
                val denied = runCatching {
                    repository.withAuthorizedAccess(session) { throw AuthApiException(403, "FORBIDDEN", "Denied fixture") }
                }.exceptionOrNull()
                assertEquals("FORBIDDEN", (denied as AuthApiException).code)
                assertEquals(1, fixture.requests.get())
            }
        } finally {
            if (previous == null) store.clear() else store.save(previous)
        }
    }

    private class Fixture(private val status: Int, private val code: String) : AutoCloseable {
        private val server = ServerSocket(0)
        private val executor = Executors.newSingleThreadExecutor()
        val requests = AtomicInteger()
        val url = "http://127.0.0.1:${server.localPort}"
        init {
            executor.submit {
                while (!server.isClosed) {
                    val socket = try { server.accept() } catch (_: Exception) { break }
                    socket.use {
                        val reader = it.getInputStream().bufferedReader()
                        reader.readLine()
                        var length = 0
                        while (true) {
                            val line = reader.readLine() ?: break
                            if (line.isEmpty()) break
                            if (line.startsWith("Content-Length:", true)) length = line.substringAfter(':').trim().toInt()
                        }
                        repeat(length) { reader.read() }
                        requests.incrementAndGet()
                        val body = if (status == 200) """{"access_token":"test-only-new","access_expires_at":"","refresh_token":"test-only-next","refresh_expires_at":""}"""
                            else """{"code":"$code","message":"Test fixture"}"""
                        val bytes = body.toByteArray(Charsets.UTF_8)
                        it.getOutputStream().write("HTTP/1.1 $status Fixture\r\nContent-Type: application/json\r\nContent-Length: ${bytes.size}\r\nConnection: close\r\n\r\n".toByteArray() + bytes)
                    }
                }
            }
        }
        override fun close() { server.close(); executor.shutdownNow() }
    }
}
