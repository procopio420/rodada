package com.rodada.attendance.operations

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ServiceRequestTest {
    @Test fun `missing timing and responsibility are never invented`() {
        val task = ServiceRequest.fromJson(JSONObject("""{"id":"task","task_type":"BILL_REQUEST","state":"OPEN","destination_label":"Mesa 24"}"""))
        assertEquals("Pedido de conta", task.title)
        assertEquals("Tempo não informado", task.ageLabel)
        assertEquals("Sem responsável", task.responsibility("me"))
        assertFalse(task.belongsToOther("me"))
    }
    @Test fun `other operator claim blocks actions while own claim remains actionable`() {
        val task = ServiceRequest("task", "SERVICE_REQUEST", "CLAIMED", "Mesa 24", "other", 125)
        assertTrue(task.belongsToOther("me"))
        assertEquals("Outro operador está responsável", task.responsibility("me"))
        assertFalse(task.belongsToOther("other"))
        assertEquals("Você está responsável", task.responsibility("other"))
        assertEquals("Solicitado há 2 min", task.ageLabel)
        assertEquals("Tempo não informado", task.copy(ageSeconds = -1).ageLabel)
    }
}
