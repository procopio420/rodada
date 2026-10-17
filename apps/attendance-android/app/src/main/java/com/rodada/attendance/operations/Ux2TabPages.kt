package com.rodada.attendance.operations

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
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
) {
    val summary = tab.summary
    val closed = summary.state in setOf("CLOSED", "CANCELLED")
    val locked = !state.canLeaveTabContext() || state.queuedOrders.any { it.tabId == summary.id }
    val cart = state.cart.map { it.copy(product = state.products.firstOrNull { p -> p.id == it.product.id } ?: it.product.copy(active = false)) }
    val total = cart.sumOf { it.unitPriceCents * it.quantity }
    val count = cart.sumOf { it.quantity }
    val pending = state.orderIntentId != null || state.queuedOrders.any { it.tabId == summary.id }
    var query by rememberSaveable(summary.id) { mutableStateOf("") }
    var category by rememberSaveable(summary.id) { mutableStateOf("Todos") }
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
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(13.dp)) {
            TextButton(onClick = back, enabled = !locked, contentPadding = PaddingValues(0.dp), modifier = Modifier.heightIn(min = 44.dp)) { Text("‹  Voltar", style = AttendanceUx2.text(14), color = RodadaVisual.Muted) }
            Ux2Eyebrow(if (section == "Comanda") summary.operationalReference() else if (section == "Pedido atual") "Resumo opcional" else "Pedido para ${summary.operationalReference()}")
            Ux2Title(when (section) { "Comanda" -> summary.displayLabel; "Pedido atual" -> "Resumo do pedido."; else -> "Adicionar itens." })
            Text(if (section == "Comanda") "${summary.tableLabel?.let { "Mesa $it" } ?: "Sem mesa"} · ${if (closed) "Encerrada" else "Comanda aberta"}" else "${summary.displayLabel} · ${summary.tableLabel?.let { "Mesa $it" } ?: "Sem mesa"} · destino fixo", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
            if (state.connectivity != ConnectivityState.ONLINE) Text(state.connectivity.label(), style = AttendanceUx2.text(12), color = RodadaVisual.Amber)
            state.errorMessage?.let { Text(it, color = RodadaVisual.Danger, style = AttendanceUx2.text(14)) }
            state.noticeMessage?.let { Text(it, style = AttendanceUx2.text(14)) }
            if (pending) Ux2Action("Verificar mesmo pedido", !state.submitting && !state.loading, onConfirm, primary = true)
            if (section == "Comanda") {
                if (closed) Text("Comanda encerrada. Não é possível adicionar pedidos nem recebimentos.")
                else Ux2Action("＋ Adicionar itens", !locked, { onSection("Cardápio") }, true)
                val repeatAction = @Composable { Ux2Action("↻ Mais uma rodada", !locked && !closed && cart.isEmpty() && tab.orders.isNotEmpty(), { tab.orders.lastOrNull()?.let { repeat = reviewRepeatedOrder(it, state.products) } }) }
                val accountAction = @Composable { Ux2Action(if (closed) "Ver conta encerrada" else "Conferir / fechar conta", !locked, { onSection("Conta") }) }
                if (LocalDensity.current.fontScale > 1.3f) { repeatAction(); accountAction() }
                else Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f)) { repeatAction() }
                    Box(Modifier.weight(1f)) { accountAction() }
                }
                HorizontalDivider(color = RodadaVisual.Border)
                Text("Saldo em aberto", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                Text(formatCents(summary.exposureCents), style = AttendanceUx2.text(24, 800).copy(fontFamily = RodadaVisual.Number))
                Text("Sem incluir rascunhos não enviados", style = AttendanceUx2.text(11), color = RodadaVisual.Muted)
                Ux2CreditBar(summary, 0, onLimit, !locked)
                if (count > 0) Text("$count item(ns) não enviados. Confira o rascunho antes de encerrar.", color = RodadaVisual.Amber, style = AttendanceUx2.text(14))
                Text("Último pedido", style = AttendanceUx2.text(18, 800))
                val latest = tab.orders.lastOrNull()
                if (latest == null) Text("Nenhum pedido anterior.", style = AttendanceUx2.text(14), color = RodadaVisual.Muted)
                latest?.items?.forEach { item ->
                    HorizontalDivider(color = RodadaVisual.Border)
                    Text("${item.quantity}× ${item.productName}", style = AttendanceUx2.text(16, 820))
                    Text(item.state, style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
                }
                Ux2Action("Trocar de mesa ou comanda", !locked, onBack)
            } else {
                Ux2CreditBar(summary, total, onLimit, !locked)
                if (section == "Pedido atual") {
                    if (cart.isEmpty()) Text("O pedido está vazio.")
                    cart.forEach { line ->
                        Ux2DraftRow(line, !locked, onQuantity) { editing = line; configuring = line.product }
                    }
                    Ux2Action("Continuar escolhendo itens", !locked, { onSection("Cardápio") })
                } else {
                    OutlinedTextField(query, { query = it }, modifier = Modifier.fillMaxWidth(), label = { Text("Buscar no cardápio", style = AttendanceUx2.text(14)) }, enabled = !locked, singleLine = true)
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        (listOf("Todos") + state.products.map { it.category.ifBlank { "Outros" } }.distinct().sorted()).forEach { name ->
                            FilterChip(selected = category == name, onClick = { category = name }, label = { Text(name, style = AttendanceUx2.text(13, 750)) }, enabled = !locked, modifier = Modifier.heightIn(min = 44.dp))
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
                            Text(product.name, style = AttendanceUx2.text(15, 800))
                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                                Text(formatCents(product.priceCents), style = AttendanceUx2.text(12).copy(fontFamily = RodadaVisual.Number), color = RodadaVisual.Muted, modifier = Modifier.weight(1f))
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
    Button(onClick, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp), shape = RoundedCornerShape(10.dp), border = androidx.compose.foundation.BorderStroke(1.dp, if (primary) RodadaVisual.Paper else RodadaVisual.StrongBorder),
        colors = ButtonDefaults.buttonColors(containerColor = if (primary) RodadaVisual.Paper else RodadaVisual.Ground, contentColor = if (primary) RodadaVisual.Ink else RodadaVisual.Paper), contentPadding = PaddingValues(15.dp, 12.dp)) { Text(label, style = AttendanceUx2.text(if (primary) 17 else 15, 800)) }
}
@Composable internal fun Ux2Quantity(count: Int, minus: Boolean, plus: Boolean, onMinus: () -> Unit, onPlus: () -> Unit, name: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        TextButton(onMinus, enabled = minus && count > 0, modifier = Modifier.sizeIn(minWidth = 44.dp, minHeight = 44.dp).semantics { contentDescription = "Reduzir $name" }) { Text("−", style = AttendanceUx2.text(22)) }
        Text("$count", style = AttendanceUx2.text(14, 800).copy(fontFamily = RodadaVisual.Number))
        TextButton(onPlus, enabled = plus && count < 99, modifier = Modifier.sizeIn(minWidth = 44.dp, minHeight = 44.dp).semantics { contentDescription = "Adicionar $name" }) { Text("+", style = AttendanceUx2.text(22), color = RodadaVisual.Amber) }
    }
}
@Composable private fun Ux2DraftRow(line: CartLine, enabled: Boolean, onQuantity: (String, Int) -> Unit, onEdit: () -> Unit) {
    HorizontalDivider(color = RodadaVisual.Border)
    Column {
        Text("${line.quantity}× ${line.product.name}", style = AttendanceUx2.text(16, 800))
        Text(line.product.configurationText(line.customization), style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
        Text(formatCents(line.unitPriceCents * line.quantity), style = AttendanceUx2.text(14, 800).copy(fontFamily = RodadaVisual.Number))
        Ux2Quantity(line.quantity, enabled, enabled && line.product.active && line.product.availability == "AVAILABLE" && draftQuantityCapacity(listOf(line), line.product.id, line.customization) > 0,
            { onQuantity(line.lineId, -1) }, { onQuantity(line.lineId, 1) }, line.product.name)
        TextButton(onEdit, enabled = enabled) { Text("Editar configuração", style = AttendanceUx2.text(13)) }
    }
}

@Composable
private fun Ux2CreditBar(summary: TabSummary, draftCents: Long, onLimit: () -> Unit, enabled: Boolean) {
    Column(Modifier.fillMaxWidth().border(1.dp, RodadaVisual.Border, RoundedCornerShape(10.dp)).padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        summary.relationshipSnapshot?.let { kind ->
            val label = when (kind) { "VISITOR" -> "Visitante"; "KNOWN" -> "Conhecido"; "RESTRICTED" -> "Restrito"; "REGULAR" -> "Recorrente"; "HOUSE" -> "Cliente da casa"; else -> kind }
            Text("Perfil · $label", style = AttendanceUx2.text(12, 750), color = RodadaVisual.Muted)
        }
        Text("Limite operacional · ${formatCents(summary.effectiveLimitCents)}", style = AttendanceUx2.text(13, 750))
        val used = summary.percentageUsed ?: if (summary.effectiveLimitCents > 0) ((summary.exposureCents.toDouble() / summary.effectiveLimitCents) * 100).toInt() else 0
        LinearProgressIndicator(progress = { used.coerceIn(0, 100) / 100f }, modifier = Modifier.fillMaxWidth().height(5.dp), color = if (summary.consumptionBlocked) RodadaVisual.Danger else RodadaVisual.Amber, trackColor = RodadaVisual.Border)
        Text("Disponível ${formatCents(summary.remainingCapacityCents)} · saldo ${formatCents(summary.exposureCents)}", style = AttendanceUx2.text(12).copy(fontFamily = RodadaVisual.Number))
        if (draftCents > 0) Text("Pedido não enviado · ${formatCents(draftCents)}", style = AttendanceUx2.text(12), color = RodadaVisual.Muted)
        if (summary.consumptionBlocked || summary.limitWarning || draftCents > summary.remainingCapacityCents) {
            Text(if (summary.consumptionBlocked || draftCents > summary.remainingCapacityCents) "Consumo bloqueado. Resolva o limite antes de enviar." else "Atenção ao limite operacional.", style = AttendanceUx2.text(13), color = RodadaVisual.Amber)
            TextButton(onLimit, enabled = enabled, modifier = Modifier.heightIn(min = 44.dp)) { Text("Resolver limite") }
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
