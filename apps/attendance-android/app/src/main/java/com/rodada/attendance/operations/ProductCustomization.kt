package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog

data class ProductVariant(val id: String, val name: String, val priceCents: Long, val available: Boolean, val isDefault: Boolean)
data class ModifierOption(val id: String, val name: String, val deltaCents: Long, val available: Boolean, val defaultSelected: Boolean, val kind: String)
data class ModifierGroup(val id: String, val name: String, val min: Int, val max: Int, val single: Boolean, val options: List<ModifierOption>)
data class Customization(val variantId: String? = null, val optionIds: List<String> = emptyList(), val note: String = "")
fun Product.defaults() = Customization(variants.firstOrNull { it.isDefault && it.available }?.id,
    modifierGroups.flatMap { g -> g.options.filter { it.defaultSelected && it.available }.take(g.max).map { it.id } })
fun Product.customizationError(selection: Customization): String? {
    if (variants.isNotEmpty() && variants.none { it.id == selection.variantId && it.available }) return "Escolha uma variação disponível."
    if (selection.optionIds.any { id -> modifierGroups.flatMap { it.options }.none { it.id == id && it.available } }) return "Uma opção ficou indisponível. Revise o item."
    for (g in modifierGroups) {
        val count = g.options.count { it.id in selection.optionIds }
        if (count < g.min || count > g.max || (g.single && count > 1)) return "${g.name}: selecione de ${g.min} a ${g.max}."
    }
    return null
}
fun Product.unitPrice(selection: Customization): Long = (variants.firstOrNull { it.id == selection.variantId }?.priceCents ?: priceCents) + modifierGroups.flatMap { it.options }.filter { it.id in selection.optionIds }.sumOf { it.deltaCents }
fun Product.configurationText(selection: Customization): String = buildList {
    variants.firstOrNull { it.id == selection.variantId }?.let { add(it.name) }
    modifierGroups.forEach { g -> g.options.filter { it.id in selection.optionIds }.forEach { add(if (it.kind == "ADD") "+ ${it.name}" else if (it.kind == "REMOVE") "− ${it.name}" else "${g.name}: ${it.name}") } }
    if (selection.note.isNotBlank()) add("Observação: ${selection.note}")
}.joinToString("\n")

@Composable
fun ProductCustomizationSheet(product: Product, initial: Customization = product.defaults(), onDismiss: () -> Unit,
    quantity: Int? = null, validationQuantity: Int? = quantity, onQuantityChange: (Int) -> Unit = {}, capacity: (Customization) -> Int = { 99 },
    locked: Boolean = false, canSubmit: Boolean = true, onAdd: (Customization) -> Unit) {
    var selection by remember(product.id) { mutableStateOf(initial) }
    var showOptions by remember(product.id) { mutableStateOf(quantity == null || product.customizationError(initial) != null) }
    val error = product.customizationError(selection)
    val quantityValid = validationQuantity == null || validationQuantity in 1..minOf(99, capacity(selection))
    val maxHeight = LocalConfiguration.current.screenHeightDp.dp * .9f
    Dialog(onDismissRequest = { if (!locked) onDismiss() }) {
        Surface(Modifier.heightIn(max = maxHeight).imePadding(), shape = MaterialTheme.shapes.medium) {
            Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(product.name, style = MaterialTheme.typography.titleLarge)
                if (quantity != null) {
                    Text("Quantidade", style = MaterialTheme.typography.titleMedium)
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        TextButton(onClick = { onQuantityChange(quantity - 1) }, enabled = !locked && quantity > 1,
                            modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = "Diminuir quantidade escolhida" }) { Text("−") }
                        Text("$quantity", modifier = Modifier.padding(12.dp).testTag("chosen-quantity"))
                        TextButton(onClick = { onQuantityChange(quantity + 1) }, enabled = !locked && quantity < minOf(99, capacity(selection)),
                            modifier = Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp).semantics { contentDescription = "Aumentar quantidade escolhida" }) { Text("+") }
                    }
                    OutlinedButton(onClick = { showOptions = !showOptions }, enabled = !locked,
                        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(if (showOptions) "Recolher personalização" else "Personalizar") }
                }
                if (showOptions) {
                if (product.variants.isNotEmpty()) Text("Variação · obrigatória")
                product.variants.forEach { v ->
                    OutlinedButton(onClick = { selection = selection.copy(variantId = v.id) }, enabled = !locked && v.available, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                        Text("${if (selection.variantId == v.id) "✓ " else ""}${v.name} · ${formatCents(v.priceCents)}${if (!v.available) " · Indisponível" else ""}")
                    }
                }
                product.modifierGroups.forEach { group ->
                    Text("${group.name} · ${if (group.min > 0) "obrigatório" else "opcional"} (${group.min}–${group.max})")
                    group.options.forEach { option ->
                        OutlinedButton(onClick = {
                            val next = if (option.id in selection.optionIds) selection.optionIds - option.id else if (group.single) selection.optionIds.filterNot { id -> group.options.any { it.id == id } } + option.id else selection.optionIds + option.id
                            selection = selection.copy(optionIds = next)
                        }, enabled = !locked && option.available, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                            Text("${if (option.id in selection.optionIds) "✓ " else ""}${option.name}${if (option.deltaCents > 0) " + ${formatCents(option.deltaCents)}" else ""}${if (!option.available) " · Indisponível" else ""}")
                        }
                    }
                }
                val unavailableIds = selection.optionIds.filter { id -> product.modifierGroups.flatMap { it.options }.none { it.id == id && it.available } }
                if (unavailableIds.isNotEmpty()) OutlinedButton(onClick = { selection = selection.copy(optionIds = selection.optionIds - unavailableIds.toSet()) }, modifier = Modifier.fillMaxWidth()) { Text("Remover escolhas indisponíveis") }
                OutlinedTextField(value = selection.note, onValueChange = { selection = selection.copy(note = it.take(500)) }, label = { Text("Pedido especial (opcional)") }, enabled = !locked, modifier = Modifier.fillMaxWidth())
                }
                if (!quantityValid) Text("Máximo de 99 unidades por configuração. Revise a quantidade.", color = MaterialTheme.colorScheme.error)
                if (!canSubmit) Text("Produto indisponível ou catálogo desatualizado.", color = MaterialTheme.colorScheme.error)
                if (error != null) Text(error, color = MaterialTheme.colorScheme.error)
                Button(onClick = { onAdd(selection) }, enabled = !locked && canSubmit && quantityValid && error == null, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Adicionar · ${formatCents(product.unitPrice(selection) * (quantity ?: 1))}") }
                TextButton(onClick = onDismiss, enabled = !locked, modifier = Modifier.fillMaxWidth()) { Text("Voltar") }
            }
        }
    }
}
