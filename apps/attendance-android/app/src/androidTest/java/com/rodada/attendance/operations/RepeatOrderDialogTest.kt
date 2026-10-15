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
        val addBounds = compose.onNodeWithText("Adicionar ao carrinho").fetchSemanticsNode().boundsInRoot
        val cancelBounds = compose.onNodeWithText("Cancelar").fetchSemanticsNode().boundsInRoot
        org.junit.Assert.assertTrue("Ações devem ocupar regiões separadas", addBounds.bottom <= cancelBounds.top)
        captureCriticalEvidence(compose, "repeat-order", compose.onNode(isDialog()))
        assertEquals(0, added)
        compose.onNodeWithText("Adicionar ao carrinho").assertIsEnabled().performClick()
        assertEquals(1, added)
    }
    @Test fun blockedConfigurationAndStaleContextCannotAddAndCancelHasNoMutation() {
        var added = 0
        var dismissed = 0
        val blocked = reviewRepeatedOrder(TabOrder("order", "", listOf(item.copy(customization = Customization(optionIds = listOf("removed"))))), listOf(product))
        compose.setContent { RodadaTheme { Surface { RepeatOrderDialog(blocked, false, { dismissed++ }, { _ -> added++ }) } } }
        compose.onNodeWithText("Adicionar ao carrinho").assertIsNotEnabled()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(0, added)
        assertEquals(1, dismissed)
    }

    @Test fun historyActionAddsDraftAndOpensCartWithoutSending() {
        val tab = TabSummary("tab", "Comanda", "OPEN", 1, 1600, 0, 1600)
        val order = TabOrder("order", "", listOf(item))
        val ui = androidx.compose.runtime.mutableStateOf(OperationsUiState(products = listOf(product),
            selectedTab = TabDetail(tab, listOf(order)), connectivity = ConnectivityState.ONLINE))
        var sent = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(ui.value, ui.value.selectedTab!!, {}, { _, _ -> }, { _, _ -> }, { _, _ -> },
                { sent++ }, {}, {}, {}, {}, {}, {}, {}, {},
                onRepeatOrder = { review, quantities -> ui.value = ui.value.withRepeatedOrder(tab.id, review, quantities) })
        } } }
        compose.onNode(hasScrollAction()).performScrollToNode(hasText("Mais uma rodada"))
        compose.onNodeWithText("Mais uma rodada").performClick()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(0, ui.value.cart.size)
        compose.onNodeWithText("Mais uma rodada").performClick()
        compose.onNodeWithText("Adicionar ao carrinho").performClick()
        compose.onNodeWithText("Confirmar pedido").assertIsDisplayed()
        assertEquals(2, ui.value.cart.single().quantity)
        assertEquals(0, sent)
    }
}
