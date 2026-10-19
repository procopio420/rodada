package com.rodada.attendance.operations

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.rodada.attendance.ui.RodadaVisual

@Composable
internal fun Ux2AccountPage(state: OperationsUiState, tab: TabDetail, onBack: () -> Unit,
    onPay: () -> Unit, onClose: () -> Unit, onReturn: () -> Unit,
    onAdjustPricing: () -> Unit, onRefund: (TabPayment) -> Unit,
    onSettleCorrection: (RefundRequiredCorrection) -> Unit, onOperations: () -> Unit,
    onCorrectItem: (OrderItem) -> Unit) {
    val summary = tab.summary
    val closed = summary.state in setOf("CLOSED", "CANCELLED")
    val locked = !state.canLeaveTabContext()
    var details by rememberSaveable(summary.id) { mutableStateOf(false) }
    BackHandler { if (!locked) onBack() }
    Column(Modifier.fillMaxSize().background(RodadaVisual.Ground).verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        Ux2AccountBack(!locked, onBack)
        Ux2Eyebrow("Conta · ${summary.operationalReference()}")
        Ux2Title(if (closed) "Conta encerrada." else "Fechar a conta.")
        Text(summary.displayLabel.ifBlank { summary.operationalReference() } + (summary.tableLabel?.let { " · ${attendanceTableLocation(it)}" } ?: " · Sem mesa"), style = AttendanceUx2.text(16))
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
        TextButton({ details = !details }, enabled = !locked) { Text(if (details) "Recolher detalhes da conta" else "Ver detalhes da conta") }
        if (details) {
            Ux2ReceiptLine("Subtotal original", formatCents(summary.originalSubtotalCents))
            Ux2ReceiptLine("Descontos", formatCents(summary.discountsCents))
            Ux2ReceiptLine("Cortesias", formatCents(summary.courtesyCents))
            Ux2ReceiptLine("Taxa de serviço", formatCents(summary.serviceChargeCents))
            tab.orders.forEach { order -> order.items.forEach { item ->
                Ux2ReceiptLine("${item.quantity}× ${item.productName}", formatCents(item.lineTotalCents))
                Text(itemStateLabel(item.state), style = AttendanceUx2.text(12))
                if (!closed && item.state != "CANCELLED") TextButton({ onCorrectItem(item) }, enabled = !locked) { Text("Corrigir item") }
            } }
            Ux2Action("Revisar valores da conta", !locked, onAdjustPricing)
            Ux2Action("Operações da comanda", !locked, onOperations)
        }
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
    val openCashPoints = state.cashPoints.filter { it.activeShiftId != null }
    val selectedCashPoint = openCashPoints.singleOrNull()?.id ?: cashPoint
    var paymentDetails by rememberSaveable(summary.id) { mutableStateOf(false) }
    val amount = parseCents(raw)
    val full = method in setOf(PaymentMethod.CASH, PaymentMethod.EXTERNAL_TERMINAL) && amount == summary.exposureCents && state.cart.isEmpty() && state.orderIntentId == null
    val valid = amount != null && amount > 0 && amount <= summary.exposureCents && !state.submitting && pending == null &&
        summary.state !in setOf("CLOSED", "CANCELLED") && !summary.serviceAssessmentStale &&
        (method != PaymentMethod.CASH || state.cashPoints.any { it.id == selectedCashPoint && it.activeShiftId != null })
    BackHandler { if (!state.submitting && pending == null) onBack() }
    Column(Modifier.fillMaxSize().background(RodadaVisual.Ground).verticalScroll(rememberScrollState()).imePadding().padding(20.dp), verticalArrangement = Arrangement.spacedBy(13.dp)) {
        Ux2AccountBack(!state.submitting && pending == null, onBack)
        Ux2Eyebrow("Recebimento manual")
        Ux2Title("Receber conta.")
        Text("${summary.displayLabel.ifBlank { summary.operationalReference() }} · ${summary.operationalReference()}" + (summary.tableLabel?.let { " · ${attendanceTableLocation(it)}" } ?: " · Sem mesa"), style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
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
                    OutlinedButton({ method = if (index == 1) PaymentMethod.PIX else PaymentMethod.CASH }, enabled = (index == 0 || index == 1 && state.pixEnabled) && !state.submitting, modifier = Modifier.weight(1f).heightIn(min = 52.dp),
                        shape = RoundedCornerShape(8.dp), contentPadding = PaddingValues(4.dp),
                        border = BorderStroke(if ((index == 0 && method == PaymentMethod.CASH || index == 1 && method == PaymentMethod.PIX)) 2.dp else 1.dp,
                            if ((index == 0 && method == PaymentMethod.CASH || index == 1 && method == PaymentMethod.PIX)) RodadaVisual.Amber else RodadaVisual.StrongBorder),
                        colors = ButtonDefaults.outlinedButtonColors(containerColor = RodadaVisual.Control, contentColor = RodadaVisual.Paper)) {
                        Text(label, style = AttendanceUx2.text(13, 780))
                    }
                }
            }
            if (state.paymentProviderSimulated && method == PaymentMethod.PIX)
                Text("SIMULAÇÃO Pix. Não recebe dinheiro; não comprova liquidação real.", style = AttendanceUx2.text(12), color = RodadaVisual.Amber)
            if (method == PaymentMethod.EXTERNAL_TERMINAL)
                Text("Registre somente após confirmação no terminal/provedor. O aplicativo não efetua essa cobrança.", style = AttendanceUx2.text(12))
            if (method == PaymentMethod.CASH) {
                val openPoints = openCashPoints
                if (openPoints.size != 1) {
                    Text("Caixa aberto", style = AttendanceUx2.text(13, 740), color = RodadaVisual.Muted)
                    openPoints.forEach { point ->
                        Ux2Action((if (cashPoint == point.id) "✓ " else "") + point.label, !state.submitting, { cashPoint = point.id })
                    }
                    if (openPoints.isEmpty()) Text("Abra um caixa antes de receber dinheiro.")
                }
            }
            Text("Valor recebido (R$)", color = RodadaVisual.Muted, style = AttendanceUx2.text(13, 740))
            OutlinedTextField(raw, { raw = it }, enabled = !state.submitting,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), singleLine = true,
                textStyle = AttendanceUx2.text(16).copy(fontFamily = RodadaVisual.Number),
                shape = RoundedCornerShape(9.dp),
                colors = OutlinedTextFieldDefaults.colors(unfocusedContainerColor = RodadaVisual.Control,
                    focusedContainerColor = RodadaVisual.Control, unfocusedBorderColor = RodadaVisual.StrongBorder),
                modifier = Modifier.fillMaxWidth().heightIn(min = 53.dp))
            Text("Informe o valor recebido, sem incluir troco.", style = AttendanceUx2.text(12))
            Ux2Action(if (method == PaymentMethod.PIX) "Gerar cobrança Pix" else if (full) "Receber e encerrar comanda" else "Registrar recebimento", valid,
                { onPay(amount ?: 0, method, if (method == PaymentMethod.CASH) selectedCashPoint else null, full) }, true)
            if (full) Ux2Action("Só registrar; manter comanda aberta", valid,
                { onPay(amount ?: 0, method, if (method == PaymentMethod.CASH) selectedCashPoint else null, false) })
            if (method == PaymentMethod.CASH && openCashPoints.size == 1)
                Text("Caixa: ${openCashPoints.single().label}", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
            TextButton({ paymentDetails = !paymentDetails }, enabled = !state.submitting,
                contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) {
                Text(if (paymentDetails) "Recolher outros meios e condições" else "Outros meios e condições", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
            }
            if (paymentDetails) {
                Text("Pix depende da capacidade canônica do estabelecimento; cartão integrado aguarda homologação.", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                if (state.tapSimulationEnabled) Ux2Action("Testar aproximação · SIMULAÇÃO", valid,
                    { onPay(amount ?: 0, PaymentMethod.TAP_CREDIT, null, false) })
                Ux2Action(if (method == PaymentMethod.EXTERNAL_TERMINAL) "✓ Terminal externo confirmado" else "Registrar terminal externo confirmado", !state.submitting, { method = PaymentMethod.EXTERNAL_TERMINAL })
            }
        }
        state.errorMessage?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.noticeMessage?.let { Text(it) }
    }
}

@Composable private fun Ux2SettlementSummary(label: String, cents: Long, help: String) {
    Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(12.dp))
        .border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(12.dp)).padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(label, color = RodadaVisual.Muted, style = AttendanceUx2.text(12))
        Text(formatCents(cents), style = AttendanceUx2.text(30, 850).copy(fontFamily = RodadaVisual.Number))
        Text(help, color = RodadaVisual.Muted, style = AttendanceUx2.text(12))
    }
}
@Composable private fun Ux2ReceiptLine(label: String, value: String) {
    Column {
        Row(Modifier.fillMaxWidth().padding(vertical = 13.dp), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(label, modifier = Modifier.weight(1f), color = RodadaVisual.Muted, style = AttendanceUx2.text(12))
            Text(value, style = AttendanceUx2.text(13, 760).copy(fontFamily = RodadaVisual.Number))
        }
        HorizontalDivider(color = RodadaVisual.Border)
    }
}

@Composable private fun Ux2AccountBack(enabled: Boolean, onBack: () -> Unit) {
    TextButton(onClick = onBack, enabled = enabled, contentPadding = PaddingValues(0.dp),
        modifier = Modifier.heightIn(min = 44.dp)) {
        Text("‹  Voltar", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
    }
}
