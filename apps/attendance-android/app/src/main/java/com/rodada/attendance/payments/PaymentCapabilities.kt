package com.rodada.attendance.payments

data class PaymentCapabilities(val pix: Boolean = false, val tapToPay: Boolean = false, val simulated: Boolean = false)

fun tapEventMessage(event: SumUpPaymentEvent, simulated: Boolean = false): String =
    (if (simulated) "SIMULAÇÃO — " else "") + when (event) {
        SumUpPaymentEvent.CardRequested -> "Aguardando aproximação"
        SumUpPaymentEvent.CardPresented -> "Cartão detectado"
        SumUpPaymentEvent.CvmRequested -> "Verificação pelo componente seguro do provedor"
        SumUpPaymentEvent.CvmPresented -> "Confirmando com o provedor"
        is SumUpPaymentEvent.TransactionDone -> "Verificando transação no Rodada"
        SumUpPaymentEvent.TransactionFailed -> "Transação não verificada; reconcilie antes de repetir"
        SumUpPaymentEvent.TransactionCanceled -> "Cancelamento informado; verificando no Rodada"
        SumUpPaymentEvent.TransactionResultUnknown -> "Resultado desconhecido; não cobre novamente"
    }
