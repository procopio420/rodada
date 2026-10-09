package com.rodada.attendance.payments

/** SDK types and card data never cross this boundary. Local results are only evidence. */
interface TapToPayProvider {
    val providerName: String
    fun availability(): TapToPayAvailability
    suspend fun collect(request: TapPaymentRequest): TapCaptureEvidence
    fun onHostStopped()
    fun close()
}

data class TapPaymentRequest(val paymentId: String, val amountCents: Long, val currency: String = "BRL")

sealed interface TapCaptureEvidence {
    data class Submitted(val providerTransactionId: String) : TapCaptureEvidence
    data object ConfirmationPending : TapCaptureEvidence
    data class NotStarted(val message: String) : TapCaptureEvidence
}

sealed interface TapToPayAvailability {
    data object Available : TapToPayAvailability
    data class Unavailable(val operationalMessage: String) : TapToPayAvailability
}

data class TapDeviceCapabilities(
    val androidApi: Int,
    val nfcSupported: Boolean,
    val nfcEnabled: Boolean,
    val physicalDevice: Boolean,
)

/** Implemented only when the private Paytime artifact is supplied and verified.
 * configure(applicationContext, license) belongs to Application.onCreate, once.
 * Activation/checkDeviceStatus/makeTransaction stay in that licensed implementation.
 * Do not invent an SDK abort method: host stop leaves submitted transactions ambiguous.
 */
interface PaytimeSdkBoundary {
    fun availability(): TapToPayAvailability
    suspend fun makeTransaction(request: TapPaymentRequest): TapCaptureEvidence
    fun onHostStopped()
    fun close()
}

class PaytimeTapProvider(
    private val device: TapDeviceCapabilities? = null,
    private val sdk: PaytimeSdkBoundary? = null,
    private val backendEnabled: Boolean = false,
) : TapToPayProvider {
    override val providerName = "Paytime"
    private var submitting = false
    private var submitted = false

    override fun availability(): TapToPayAvailability = when {
        device == null || device.androidApi < 30 -> unavailable("Aproximação exige Android 11 ou superior.")
        !device.physicalDevice -> unavailable("Aproximação exige um aparelho físico homologado.")
        !device.nfcSupported -> unavailable("Este aparelho não possui NFC.")
        !device.nfcEnabled -> unavailable("Ative o NFC para usar aproximação.")
        sdk == null || !backendEnabled -> unavailable("Aproximação aguarda ativação Paytime. Use um método disponível.")
        else -> sdk.availability()
    }

    override suspend fun collect(request: TapPaymentRequest): TapCaptureEvidence {
        if (submitting || submitted) return TapCaptureEvidence.ConfirmationPending
        val available = availability()
        if (available is TapToPayAvailability.Unavailable) return TapCaptureEvidence.NotStarted(available.operationalMessage)
        require(request.amountCents > 0 && request.currency == "BRL" && request.paymentId.isNotBlank())
        submitting = true
        submitted = true
        return try {
            sdk!!.makeTransaction(request).also { if (it is TapCaptureEvidence.NotStarted) submitted = false }
        } catch (_: Exception) {
            TapCaptureEvidence.ConfirmationPending
        } finally {
            submitting = false
        }
    }

    override fun onHostStopped() { sdk?.onHostStopped() }
    override fun close() { sdk?.close() }
    private fun unavailable(message: String) = TapToPayAvailability.Unavailable(message)
}
