package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class TableReleaseCommandTest {
    @Test fun confirmationEnvelopeCarriesOriginalOccupancyAndGeneration() {
        val original = TableReleaseCommand("table-a", "visit-a", 7)
        val newer = TableReleaseCommand("table-a", "visit-b", 8)
        val body = original.toJson()
        assertEquals(setOf("expected_occupancy_id", "expected_generation"), body.keys().asSequence().toSet())
        assertEquals("visit-a", body.getString("expected_occupancy_id"))
        assertEquals(7, body.getInt("expected_generation"))
        assertNotEquals(newer.toJson().toString(), body.toString())
    }
    @Test(expected = IllegalArgumentException::class) fun invalidGenerationCannotProduceReleaseCommand() {
        TableReleaseCommand("table", "visit", 0)
    }
}
