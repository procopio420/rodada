package com.rodada.attendance.operations

/** Only offer commands that can apply to the canonical state. The server still authorizes. */
fun tabOperationOptions(capabilities: Set<String>, state: String): List<Pair<String, String>> = buildList {
    if (state in setOf("OPEN", "REQUIRES_ACTION")) {
        if ("tab.move" in capabilities) add("MOVE_LOCATION" to "Mover local")
        if ("tab.transfer" in capabilities) {
            add("SPLIT" to "Dividir conta")
            add("MOVE_ITEMS" to "Transferir consumo")
            add("MERGE" to "Juntar comandas")
        }
        if ("tab.cancel_empty" in capabilities) add("CANCEL_EMPTY" to "Cancelar comanda vazia")
    }
    if (state == "CLOSED" && "tab.reopen" in capabilities) add("REOPEN" to "Reabrir comanda")
}

/** A secondary read failure must not obscure the financial command's server rejection. */
suspend fun <T> refreshAfterTabOperationRejection(
    rejection: OperationsApiException,
    refresh: suspend () -> T,
): T = try {
    refresh()
} catch (refreshFailure: Exception) {
    rejection.addSuppressed(refreshFailure)
    throw rejection
}
