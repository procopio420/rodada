package com.rodada.attendance.operations

import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class Ux2TabPagesTest {
    @get:Rule val compose = createComposeRule()
    private val product = Product("p", "Água", 500, true, "BAR", "AVAILABLE")
    private val tab = TabDetail(TabSummary("tab", "Teste", "OPEN", 1, 1000, 0, 1000, relationshipSnapshot = "HOUSE"), emptyList())

    @Test fun homeOpensCatalogAndReviewIgnoresSearch() {
        var sends = 0
        compose.setContent {
            var section by remember { mutableStateOf("Comanda") }
            RodadaTheme { Surface {
                Ux2TabPages(OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 2)), connectivity = ConnectivityState.ONLINE), tab,
                    section, { section = it }, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, { sends++ }, { _, _ -> }, {})
            } }
        }
        captureCriticalEvidence(compose, "ux2-tab-home", compose.onRoot())
        compose.onNodeWithText("＋ Adicionar itens").assertIsDisplayed().performClick()
        captureCriticalEvidence(compose, "ux2-tab-catalog", compose.onRoot())
        compose.onNode(hasSetTextAction()).performTextInput("inexistente")
        compose.onNodeWithText("Nenhum produto corresponde à pesquisa.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Ver resumo · 2 itens · ${formatCents(1000)}").performScrollTo().performClick()
        compose.onNodeWithText("2× Água").performScrollTo().assertIsDisplayed()
        captureCriticalEvidence(compose, "ux2-tab-review", compose.onRoot())
        assertEquals(0, sends)
        compose.onNodeWithText("Enviar 2 itens · ${formatCents(1000)}").performClick()
        assertEquals(1, sends)
    }

    @Test fun pendingLocksEditingAndOnlyReplaysOriginalCallback() {
        var sends = 0
        compose.setContent { RodadaTheme { Surface {
            Ux2TabPages(OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 2)), connectivity = ConnectivityState.ONLINE, orderIntentId = "immutable", noticeMessage = "Enviando pedido..."), tab,
                "Pedido atual", {}, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, { sends++ }, { _, _ -> }, {})
        } } }
        compose.onNodeWithText("Enviando pedido...").assertDoesNotExist()
        compose.onNodeWithText("Editar configuração").assertDoesNotExist()
        compose.onNodeWithContentDescription("Adicionar Água").assertIsNotEnabled()
        compose.onNodeWithText("Verificar mesmo pedido").performScrollTo().performClick()
        assertEquals(1, sends)
    }
    @Test fun confirmedOrderUsesHistoricalStationAndLocalizedState() {
        val item = OrderItem("item", "Água", 500, 1, 500, "NEW", fulfillmentStationSnapshot = "BAR")
        val canonical = tab.copy(orders = listOf(TabOrder("real-order-id", "", listOf(item))))
        compose.setContent { RodadaTheme { Surface {
            Ux2TabPages(OperationsUiState(products = listOf(product.copy(fulfillmentStation = "KITCHEN")), connectivity = ConnectivityState.ONLINE), canonical,
                "Comanda", {}, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, {}, { _, _ -> }, {})
        } } }
        compose.onNodeWithText("Pedido real-order-id confirmado").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Bar · Na fila").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Cozinha · Na fila").assertDoesNotExist()
    }

    @Test fun filtersAndSectionSurviveTabSwitchAndLeavingWorkspace() {
        compose.setContent {
            var selectedId by remember { mutableStateOf<String?>("A") }
            val contexts = androidx.compose.runtime.saveable.rememberSaveableStateHolder()
            RodadaTheme { Surface {
                Column(Modifier.fillMaxSize()) {
                    Row {
                        listOf("A", "B", "Mesas").forEach { name -> TextButton({ selectedId = name.takeUnless { it == "Mesas" } }) { Text(name) } }
                    }
                    selectedId?.let { id -> contexts.SaveableStateProvider("tab:$id") {
                        val selected = tab.copy(summary = tab.summary.copy(id = id))
                        TabWorkspace(state = OperationsUiState(products = listOf(product), selectedTab = selected, connectivity = ConnectivityState.ONLINE), tab = selected,
                            onBack = { selectedId = null }, onAdd = { _, _ -> }, onEdit = { _, _ -> }, onQuantity = { _, _ -> }, onConfirmOrder = {},
                            onPay = {}, onClose = {}, onAdjustPricing = {}, onOperations = {}, onResolveLimit = {}, onCorrectItem = {}, onRefundPayment = {}, onSettleCorrection = {})
                    } }
                }
            } }
        }
        compose.onNodeWithText("＋ Adicionar itens").performClick()
        compose.onNode(hasSetTextAction()).performTextInput("inexistente")
        compose.onNodeWithText("Mesas").performClick()
        compose.onNodeWithText("B").performClick()
        compose.onNodeWithText("＋ Adicionar itens").performClick()
        compose.onNode(hasSetTextAction()).assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("")))
        compose.onNodeWithText("Mesas").performClick()
        compose.onNodeWithText("A").performClick()
        compose.onNode(hasSetTextAction()).assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("inexistente")))
        compose.onNodeWithText("Nenhum produto corresponde à pesquisa.").performScrollTo().assertIsDisplayed()
    }

    @Test fun unknownRepeatWithEmptyCartVerifiesWithoutSubmittingDraft() {
        var confirms = 0
        var verifications = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(state = OperationsUiState(selectedTab = tab, orderIntentId = "original-repeat-key", connectivity = ConnectivityState.STALE), tab = tab,
                onBack = {}, onAdd = { _, _ -> }, onEdit = { _, _ -> }, onQuantity = { _, _ -> }, onConfirmOrder = { confirms++ }, onVerifyPending = { verifications++ },
                onPay = {}, onClose = {}, onAdjustPricing = {}, onOperations = {}, onResolveLimit = {}, onCorrectItem = {}, onRefundPayment = {}, onSettleCorrection = {})
        } } }
        compose.onNodeWithText("Verificar mesmo pedido").performScrollTo().performClick()
        assertEquals(1, verifications)
        assertEquals(0, confirms)
        compose.onNodeWithText("Trocar de mesa ou comanda").performScrollTo().assertIsNotEnabled()
    }

    @Test fun accountRoundTripPreservesCatalogSearchAndCategory() {
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(state = OperationsUiState(products = listOf(product, product.copy(id = "coffee", name = "Café", category = "Bebidas")), selectedTab = tab, connectivity = ConnectivityState.ONLINE), tab = tab,
                onBack = {}, onAdd = { _, _ -> }, onEdit = { _, _ -> }, onQuantity = { _, _ -> }, onConfirmOrder = {},
                onPay = {}, onClose = {}, onAdjustPricing = {}, onOperations = {}, onResolveLimit = {}, onCorrectItem = {}, onRefundPayment = {}, onSettleCorrection = {})
        } } }
        compose.onNodeWithText("＋ Adicionar itens").performClick()
        compose.onNodeWithText("Outros").performClick()
        compose.onNode(hasSetTextAction()).performTextInput("inexistente")
        compose.onNodeWithText("‹  Voltar").performScrollTo().performClick()
        compose.onNodeWithText("Conferir / fechar conta").performScrollTo().performClick()
        compose.onNodeWithText("← Voltar à comanda").performClick()
        compose.onNodeWithText("＋ Adicionar itens").performScrollTo().performClick()
        compose.onNode(hasSetTextAction()).assert(SemanticsMatcher.expectValue(androidx.compose.ui.semantics.SemanticsProperties.EditableText, androidx.compose.ui.text.AnnotatedString("inexistente")))
        compose.onNode(hasSetTextAction()).performTextClearance()
        compose.onNodeWithText("Água").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Café").assertDoesNotExist()
    }

    /** Same presentation data as PR212; isolated Compose, no API mutation evidence. */
    @Test fun prototypeMarinaCatalogAndSummary() {
        val names = listOf("Chopp Pilsen", "Água sem gás", "Refrigerante lata", "Suco de laranja", "Batata frita", "Polenta frita", "Pastel de queijo", "Hambúrguer da casa")
        val prices = listOf(1400L, 600L, 800L, 1200L, 2800L, 2600L, 1600L, 3400L)
        val products = names.mapIndexed { index, name -> Product("p${index + 1}", name, prices[index], true,
            if (index < 4) "BAR" else "KITCHEN", "AVAILABLE", category = if (index < 4) "Bebidas" else if (index < 7) "Porções" else "Lanches") }
        val marina = TabDetail(TabSummary("1048", "Marina", "OPEN", 1, 5600, 0, 5600,
            effectiveLimitCents = 20000, remainingCapacityCents = 14400, tableLabel = "08", relationshipSnapshot = "REGULAR"), emptyList())
        compose.setContent {
            var section by remember { mutableStateOf("Cardápio") }
            RodadaTheme { Surface { Ux2TabPages(OperationsUiState(products = products, cart = listOf(CartLine(products.first(), 1)), connectivity = ConnectivityState.ONLINE),
                marina, section, { section = it }, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, {}, { _, _ -> }, {}) } }
        }
        captureCriticalEvidence(compose, "prototype-marina-catalog", compose.onRoot())
        compose.onNodeWithText("Ver resumo · 1 itens · ${formatCents(1400)}").performScrollTo().performClick()
        compose.onNodeWithText("Editar configuração").assertDoesNotExist()
        compose.onNodeWithText("1× Chopp Pilsen").performScrollTo().assertIsDisplayed()
        captureCriticalEvidence(compose, "prototype-marina-summary", compose.onRoot())
    }

    @Test fun restoredNoteOnlyDraftRetainsEditing() {
        compose.setContent { RodadaTheme { Surface {
            Ux2TabPages(OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 1, Customization(note = "Sem gelo"))), connectivity = ConnectivityState.ONLINE), tab,
                "Pedido atual", {}, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, {}, { _, _ -> }, {})
        } } }
        compose.onNodeWithText("Editar configuração").performScrollTo().performClick()
        compose.onNode(hasSetTextAction()).assertTextContains("Sem gelo")
    }

    @Test fun quantityPaintKeepsPrototypeSizeAndExpandedTouchTarget() {
        var additions = 0
        compose.setContent { RodadaTheme { Surface {
            Ux2Quantity(1, true, true, {}, { additions++ }, "Chopp")
        } } }
        val node = compose.onNodeWithContentDescription("Adicionar Chopp")
        val bounds = node.getUnclippedBoundsInRoot()
        assertEquals(39f, (bounds.right - bounds.left).value, .1f)
        assertEquals(42f, (bounds.bottom - bounds.top).value, .1f)
        val pixels = node.fetchSemanticsNode().boundsInRoot
        // Native minimum target extends outside the 39dp painted rectangle.
        compose.onRoot().performTouchInput {
            click(androidx.compose.ui.geometry.Offset(pixels.left - 1f, pixels.center.y))
        }
        assertEquals(1, additions)
    }

}
