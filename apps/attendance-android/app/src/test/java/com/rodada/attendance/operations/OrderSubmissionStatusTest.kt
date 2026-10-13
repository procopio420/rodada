package com.rodada.attendance.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class OrderSubmissionStatusTest {
    @Test fun normalPendingOrderShowsSendingNotReconnect() {
        val message = OrderSubmissionStatus.message(RecoveryState.PENDING)
        assertEquals("Enviando pedido…", message)
        assertFalse(message.contains("reconect", ignoreCase = true))
        assertFalse(message.contains("pendente", ignoreCase = true))
    }

    @Test fun ambiguousOrderShowsReconciliation() {
        assertEquals(
            "Verificando pedido pendente; não registre outro pedido.",
            OrderSubmissionStatus.message(RecoveryState.CHECKING),
        )
    }

    @Test fun retryableOrderDoesNotPretendToBeNew() {
        assertEquals(
            "Verificando pedido pendente; não registre outro pedido.",
            OrderSubmissionStatus.message(RecoveryState.SAFE_TO_RETRY),
        )
    }
}
