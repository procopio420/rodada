package com.rodada.attendance.operations

/** A freshly captured order is not evidence of a network outage. */
internal object OrderSubmissionStatus {
    fun message(state: RecoveryState): String =
        if (state == RecoveryState.PENDING) "Enviando pedido…"
        else "Verificando pedido pendente; não registre outro pedido."
}
