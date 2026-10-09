package com.rodada.attendance.payments

import android.graphics.BitmapFactory
import android.util.Base64
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp

@Composable
fun IntegratedPaymentPanel(payment: IntegratedPayment, busy: Boolean, onCheck: () -> Unit, onDismiss: () -> Unit) {
    val clipboard = LocalClipboardManager.current
    val bitmap = remember(payment.qrCode) {
        runCatching {
            val bytes = Base64.decode(payment.qrCode.substringAfter(","), Base64.DEFAULT)
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }.getOrNull()
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (payment.simulated) "SIMULAÇÃO de pagamento" else if (payment.confirmed) "Pagamento confirmado" else "Pagamento Pix") },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                Text(payment.message)
                if (payment.blocksNewCharge && payment.expiresAt.isNotBlank()) {
                    Text("Validade informada pelo provedor: ${payment.expiresAt}")
                }
                if (busy) CircularProgressIndicator()
                if (payment.blocksNewCharge) {
                    bitmap?.let { Image(it, contentDescription = "QR Pix da cobrança", modifier = Modifier.size(200.dp)) }
                    if (payment.copyPaste.isNotBlank()) {
                        Text("Pix copia e cola")
                        SelectionContainer { Text(payment.copyPaste) }
                        TextButton(onClick = { clipboard.setText(AnnotatedString(payment.copyPaste)) }) { Text("Copiar código Pix") }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onCheck, enabled = !busy) { Text("Verificar no Rodada") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Voltar à comanda") } },
    )
}
