package com.rodada.attendance.operations

import org.junit.Assert.*
import org.junit.Test

class TableReleaseTargetTest {
    @Test fun confirmationEnvelopeCarriesOriginalOccupancyAndGeneration() {
        val original = TableReleaseTarget("table-a", "visit-a", 7)
        val newer = TableReleaseTarget("table-a", "visit-b", 8)
        val body = original.body()
        assertEquals(setOf("expected_occupancy_id", "expected_generation"), body.keys().asSequence().toSet())
        assertEquals("visit-a", body.getString("expected_occupancy_id"))
        assertEquals(7, body.getInt("expected_generation"))
        assertNotEquals(newer.body().toString(), body.toString())
    }
    @Test(expected = IllegalArgumentException::class) fun invalidGenerationCannotProduceReleaseCommand() {
        TableReleaseTarget("table", "visit", 0)
    }
}
