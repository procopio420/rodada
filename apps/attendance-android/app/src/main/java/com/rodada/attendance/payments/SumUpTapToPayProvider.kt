package com.rodada.attendance.payments

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.collect

/** Rodada events mirror the documented SDK events without importing private SDK types. */
sealed interface SumUpPaymentEvent {
    data object CardRequested : SumUpPaymentEvent
    data object CardPresented : SumUpPaymentEvent
    data object CvmRequested : SumUpPaymentEvent
    data object CvmPresented : SumUpPaymentEvent
    data class TransactionDone(val transactionId: String) : SumUpPaymentEvent
    data object TransactionFailed : SumUpPaymentEvent
    data object TransactionCanceled : SumUpPaymentEvent
    data object TransactionResultUnknown : SumUpPaymentEvent
}

enum class CardProcessing { CREDIT, DEBIT }

data class SumUpCheckout(
    val clientUniqueTransactionId: String,
    val totalAmount: Long,
    val tipsAmount: Long? = null,
    val processCardAs: CardProcessing,
)

/** Real implementation wraps TapToPayApiProvider.provide, init(AuthTokenProvider),
 * startPayment(CheckoutData): Flow<PaymentEvent>, and tearDown(). No owner secrets.
 * SDK token issuance remains disabled until employee OAuth delegation is approved.
 */
interface SumUpSdkBoundary {
    suspend fun initialize(): Boolean
    fun startPayment(checkout: SumUpCheckout): Flow<SumUpPaymentEvent>
    suspend fun tearDown()
}

class DeterministicSumUpSdk(private val outcome: SumUpPaymentEvent = SumUpPaymentEvent.TransactionDone("SIMULATED")) : SumUpSdkBoundary {
    override suspend fun initialize() = true
    override fun startPayment(checkout: SumUpCheckout) = flow {
        emit(SumUpPaymentEvent.CardRequested)
        emit(SumUpPaymentEvent.CardPresented)
        // No PIN field or fake PIN pad: certified provider owns sensitive collection.
        emit(outcome)
    }
    override suspend fun tearDown() {}
}

class SumUpTapToPayProvider(
    private val device: TapDeviceCapabilities,
    private val authorized: Boolean,
    private val sdk: SumUpSdkBoundary?,
    private val simulated: Boolean = false,
    private val onEvent: (SumUpPaymentEvent) -> Unit = {},
) : TapToPayProvider {
    override val providerName = "SumUp"
    private var initialized = false
    private var submitted = false
    var cardProcessing = CardProcessing.CREDIT

    suspend fun initialize(): Boolean {
        initialized = try { sdk?.initialize() == true } catch (_: Exception) { false }
        return initialized
    }

    override fun availability(): TapToPayAvailability = when {
        !authorized -> TapToPayAvailability.Unavailable("Aparelho não autorizado para cobrar.")
        !simulated && device.androidApi < 30 -> TapToPayAvailability.Unavailable("Aproximação exige Android 11+.")
        !simulated && (!device.nfcSupported || !device.nfcEnabled || !device.physicalDevice) ->
            TapToPayAvailability.Unavailable("Use um aparelho físico compatível com NFC ativo.")
        sdk == null -> TapToPayAvailability.Unavailable("SDK SumUp ainda não configurado.")
        !initialized -> TapToPayAvailability.Unavailable("Inicialização SumUp pendente ou indisponível.")
        else -> TapToPayAvailability.Available
    }

    override suspend fun collect(request: TapPaymentRequest): TapCaptureEvidence {
        if (submitted) return TapCaptureEvidence.ConfirmationPending
        val available = availability()
        if (available is TapToPayAvailability.Unavailable) return TapCaptureEvidence.NotStarted(available.operationalMessage)
        require(request.amountCents > 0 && request.paymentId.isNotBlank() && request.currency == "BRL")
        submitted = true
        var result: TapCaptureEvidence = TapCaptureEvidence.ConfirmationPending
        try {
            sdk!!.startPayment(SumUpCheckout(request.paymentId, request.amountCents, processCardAs = cardProcessing)).collect { event ->
                onEvent(event)
                result = when (event) {
                    is SumUpPaymentEvent.TransactionDone -> TapCaptureEvidence.Submitted(event.transactionId)
                    // Even failed/canceled events may have a backend transaction. Reconcile all.
                    SumUpPaymentEvent.TransactionFailed, SumUpPaymentEvent.TransactionCanceled,
                    SumUpPaymentEvent.TransactionResultUnknown -> TapCaptureEvidence.ConfirmationPending
                    else -> result
                }
            }
        } catch (_: Exception) { result = TapCaptureEvidence.ConfirmationPending }
        return result
    }

    override fun onHostStopped() { /* No blind cancel or another start after lifecycle interruption. */ }
    override fun close() { initialized = false }
    suspend fun tearDown() { sdk?.tearDown(); initialized = false }
}
