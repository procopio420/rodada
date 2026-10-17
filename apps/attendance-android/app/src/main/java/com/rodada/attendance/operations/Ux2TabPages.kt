package com.rodada.attendance.operations

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rodada.attendance.ui.AttendanceUx2
import com.rodada.attendance.ui.RodadaVisual

/** Presentation only: all drafts, canonical readbacks and immutable intents belong to the existing controller. */
@Composable
internal fun Ux2TabPages(
    state: OperationsUiState, tab: TabDetail, section: String, onSection: (String) -> Unit,
    onBack: () -> Unit, onAdd: (Product, Customization) -> Unit,
    onEdit: (String, Customization) -> Unit, onQuantity: (String, Int) -> Unit,
    onConfirm: () -> Unit, onRepeat: (RepeatOrderReview, Map<String, Int>) -> Unit,
    onLimit: () -> Unit,
    onVerifyPending: () -> Unit = onConfirm,
) {
    val summary = tab.summary
    val label = summary.displayLabel.ifBlank { summary.operationalReference() }
    val closed = summary.state in setOf("CLOSED", "CANCELLED")
    val locked = !state.canLeaveTabContext() || state.queuedOrders.any { it.tabId == summary.id }
    val cart = state.cart.map { it.copy(product = state.products.firstOrNull { p -> p.id == it.product.id } ?: it.product.copy(active = false)) }
    val total = cart.sumOf { it.unitPriceCents * it.quantity }
    val count = cart.sumOf { it.quantity }
    val pending = state.orderIntentId != null || state.queuedOrders.any { it.tabId == summary.id }
    var query by rememberSaveable(summary.id) { mutableStateOf("") }
    var category by rememberSaveable(summary.id) { mutableStateOf("Todos") }
    val homeScroll = rememberScrollState()
    val catalogScroll = rememberScrollState()
    val reviewScroll = rememberScrollState()
    val pageScroll = when (section) { "Comanda" -> homeScroll; "Pedido atual" -> reviewScroll; else -> catalogScroll }
    var configuring by remember(summary.id) { mutableStateOf<Product?>(null) }
    var editing by remember(summary.id) { mutableStateOf<CartLine?>(null) }
    var repeat by remember(summary.id) { mutableStateOf<RepeatOrderReview?>(null) }
    val back = { if (!locked) { if (section == "Comanda") onBack() else onSection(if (section == "Pedido atual") "Cardápio" else "Comanda") } }
    BackHandler { back() }
    configuring?.let { product ->
        val current = state.products.firstOrNull { it.id == product.id } ?: product.copy(active = false)
        ProductCustomizationSheet(current, editing?.customization ?: current.defaults(),
            onDismiss = { configuring = null; editing = null }, validationQuantity = editing?.quantity,
            capacity = { selection -> draftQuantityCapacity(cart.filterNot { it.lineId == editing?.lineId }, current.id, selection) },
            locked = locked, canSubmit = !locked && !closed && current.active && current.availability == "AVAILABLE" && state.connectivity == ConnectivityState.ONLINE) { selection ->
            editing?.let { onEdit(it.lineId, selection) } ?: onAdd(current, selection)
            configuring = null; editing = null
        }
    }
    repeat?.let { review ->
        Ux2RepeatPage(review, !locked && !closed && state.connectivity == ConnectivityState.ONLINE &&
            tab.orders.firstOrNull { it.id == review.orderId }?.let { reviewRepeatedOrder(it, state.products) == review } == true,
            { repeat = null }) { quantities -> repeat = null; onRepeat(review, quantities) }
        return
    }
    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp).testTag("ux2-tab-pages")) {
        Column(Modifier.weight(1f).verticalScroll(pageScroll), verticalArrangement = Arrangement.spacedBy(13.dp)) {
            TextButton(onClick = back, enabled = !locked, contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) { Text("‹  Voltar", style = AttendanceUx2.text(14), color = RodadaVisual.Muted) }
            Ux2Eyebrow(if (section == "Comanda") summary.operationalReference() else if (section == "Pedido atual") "Resumo opcional" else "Pedido para ${summary.operationalReference()}")
            Ux2Title(when (section) { "Comanda" -> label; "Pedido atual" -> "Resumo do pedido."; else -> "Adicionar itens." })
            Text(if (section == "Comanda") "${summary.tableLabel?.let { "Mesa $it" } ?: "Sem mesa"} · ${if (closed) "Encerrada" else "Comanda aberta"}" else "${label} · ${summary.tableLabel?.let { "Mesa $it" } ?: "Sem mesa"} · destino fixo", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
            if (state.connectivity != ConnectivityState.ONLINE) Text(state.connectivity.label(), style = AttendanceUx2.text(12), color = RodadaVisual.Amber)
            state.errorMessage?.let { Text(it, color = RodadaVisual.Danger, style = AttendanceUx2.text(14)) }
            state.noticeMessage?.let { Text(it, style = AttendanceUx2.text(14)) }
            if (pending) Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(8.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(8.dp)).padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(OrderSubmissionStatus.message(if (state.submitting) RecoveryState.PENDING else RecoveryState.CHECKING), style = AttendanceUx2.text(15, 800), color = RodadaVisual.Amber)
                Text("Não registre outro pedido. A verificação usa a mesma intenção e o destino original.", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                Ux2Action("Verificar mesmo pedido", !state.submitting && !state.loading, onVerifyPending, primary = true)
            }
            if (section == "Comanda") {
                if (closed) Text("Comanda encerrada. Não é possível adicionar pedidos nem recebimentos.")
                else if (!pending) Ux2Action("＋ Adicionar itens", !locked, { onSection("Cardápio") }, true)
                val repeatAction = @Composable { Ux2Action("↻ Mais uma rodada", !locked && !closed && cart.isEmpty() && tab.orders.isNotEmpty(), { tab.orders.lastOrNull()?.let { repeat = reviewRepeatedOrder(it, state.products) } }) }
                val accountAction = @Composable { Ux2Action(if (closed) "Ver conta encerrada" else "Conferir / fechar conta", !locked, { onSection("Conta") }) }
                if (LocalDensity.current.fontScale > 1.3f) { repeatAction(); accountAction() }
                else Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) { repeatAction() }
                    Box(Modifier.weight(1f)) { accountAction() }
                }
                val latest = tab.orders.lastOrNull()
                if (latest == null) {
                    Text("Último pedido", style = AttendanceUx2.text(18, 800))
                    Text("Nenhum pedido anterior.", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
                } else Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(8.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(8.dp)).drawBehind { drawRect(RodadaVisual.Success, size = Size(3.dp.toPx(), size.height)) }.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("Pedido ${latest.id} confirmado", style = AttendanceUx2.text(15, 800))
                    Text("$label · ${summary.operationalReference()} · ${latest.items.sumOf { it.lineTotalCents }.let(::formatCents)}", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                    latest.items.forEach { item ->
                        Text("${item.quantity}× ${item.productName}", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                        val route = when (item.fulfillmentStationSnapshot) { "BAR" -> "Bar"; "KITCHEN" -> "Cozinha"; null -> "Destino não informado"; else -> item.fulfillmentStationSnapshot }
                        val status = when (item.state) { "NEW" -> "Na fila"; "CONFIRMED" -> "Confirmado"; "QUEUED" -> "Na fila"; "ACCEPTED" -> "Aceito"; "PREPARING" -> "Em preparo"; "READY" -> "Pronto"; "PICKED_UP" -> "Retirado"; "DELIVERED" -> "Entregue"; "CANCELLED" -> "Cancelado"; else -> "Estado não reconhecido" }
                        Text("$route · $status", modifier = Modifier.background(RodadaVisual.Control, RoundedCornerShape(5.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(5.dp)).padding(8.dp, 5.dp), style = AttendanceUx2.text(11, 800))
                    }
                }
                HorizontalDivider(color = RodadaVisual.Border)
                val balanceLabel = @Composable { Column { Text("Saldo em aberto", style = AttendanceUx2.text(12), color = RodadaVisual.Muted); Text("Sem incluir rascunhos não enviados", style = AttendanceUx2.text(11), color = RodadaVisual.Subtle) } }
                val balanceValue = @Composable { Text(formatCents(summary.exposureCents), style = AttendanceUx2.text(21, 750).copy(fontFamily = RodadaVisual.Number)) }
                if (LocalDensity.current.fontScale > 1.3f) { balanceLabel(); balanceValue() }
                else Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) { Box(Modifier.weight(1f)) { balanceLabel() }; balanceValue() }
                HorizontalDivider(color = RodadaVisual.Border)
                Ux2CreditBar(summary, 0, onLimit, !locked, compact = true)
                if (count > 0) Text("$count item(ns) não enviados. Confira o rascunho antes de encerrar.", color = RodadaVisual.Amber, style = AttendanceUx2.text(14))
                Ux2Action("Trocar de mesa ou comanda", !locked, onBack)
            } else {
                if (section == "Pedido atual") {
                    Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(10.dp)).border(1.dp, RodadaVisual.Border, RoundedCornerShape(10.dp)).padding(14.dp)) {
                        Text("$label · ${summary.operationalReference()}", style = AttendanceUx2.text(14, 800))
                        Text("${summary.tableLabel?.let { "Mesa $it" } ?: "Sem mesa"} · Rascunho ainda não enviado", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                    }
                    if (cart.isEmpty()) Text("O pedido está vazio.")
                    cart.forEach { line ->
                        Ux2DraftRow(line, !locked, onQuantity) { editing = line; configuring = line.product }
                    }
                    Text("Total do novo pedido", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                    Text(formatCents(total), style = AttendanceUx2.text(24, 800).copy(fontFamily = RodadaVisual.Number))
                    Ux2CreditBar(summary, total, onLimit, !locked)
                    Ux2Action("Continuar escolhendo itens", !locked, { onSection("Cardápio") })
                } else {
                    Ux2CreditBar(summary, total, onLimit, !locked)
                    BasicTextField(query, { query = it }, enabled = !locked, singleLine = true, textStyle = AttendanceUx2.text(14).copy(color = RodadaVisual.Paper), modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp).background(RodadaVisual.Control, RoundedCornerShape(10.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(10.dp)).padding(14.dp), decorationBox = { field ->
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text("⌕", color = RodadaVisual.Muted)
                            Box { if (query.isEmpty()) Text("Buscar no cardápio", style = AttendanceUx2.text(14), color = RodadaVisual.Muted); field() }
                        }
                    })
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        (listOf("Todos") + state.products.map { it.category.ifBlank { "Outros" } }.distinct().sorted()).forEach { name ->
                            OutlinedButton(onClick = { category = name }, enabled = !locked, shape = RoundedCornerShape(7.dp), border = androidx.compose.foundation.BorderStroke(1.dp, if (category == name) RodadaVisual.Paper else RodadaVisual.Border), colors = ButtonDefaults.outlinedButtonColors(containerColor = if (category == name) RodadaVisual.Paper else RodadaVisual.Ground, contentColor = if (category == name) RodadaVisual.Ink else RodadaVisual.Muted), contentPadding = PaddingValues(horizontal = 15.dp, vertical = 8.dp), modifier = Modifier.heightIn(min = 44.dp)) { Text(name, style = AttendanceUx2.text(13, 750)) }
                        }
                    }
                    Text("Cardápio", style = AttendanceUx2.text(18, 800))
                    val products = state.products.filter { (category == "Todos" || it.category.ifBlank { "Outros" } == category) && it.name.contains(query.trim(), true) }
                    if (products.isEmpty()) Text(if (state.loading) "Carregando catálogo…" else "Nenhum produto corresponde à pesquisa.")
                    products.forEach { product ->
                        val lines = cart.filter { it.product.id == product.id }
                        val selectable = !locked && !closed && product.active && product.availability == "AVAILABLE" && state.connectivity == ConnectivityState.ONLINE
                        HorizontalDivider(color = RodadaVisual.Border)
                        Column(Modifier.fillMaxWidth()) {
                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(product.name, style = AttendanceUx2.text(15, 800))
                                    Text(formatCents(product.priceCents), style = AttendanceUx2.text(12).copy(fontFamily = RodadaVisual.Number), color = RodadaVisual.Muted)
                                }
                                Ux2Quantity(lines.sumOf { it.quantity }, !locked && lines.size == 1, selectable,
                                    { lines.singleOrNull()?.let { onQuantity(it.lineId, -1) } },
                                    { if (product.variants.isNotEmpty() || product.modifierGroups.isNotEmpty()) { editing = null; configuring = product } else onAdd(product, product.defaults()) }, product.name)
                            }
                            if (!product.active || product.availability != "AVAILABLE") Text("Indisponível", color = RodadaVisual.Amber, style = AttendanceUx2.text(12))
                            if (lines.size > 1) TextButton(onClick = { onSection("Pedido atual") }, enabled = !locked) { Text("${lines.size} configurações · editar no resumo") }
                        }
                    }
                    if (count > 0) Ux2Action("Ver resumo · $count itens · ${formatCents(total)}", !locked, { onSection("Pedido atual") })
                }
            }
            Spacer(Modifier.height(16.dp))
        }
        if (!closed && count == 0 && section == "Cardápio" && !pending) Ux2Action("Adicione itens para enviar", false, onConfirm, true)
        if (!closed && count > 0 && !pending) {
            val withinLimit = !summary.consumptionBlocked && total <= summary.remainingCapacityCents
            val valid = cart.all { it.product.active && it.product.availability == "AVAILABLE" && it.product.customizationError(it.customization) == null }
            Ux2Action("Enviar $count ${if (count == 1) "item" else "itens"} · ${formatCents(total)}", !locked && valid && withinLimit && state.connectivity == ConnectivityState.ONLINE, onConfirm, true)
        }
    }
}

@Composable internal fun Ux2Eyebrow(text: String) { Text(text.uppercase(), style = AttendanceUx2.text(10, 850).copy(letterSpacing = 1.5.sp), color = RodadaVisual.Amber) }
@Composable internal fun Ux2Title(text: String) { Text(text, style = AttendanceUx2.text(34, 900, 35.7f).copy(letterSpacing = (-1.87).sp), modifier = Modifier.semantics { heading() }) }
@Composable internal fun Ux2Action(label: String, enabled: Boolean, onClick: () -> Unit, primary: Boolean = false) {
    Button(onClick, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp), shape = RoundedCornerShape(10.dp), border = androidx.compose.foundation.BorderStroke(1.dp, if (primary) RodadaVisual.Paper else RodadaVisual.StrongBorder),
        colors = ButtonDefaults.buttonColors(containerColor = if (primary) RodadaVisual.Paper else RodadaVisual.Ground, contentColor = if (primary) RodadaVisual.Ink else RodadaVisual.Paper), contentPadding = PaddingValues(15.dp, 12.dp)) { Text(label, style = AttendanceUx2.text(if (primary) 17 else 15, 800)) }
}
@Composable internal fun Ux2Quantity(count: Int, minus: Boolean, plus: Boolean, onMinus: () -> Unit, onPlus: () -> Unit, name: String) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(7.dp)) {
        OutlinedButton(onMinus, enabled = minus && count > 0, shape = RoundedCornerShape(8.dp), border = androidx.compose.foundation.BorderStroke(1.dp, RodadaVisual.StrongBorder), colors = ButtonDefaults.outlinedButtonColors(containerColor = RodadaVisual.Control, contentColor = RodadaVisual.Paper), contentPadding = PaddingValues(0.dp), modifier = Modifier.size(44.dp).semantics { contentDescription = "Reduzir $name" }) { Text("−", style = AttendanceUx2.text(22)) }
        Text("$count", modifier = Modifier.widthIn(min = 22.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center, style = AttendanceUx2.text(14, 780).copy(fontFamily = RodadaVisual.Number))
        OutlinedButton(onPlus, enabled = plus && count < 99, shape = RoundedCornerShape(8.dp), border = androidx.compose.foundation.BorderStroke(1.dp, RodadaVisual.StrongBorder), colors = ButtonDefaults.outlinedButtonColors(containerColor = RodadaVisual.Control, contentColor = RodadaVisual.Amber), contentPadding = PaddingValues(0.dp), modifier = Modifier.size(44.dp).semantics { contentDescription = "Adicionar $name" }) { Text("+", style = AttendanceUx2.text(22)) }
    }
}
@Composable private fun Ux2DraftRow(line: CartLine, enabled: Boolean, onQuantity: (String, Int) -> Unit, onEdit: () -> Unit) {
    HorizontalDivider(color = RodadaVisual.Border)
    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text("${line.quantity}× ${line.product.name}", style = AttendanceUx2.text(16, 800))
            val configuration = line.product.configurationText(line.customization)
            if (configuration.isNotBlank()) Text(configuration, style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
            Text("${formatCents(line.unitPriceCents)} cada", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
            TextButton(onEdit, enabled = enabled, contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) { Text("Editar configuração", style = AttendanceUx2.text(13)) }
        }
        Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(9.dp)) {
            Text(formatCents(line.unitPriceCents * line.quantity), style = AttendanceUx2.text(13, 700).copy(fontFamily = RodadaVisual.Number))
            Ux2Quantity(line.quantity, enabled, enabled && line.product.active && line.product.availability == "AVAILABLE" && draftQuantityCapacity(listOf(line), line.product.id, line.customization) > 0,
                { onQuantity(line.lineId, -1) }, { onQuantity(line.lineId, 1) }, line.product.name)
        }
    }
}

@Composable
internal fun Ux2CreditBar(summary: TabSummary, draftCents: Long, onLimit: () -> Unit, enabled: Boolean, compact: Boolean = false) {
    val limit = summary.effectiveLimitCents
    val excess = (summary.exposureCents + draftCents - limit).coerceAtLeast(0)
    val warning = summary.limitWarning || (limit > 0 && summary.exposureCents + draftCents >= limit * .8)
    val color = if (summary.consumptionBlocked || excess > 0) RodadaVisual.Danger else if (warning) RodadaVisual.Amber else RodadaVisual.Success
    val relationship = summary.relationshipSnapshot?.let { when (it) { "VISITOR" -> "Visitante"; "KNOWN" -> "Conhecido"; "REGULAR" -> "Recorrente"; "HOUSE" -> "Cliente da casa"; "RESTRICTED" -> "Restrito"; else -> it } }
    val caption = when { excess > 0 -> "Pedido excede o limite em ${formatCents(excess)} · bloqueio ativo"; summary.consumptionBlocked -> "Consumo bloqueado · resolva o limite"; limit == 0L -> "Limite zero · bloqueio ativo"; warning -> "Próximo do limite operacional"; else -> "${formatCents(summary.remainingCapacityCents)} disponíveis" }
    val frame = if (compact) Modifier.fillMaxWidth() else Modifier.fillMaxWidth().background(RodadaVisual.Surface, RoundedCornerShape(11.dp)).border(1.dp, RodadaVisual.StrongBorder, RoundedCornerShape(11.dp)).drawBehind { drawRect(color, size = Size(3.dp.toPx(), size.height)) }.padding(14.dp)
    Column(frame, verticalArrangement = Arrangement.spacedBy(if (compact) 5.dp else 10.dp)) {
        if (compact) {
            val heading = @Composable { Text(relationship?.let { "Limite · $it" } ?: "Limite operacional", style = AttendanceUx2.text(12), color = RodadaVisual.Muted) }
            val amounts = @Composable { Text("${formatCents(summary.exposureCents)} / ${formatCents(limit)}", style = AttendanceUx2.text(12, 750).copy(fontFamily = RodadaVisual.Number)) }
            if (LocalDensity.current.fontScale > 1.3f) { heading(); amounts() } else Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { heading(); amounts() }
        } else {
            val heading = @Composable { Text("Referência de consumo", style = AttendanceUx2.text(12, 850)) }
            val profile = @Composable { relationship?.let { Text(it, style = AttendanceUx2.text(11, 720), color = RodadaVisual.Muted) } }
            if (LocalDensity.current.fontScale > 1.3f) { heading(); profile() }
            else Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { heading(); profile() }
            Text("${formatCents(summary.exposureCents)} de ${formatCents(limit)} usados", style = AttendanceUx2.text(18, 830).copy(fontFamily = RodadaVisual.Number))
            Text("${formatCents(summary.remainingCapacityCents)} disponíveis", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
        }
        val current = if (limit > 0) (summary.exposureCents.toFloat() / limit).coerceIn(0f, 1f) else 0f
        val draft = if (limit > 0) (draftCents.toFloat() / limit).coerceIn(0f, 1f - current) else 0f
        Canvas(Modifier.fillMaxWidth().height(if (compact) 5.dp else 10.dp).clip(RoundedCornerShape(100.dp)).semantics { contentDescription = "Consumo ${formatCents(summary.exposureCents)} de ${formatCents(limit)}; novo pedido ${formatCents(draftCents)}"; progressBarRangeInfo = ProgressBarRangeInfo(current, 0f..1f) }) {
            drawRect(RodadaVisual.Border)
            drawRect(color, size = Size(size.width * current, size.height))
            val start = size.width * current
            val end = start + size.width * draft
            if (end > start) clipRect(left = start, right = end) {
                drawRect(RodadaVisual.Amber, topLeft = Offset(start, 0f), size = Size(end - start, size.height))
                var x = start - size.height
                while (x < end + size.height) { drawLine(RodadaVisual.StrongBorder, Offset(x, size.height), Offset(x + size.height, 0f), strokeWidth = 3.dp.toPx()); x += 9.dp.toPx() }
            }
            drawLine(RodadaVisual.Paper, Offset(size.width * .8f, 0f), Offset(size.width * .8f, size.height), strokeWidth = 2.dp.toPx())
        }
        if (!compact) {
            Text(if (limit > 0) "${((summary.exposureCents.toDouble() / limit) * 100).toInt()}% utilizado${if (draftCents > 0) " · pedido em listras" else ""}" else "Limite zero", style = AttendanceUx2.text(11), color = RodadaVisual.Muted)
            if (draftCents > 0) Text("＋ ${formatCents(draftCents)} no pedido", style = AttendanceUx2.text(11, 800), color = RodadaVisual.Amber)
        }
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(caption, modifier = Modifier.weight(1f), style = AttendanceUx2.text(if (compact) 11 else 12), color = if (excess > 0) RodadaVisual.Danger else RodadaVisual.Muted)
            TextButton(onLimit, enabled = enabled, contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) { Text("Detalhes ›", style = AttendanceUx2.text(11, 700), color = RodadaVisual.Muted) }
        }
    }
}

@Composable
private fun Ux2RepeatPage(review: RepeatOrderReview, enabled: Boolean, onBack: () -> Unit, onConfirm: (Map<String, Int>) -> Unit) {
    val quantities = remember(review) { mutableStateMapOf<String, Int>().apply { review.lines.forEach { put(it.original.id, it.original.quantity) } } }
    val selected = selectedRepeatedLines(review, quantities)
    BackHandler { onBack() }
    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(onBack, modifier = Modifier.heightIn(min = 44.dp)) { Text("‹ Voltar") }
            Ux2Eyebrow("Repetir pedido")
            Ux2Title("Mais uma rodada.")
            Text("Confira itens e quantidades. Confirmar envia diretamente ao bar e à cozinha.", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
            if (!enabled) Text("O contexto mudou ou está ocupado. Volte e revise novamente.", color = RodadaVisual.Amber)
            review.problems.forEach { Text(it, color = RodadaVisual.Danger) }
            if (review.excluded > 0) Text("${review.excluded} linha(s) canceladas ou sem unidades restantes não serão repetidas.")
            review.lines.forEach { line ->
                val id = line.original.id
                val quantity = quantities[id] ?: 0
                HorizontalDivider(color = RodadaVisual.Border)
                Text(line.product.name, style = AttendanceUx2.text(16, 800))
                Text(line.product.configurationText(line.customization), style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                val price = line.product.unitPrice(line.customization)
                Text("${formatCents(price)} / un.", style = AttendanceUx2.text(13).copy(fontFamily = RodadaVisual.Number))
                Ux2Quantity(quantity, enabled, enabled, { quantities[id] = (quantity - 1).coerceAtLeast(0) }, { quantities[id] = (quantity + 1).coerceAtMost(99) }, line.product.name)
                if (line.original.unitPriceCents != price || line.original.productName != line.product.name || line.original.customizationText != line.product.configurationText(line.customization)) Text("Alteração: antes ${formatCents(line.original.unitPriceCents)} / un. Confira descrição e valor atuais.", style = AttendanceUx2.text(12), color = RodadaVisual.Amber)
            }
            Text("Quantidade zero exclui o item desta rodada.", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
        }
        val total = selected?.sumOf { it.line.product.unitPrice(it.line.customization) * it.quantity } ?: 0L
        Ux2Action("Confirmar e enviar · ${formatCents(total)}", enabled && selected != null, { if (selected != null) onConfirm(quantities.toMap()) }, true)
    }
}
