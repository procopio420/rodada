package com.rodada.attendance.payments

import android.content.Context
import android.nfc.NfcAdapter
import android.os.Build

/** Hardware checks are preliminary; licensed SDK must still attest security/activation. */
fun detectTapDevice(context: Context): TapDeviceCapabilities {
    val nfc = NfcAdapter.getDefaultAdapter(context)
    val emulator = Build.FINGERPRINT.startsWith("generic") || Build.FINGERPRINT.contains("emulator") ||
        Build.MODEL.contains("Emulator") || Build.PRODUCT.contains("sdk")
    return TapDeviceCapabilities(Build.VERSION.SDK_INT, nfc != null, nfc?.isEnabled == true, !emulator)
}
