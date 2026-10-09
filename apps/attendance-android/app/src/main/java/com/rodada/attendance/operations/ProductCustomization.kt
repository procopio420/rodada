package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
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
fun ProductCustomizationSheet(product: Product, initial: Customization = product.defaults(), onDismiss: () -> Unit, onAdd: (Customization) -> Unit) {
    var selection by remember(product.id) { mutableStateOf(initial) }
    val error = product.customizationError(selection)
    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = MaterialTheme.shapes.medium) {
            Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(product.name, style = MaterialTheme.typography.titleLarge)
                if (product.variants.isNotEmpty()) Text("Variação · obrigatória")
                product.variants.forEach { v ->
                    OutlinedButton(onClick = { selection = selection.copy(variantId = v.id) }, enabled = v.available, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                        Text("${if (selection.variantId == v.id) "✓ " else ""}${v.name} · ${formatCents(v.priceCents)}${if (!v.available) " · Indisponível" else ""}")
                    }
                }
                product.modifierGroups.forEach { group ->
                    Text("${group.name} · ${if (group.min > 0) "obrigatório" else "opcional"} (${group.min}–${group.max})")
                    group.options.forEach { option ->
                        OutlinedButton(onClick = {
                            val next = if (option.id in selection.optionIds) selection.optionIds - option.id else if (group.single) selection.optionIds.filterNot { id -> group.options.any { it.id == id } } + option.id else selection.optionIds + option.id
                            selection = selection.copy(optionIds = next)
                        }, enabled = option.available, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                            Text("${if (option.id in selection.optionIds) "✓ " else ""}${option.name}${if (option.deltaCents > 0) " + ${formatCents(option.deltaCents)}" else ""}${if (!option.available) " · Indisponível" else ""}")
                        }
                    }
                }
                OutlinedTextField(value = selection.note, onValueChange = { selection = selection.copy(note = it.take(500)) }, label = { Text("Pedido especial (opcional)") }, modifier = Modifier.fillMaxWidth())
                if (error != null) Text(error, color = MaterialTheme.colorScheme.error)
                Button(onClick = { onAdd(selection) }, enabled = error == null, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Adicionar · ${formatCents(product.unitPrice(selection))}") }
                TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Voltar") }
            }
        }
    }
}
