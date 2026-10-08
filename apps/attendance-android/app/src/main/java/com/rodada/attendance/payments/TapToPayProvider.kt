package com.rodada.attendance.payments

/** Provider boundary: SDK types must not reach Compose screens, Tabs or ledger contracts. */
interface TapToPayProvider {
    val providerName: String
    fun availability(): TapToPayAvailability
}

sealed interface TapToPayAvailability {
    data object Available : TapToPayAvailability
    data class Unavailable(val operationalMessage: String) : TapToPayAvailability
}

/**
 * Intentionally non-operational until the private artifact and activation are supplied by
 * Paytime. An SDK callback will still require server-side canonical reconciliation.
 */
class PaytimeTapProvider : TapToPayProvider {
    override val providerName = "Paytime"

    override fun availability() = TapToPayAvailability.Unavailable(
        "Tap on Phone ainda não está habilitado neste aparelho. Use um método disponível.",
    )
}
