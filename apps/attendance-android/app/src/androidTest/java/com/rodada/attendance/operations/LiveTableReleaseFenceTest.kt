package com.rodada.attendance.operations

import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthApiException
import com.rodada.attendance.auth.AuthHttpClient
import com.rodada.attendance.auth.LoginRequest
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

/** Opt-in real local PostgreSQL API; creates only one uniquely named test table. */
class LiveTableReleaseFenceTest {
    @Test fun originalAndroidCommandCannotReleaseReplacementOccupancy() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue("Dedicated disposable API only", args.getString("liveReleaseFence") == "true")
        val base = args.getString("releaseApi") ?: error("Missing isolated API")
        require(base == "http://10.0.2.2:18134/")
        val session = AuthHttpClient(base).login(LoginRequest("spec033-native-shell-parity",
            "android-post-drop-operator", "2468", "spec033-native-release-${UUID.randomUUID()}"))
        val token = session.tokens.accessToken
        val connection = URL(base + "hospitality/tables/").openConnection() as HttpURLConnection
        val body = JSONObject().put("label", "Native release ${UUID.randomUUID().toString().take(8)}")
            .put("guest_ordering_mode", "DISABLED").toString().toByteArray()
        val tableId = try {
            connection.requestMethod = "POST"; connection.doOutput = true
            connection.connectTimeout = 15_000; connection.readTimeout = 15_000
            connection.setRequestProperty("Authorization", "Bearer $token")
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use { it.write(body) }
            assertEquals(201, connection.responseCode)
            JSONObject(connection.inputStream.bufferedReader().use { it.readText() }).getString("id")
        } finally { connection.disconnect() }
        val client = OperationsHttpClient(base)
        fun current() = client.tables(token).single { it.id == tableId }
        client.occupyTable(token, tableId, null)
        val first = checkNotNull(current().activeOccupancy)
        val original = TableReleaseTarget(tableId, first.id, first.generation)
        client.releaseTable(token, original)
        assertEquals("DIRTY", current().status)
        client.startTableCleaning(token, tableId)
        client.completeTableCleaning(token, tableId)
        client.occupyTable(token, tableId, null)
        val second = checkNotNull(current().activeOccupancy)
        assertNotEquals(first.id, second.id)
        try {
            client.releaseTable(token, original)
            fail("An operation confirmed for A cannot release B")
        } catch (error: AuthApiException) {
            assertEquals(409, error.status); assertEquals("STALE_OCCUPANCY", error.code)
        }
        val preserved = current()
        assertEquals("OCCUPIED", preserved.status)
        assertEquals(second.id, preserved.activeOccupancy?.id)
        assertEquals(second.generation, preserved.activeOccupancy?.generation)
        client.releaseTable(token, TableReleaseTarget(tableId, second.id, second.generation))
        assertEquals("DIRTY", current().status)
        println("LIVE_RELEASE_FENCE_PASS original occupancy rejected; replacement preserved; explicit replacement released")
    }
}
