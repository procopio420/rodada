package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class RepeatOrderDialogTest {
    @get:Rule val compose = createComposeRule()
    private val product = Product("product", "Água", 1000, true, "BAR", "AVAILABLE")
    private val item = OrderItem("item", "Água", 800, 2, 1600, "DELIVERED", productId = "product", customization = Customization())
    private val review = reviewRepeatedOrder(TabOrder("order", "", listOf(item)), listOf(product))

    @Test fun reviewRequiresExplicitAddAndShowsPriceChange() {
        var added = 0
        compose.setContent { RodadaTheme { Surface { RepeatOrderDialog(review, true, {}, { _ -> added++ }) } } }
        compose.onNodeWithText("Alteração: antes ${formatCents(800)} / un. Confira o valor e a descrição atuais.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("${formatCents(1000)} / un.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Alteração: antes ${formatCents(800)} / un. Confira o valor e a descrição atuais.").performScrollTo().assertIsDisplayed()
        val addBounds = compose.onNodeWithText("Confirmar e enviar rodada").fetchSemanticsNode().boundsInRoot
        val cancelBounds = compose.onNodeWithText("Cancelar").fetchSemanticsNode().boundsInRoot
        org.junit.Assert.assertTrue("Ações devem ocupar regiões separadas", addBounds.bottom <= cancelBounds.top)
        captureCriticalEvidence(compose, "repeat-order", compose.onNode(isDialog()))
        assertEquals(0, added)
        compose.onNodeWithText("Confirmar e enviar rodada").assertIsEnabled().performClick()
        assertEquals(1, added)
    }
    @Test fun blockedConfigurationAndStaleContextCannotAddAndCancelHasNoMutation() {
        var added = 0
        var dismissed = 0
        val blocked = reviewRepeatedOrder(TabOrder("order", "", listOf(item.copy(customization = Customization(optionIds = listOf("removed"))))), listOf(product))
        compose.setContent { RodadaTheme { Surface { RepeatOrderDialog(blocked, false, { dismissed++ }, { _ -> added++ }) } } }
        compose.onNodeWithText("Confirmar e enviar rodada").assertIsNotEnabled()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(0, added)
        assertEquals(1, dismissed)
    }

    @Test fun checkboxAndQuantityEditorControlExactlyWhatIsAdded() {
        var selected: Map<String, Int>? = null
        compose.setContent { RodadaTheme { Surface { RepeatOrderDialog(review, true, {}, { selected = it }) } } }
        compose.onNode(isToggleable()).performClick()
        compose.onNodeWithText("Confirmar e enviar rodada").assertIsNotEnabled()
        compose.onNode(isToggleable()).performClick()
        compose.onNode(hasSetTextAction()).performTextReplacement("1")
        compose.onNodeWithText("Selecionados: 1 unidade(s) · ${formatCents(1000)}").assertExists()
        compose.onNodeWithText("Confirmar e enviar rodada").assertIsEnabled().performClick()
        assertEquals(mapOf(item.id to 1), selected)
    }

    @Test fun historyActionSendsSelectedRoundWithoutAddingItToCart() {
        val tab = TabSummary("tab", "Comanda", "OPEN", 1, 1600, 0, 1600)
        val order = TabOrder("order", "", listOf(item))
        val draft = CartLine(product, 1)
        val ui = androidx.compose.runtime.mutableStateOf(OperationsUiState(products = listOf(product),
            selectedTab = TabDetail(tab, listOf(order)), cart = listOf(draft), connectivity = ConnectivityState.ONLINE))
        var sent = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(ui.value, ui.value.selectedTab!!, {}, { _, _ -> }, { _, _ -> }, { _, _ -> },
                {}, {}, {}, {}, {}, {}, {}, {}, {},
                onRepeatOrder = { review, quantities ->
                    assertEquals(listOf(PendingOrderLine(product.id, 2)), ui.value.repeatedOrderLines(tab.id, review, quantities))
                    sent++
                })
        } } }
        compose.onNodeWithTag("workspace-Conta").performClick()
        compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Mais uma rodada"))
        compose.onNodeWithText("Mais uma rodada").performClick()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(listOf(draft), ui.value.cart)
        compose.onNodeWithText("Mais uma rodada").performClick()
        compose.onNodeWithText("Confirmar e enviar rodada").performClick()
        assertEquals(listOf(draft), ui.value.cart)
        assertEquals(1, sent)
    }
}
