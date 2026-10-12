package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class PartySizeContractTest {
    @Test fun `unknown covers is not zero or one and request retains exact version and identity`() {
        val snapshot = PartySizeSnapshot.fromJson(JSONObject("""{"covers_count":null,"version":0,"source":null}"""))
        assertNull(snapshot.count)
        assertEquals(0, snapshot.version)
        val command = PartySizeCommand(4, 3, "Correção explícita", "original-key")
        val first = command.toJson().toString()
        assertEquals(first, command.toJson().toString())
        assertEquals(4, JSONObject(first).getInt("covers_count"))
        assertEquals(3, JSONObject(first).getInt("expected_version"))
        assertEquals("original-key", JSONObject(first).getString("idempotency_key"))
    }
}
