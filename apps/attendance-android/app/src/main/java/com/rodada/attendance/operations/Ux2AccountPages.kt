package com.rodada.attendance.operations

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.AttendanceUx2

@Composable
internal fun Ux2AccountPage(state: OperationsUiState, tab: TabDetail, onBack: () -> Unit,
    onPay: () -> Unit, onClose: () -> Unit, onReturn: () -> Unit,
    onAdjustPricing: () -> Unit, onRefund: (TabPayment) -> Unit,
    onSettleCorrection: (RefundRequiredCorrection) -> Unit) {
    val summary = tab.summary
    val closed = summary.state in setOf("CLOSED", "CANCELLED")
    val locked = !state.canLeaveTabContext()
    BackHandler { if (!locked) onBack() }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        TextButton(onBack, enabled = !locked) { Text("← Voltar") }
        Ux2Eyebrow("Conta · ${summary.operationalReference()}")
        Ux2Title(if (closed) "Conta encerrada." else "Fechar a conta.")
        Text(summary.displayLabel.ifBlank { summary.operationalReference() } + (summary.tableLabel?.let { " · Mesa $it" } ?: " · Sem mesa"), style = AttendanceUx2.text(16))
        Ux2CreditBar(summary, 0, {}, false, compact = true)
        Ux2SettlementSummary("Falta receber", summary.exposureCents,
            if (closed) "Comanda já encerrada" else if (summary.exposureCents == 0L) "Saldo quitado" else "Pode receber tudo ou uma parte")
        Ux2ReceiptLine("Consumo registrado", formatCents(summary.payableCents))
        if (summary.paymentsCents > 0) Ux2ReceiptLine("Total já recebido", formatCents(summary.paymentsCents))
        if (summary.refundsCents > 0) Ux2ReceiptLine("Estornos", formatCents(summary.refundsCents))
        if (tab.payments.isNotEmpty()) Text("Recebimentos", style = AttendanceUx2.text(20, 800))
        tab.payments.forEach { payment ->
            Ux2ReceiptLine((if (payment.simulated) "SIMULAÇÃO · " else "") + paymentMethodLabel(payment.method) + " · " + paymentStatusLabel(payment.status), formatCents(payment.amountCents))
            if (payment.refundedCents > 0) Text("Já estornado: ${formatCents(payment.refundedCents)}")
            if (!payment.simulated && payment.amountCents > payment.refundedCents)
                TextButton({ onRefund(payment) }, enabled = !locked) { Text("Estornar recebimento") }
        }
        if (state.cart.isNotEmpty() || state.orderIntentId != null) Text("Pedido não enviado. Resolva o rascunho antes de encerrar.")
        if (summary.serviceAssessmentStale) {
            Text("Atualize a taxa de serviço antes de receber.")
            Ux2Action("Revisar valores da conta", !locked, onAdjustPricing)
        }
        tab.refundRequiredCorrections.forEach { correction ->
            Text("${correction.itemName} · ${formatCents(correction.refundRequiredCents)} a restituir")
            Ux2Action("Resolver restituição", !locked, { onSettleCorrection(correction) })
        }
        state.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.noticeMessage?.let { Text(it) }
        if (closed) Ux2Action("Voltar à mesa ou às comandas", !locked, onReturn, true)
        else if (summary.exposureCents > 0) Ux2Action("Receber ${formatCents(summary.exposureCents)}", !locked && !summary.serviceAssessmentStale, onPay, true)
        else Ux2Action("Encerrar comanda", !locked && state.cart.isEmpty() && !summary.serviceAssessmentStale, onClose, true)
    }
}

@Composable
internal fun Ux2ReceiptPage(state: OperationsUiState, tab: TabDetail, onBack: () -> Unit,
    onPay: (Long, PaymentMethod, String?, Boolean) -> Unit, onRecover: () -> Unit, onKeepOpen: () -> Unit) {
    val summary = tab.summary
    val pending = state.pendingPayment
    var raw by rememberSaveable(summary.id) { mutableStateOf("${summary.exposureCents / 100},${(summary.exposureCents % 100).toString().padStart(2, '0')}") }
    var method by rememberSaveable(summary.id) { mutableStateOf(PaymentMethod.CASH) }
    var cashPoint by rememberSaveable(summary.id) { mutableStateOf(state.cashPoints.firstOrNull { it.activeShiftId != null }?.id.orEmpty()) }
    val amount = parseCents(raw)
    val full = amount == summary.exposureCents && state.cart.isEmpty() && state.orderIntentId == null
    val valid = amount != null && amount > 0 && amount <= summary.exposureCents && !state.submitting && pending == null &&
        summary.state !in setOf("CLOSED", "CANCELLED") && !summary.serviceAssessmentStale &&
        (method != PaymentMethod.CASH || state.cashPoints.any { it.id == cashPoint && it.activeShiftId != null })
    BackHandler { if (!state.submitting && pending == null) onBack() }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        TextButton(onBack, enabled = !state.submitting && pending == null) { Text("← Voltar") }
        Ux2Eyebrow("Recebimento manual")
        Ux2Title("Receber conta.")
        Text("${summary.displayLabel.ifBlank { summary.operationalReference() }} · ${summary.operationalReference()}" + (summary.tableLabel?.let { " · Mesa $it" } ?: " · Sem mesa"))
        Ux2SettlementSummary("Valor ainda a receber", summary.exposureCents, "Pode receber só uma parte")
        if (pending != null) {
            Text(if (pending.confirmedPaymentId != null) "Recebido; encerramento pendente." else "Verificando recebimento original. Não cobre novamente.")
            Text("${formatCents(pending.amountCents)} · ${pending.method.label}")
            Ux2Action("Verificar recebimento e comanda", !state.submitting, onRecover, true)
            if (pending.confirmedPaymentId != null) Ux2Action("Manter comanda no estado atual", !state.submitting, onKeepOpen)
        } else {
            Text("Como foi recebido?", style = AttendanceUx2.text(20, 800))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Dinheiro", "Pix", "Cartão").forEachIndexed { index, label ->
                    OutlinedButton({ method = PaymentMethod.CASH }, enabled = index == 0 && !state.submitting, modifier = Modifier.weight(1f)) { Text(if (index == 0 && method == PaymentMethod.CASH) "✓ $label" else label) }
                }
            }
            Text("Pix e cartão integrados aguardam disponibilidade e homologação.", style = AttendanceUx2.text(12))
            OutlinedButton({ method = PaymentMethod.EXTERNAL_TERMINAL }, enabled = !state.submitting, modifier = Modifier.fillMaxWidth()) {
                Text(if (method == PaymentMethod.EXTERNAL_TERMINAL) "✓ Terminal externo confirmado" else "Registrar terminal externo confirmado")
            }
            if (method == PaymentMethod.EXTERNAL_TERMINAL) Text("Registre somente após confirmação no terminal/provedor. O aplicativo não efetua essa cobrança.")
            if (method == PaymentMethod.CASH) {
                Text("Caixa aberto")
                state.cashPoints.filter { it.activeShiftId != null }.forEach { point ->
                    OutlinedButton({ cashPoint = point.id }, enabled = !state.submitting, modifier = Modifier.fillMaxWidth()) { Text((if (cashPoint == point.id) "✓ " else "") + point.label) }
                }
                if (state.cashPoints.none { it.activeShiftId != null }) Text("Abra um caixa antes de receber dinheiro.")
            }
            OutlinedTextField(raw, { raw = it }, enabled = !state.submitting, label = { Text("Valor recebido (R$)") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), singleLine = true, modifier = Modifier.fillMaxWidth())
            Text("Informe o valor recebido, sem incluir troco.", style = AttendanceUx2.text(12))
            Ux2Action(if (full) "Receber e encerrar comanda" else "Registrar recebimento", valid,
                { onPay(amount ?: 0, method, if (method == PaymentMethod.CASH) cashPoint else null, full) }, true)
            if (full) Ux2Action("Só registrar; manter comanda aberta", valid,
                { onPay(amount ?: 0, method, if (method == PaymentMethod.CASH) cashPoint else null, false) })
        }
        state.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.noticeMessage?.let { Text(it) }
    }
}

@Composable private fun Ux2SettlementSummary(label: String, cents: Long, help: String) {
    Column(Modifier.fillMaxWidth().padding(vertical = 16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(label, style = AttendanceUx2.text(13)); Text(formatCents(cents), style = AttendanceUx2.text(38, 900)); Text(help, style = AttendanceUx2.text(13))
    }
}
@Composable private fun Ux2ReceiptLine(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, modifier = Modifier.weight(1f), style = AttendanceUx2.text(13)); Text(value, style = AttendanceUx2.text(14, 800))
    }
}
