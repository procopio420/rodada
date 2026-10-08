package com.rodada.attendance.payments

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class SumUpPaymentsTest {
    private val device = TapDeviceCapabilities(30, true, true, true)

    @Test fun fakeLifecycleNeverConfirmsReceiptLocally() = runBlocking {
        val events = mutableListOf<SumUpPaymentEvent>()
        val provider = SumUpTapToPayProvider(device, true, DeterministicSumUpSdk(), true) { events += it }
        assertTrue(provider.initialize())
        val result = provider.collect(TapPaymentRequest("durable-intent", 1234))
        assertTrue(result is TapCaptureEvidence.Submitted)
        assertEquals(SumUpPaymentEvent.CardRequested, events.first())
        assertEquals(TapCaptureEvidence.ConfirmationPending, provider.collect(TapPaymentRequest("durable-intent", 1234)))
        provider.tearDown()
        assertTrue(provider.availability() is TapToPayAvailability.Unavailable)
        assertTrue(IntegratedPayment("p", "t", 1234, "CONFIRMED", simulated = true).message.contains("SIMULAÇÃO"))
    }

    @Test fun unavailableNfcDeviceAuthorizationSdkAndInitializationBlockCollection() = runBlocking {
        val missingNfc = SumUpTapToPayProvider(device.copy(nfcSupported = false), true, DeterministicSumUpSdk())
        missingNfc.initialize()
        assertTrue(missingNfc.availability() is TapToPayAvailability.Unavailable)
        val unauthorized = SumUpTapToPayProvider(device, false, DeterministicSumUpSdk())
        unauthorized.initialize()
        assertTrue(unauthorized.collect(TapPaymentRequest("p", 100)) is TapCaptureEvidence.NotStarted)
        assertTrue(SumUpTapToPayProvider(device, true, null).availability() is TapToPayAvailability.Unavailable)
        val failure = object : SumUpSdkBoundary {
            override suspend fun initialize(): Boolean = throw java.io.IOException()
            override fun startPayment(checkout: SumUpCheckout) = flow<SumUpPaymentEvent> { error("must not start") }
            override suspend fun tearDown() {}
        }
        val provider = SumUpTapToPayProvider(device, true, failure)
        assertFalse(provider.initialize())
        assertTrue(provider.collect(TapPaymentRequest("p", 100)) is TapCaptureEvidence.NotStarted)
    }

    @Test fun cancelUnknownAndFailedEventsAlwaysRequireBackendReconciliation() = runBlocking {
        for (event in listOf(SumUpPaymentEvent.TransactionCanceled, SumUpPaymentEvent.TransactionResultUnknown, SumUpPaymentEvent.TransactionFailed)) {
            val provider = SumUpTapToPayProvider(device, true, DeterministicSumUpSdk(event), true)
            provider.initialize()
            assertEquals(TapCaptureEvidence.ConfirmationPending, provider.collect(TapPaymentRequest("p", 100)))
            assertTrue(tapEventMessage(event).isNotBlank())
        }
    }
}
