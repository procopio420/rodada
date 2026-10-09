package com.rodada.attendance.payments

import org.junit.Assert.*
import org.junit.Test
import kotlinx.coroutines.runBlocking

class PaymentsTest {
    @Test fun backendStateAloneControlsConfirmationAndRetry() {
        for (status in listOf("CREATED", "PROCESSING", "AUTHORIZED", "PENDING", "CONFIRMATION_PENDING", "UNKNOWN")) {
            val payment = IntegratedPayment("p", "tab", 1000, status)
            assertFalse(payment.confirmed)
            assertTrue(payment.blocksNewCharge)
        }
        assertTrue(IntegratedPayment("p", "tab", 1000, "CONFIRMED").confirmed)
        assertFalse(IntegratedPayment("p", "tab", 1000, "FAILED").blocksNewCharge)
        assertFalse(IntegratedPayment("p", "tab", 1000, "CANCELLED").blocksNewCharge)
    }

    @Test fun localExpiryNeverReleasesAnAmbiguousPayment() {
        val payment = IntegratedPayment("p", "tab", 1000, "CONFIRMATION_PENDING", copyPaste = "saved-emv", expiresAt = "2000-01-01T00:00:00Z")
        assertTrue(payment.blocksNewCharge)
        assertFalse(payment.confirmed)
        assertEquals("saved-emv", payment.copyPaste)
    }

    @Test fun paytimeRemainsBlockedWithoutPrivateSdk() = runBlocking {
        val provider = PaytimeTapProvider(TapDeviceCapabilities(30, true, true, true))
        assertTrue(provider.availability() is TapToPayAvailability.Unavailable)
        assertTrue(provider.collect(TapPaymentRequest("intent", 1500)) is TapCaptureEvidence.NotStarted)
    }

    @Test fun incompatibleDeviceCannotInvokeSdk() = runBlocking {
        var calls = 0
        val sdk = object : PaytimeSdkBoundary {
            override fun availability() = TapToPayAvailability.Available
            override suspend fun makeTransaction(request: TapPaymentRequest): TapCaptureEvidence {
                calls++
                return TapCaptureEvidence.Submitted("external")
            }
            override fun onHostStopped() {}
            override fun close() {}
        }
        for (device in listOf(TapDeviceCapabilities(29, true, true, true),
            TapDeviceCapabilities(30, false, false, true), TapDeviceCapabilities(30, true, false, true),
            TapDeviceCapabilities(30, true, true, false))) {
            val provider = PaytimeTapProvider(device, sdk, true)
            assertTrue(provider.collect(TapPaymentRequest("intent", 1000)) is TapCaptureEvidence.NotStarted)
        }
        assertEquals(0, calls)
    }

    @Test fun sdkTimeoutNeverAuthorizesAnotherCaptureAndLifecycleIsForwarded() = runBlocking {
        var calls = 0
        var stopped = false
        var closed = false
        val sdk = object : PaytimeSdkBoundary {
            override fun availability() = TapToPayAvailability.Available
            override suspend fun makeTransaction(request: TapPaymentRequest): TapCaptureEvidence {
                calls++
                throw java.io.IOException("transport failed")
            }
            override fun onHostStopped() { stopped = true }
            override fun close() { closed = true }
        }
        val provider = PaytimeTapProvider(TapDeviceCapabilities(30, true, true, true), sdk, true)
        assertEquals(TapCaptureEvidence.ConfirmationPending, provider.collect(TapPaymentRequest("intent", 1500)))
        assertEquals(TapCaptureEvidence.ConfirmationPending, provider.collect(TapPaymentRequest("intent", 1500)))
        assertEquals(1, calls)
        provider.onHostStopped()
        provider.close()
        assertTrue(stopped)
        assertTrue(closed)
    }
}
