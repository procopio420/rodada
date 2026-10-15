package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class OrderWorkspaceTest {
    @get:Rule val compose = createComposeRule()
    private val tab = TabSummary("fixture-tab", "Comanda de teste", "OPEN", 1, 3800, 1000, 2800)
    private val products = (1..146).map { Product("product-$it", "Produto $it", 800, true, "BAR", "AVAILABLE") }

    @Test fun cartIsReachableWithoutTraversingCatalogAndNavigationDoesNotSend() {
        var confirmed = 0
        var quantityChange: Pair<String, Int>? = null
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(
                OperationsUiState(products = products, cart = listOf(CartLine(products.first(), 2, lineId = "line")), connectivity = ConnectivityState.ONLINE),
                TabDetail(tab, emptyList()), {}, { _, _ -> }, { _, _ -> },
                { id, delta -> quantityChange = id to delta }, { confirmed++ },
                {}, {}, {}, {}, {}, {}, {}, {},
            )
        } } }
        compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Produto 146"))
        compose.onNodeWithText("Produto 146").assertIsDisplayed()
        compose.onNodeWithText("Ver pedido atual · 2 itens · ${formatCents(1600)}")
            .assertIsDisplayed().assertHeightIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("Confirmar pedido").assertIsDisplayed().assertIsEnabled()
        compose.onNodeWithText("+").performClick()
        assertEquals("line" to 1, quantityChange)
        captureCriticalEvidence(compose, "order-cart", compose.onRoot())
        compose.onNodeWithText("Voltar ao catálogo").assertIsDisplayed().performClick()
        compose.onNodeWithText("Produto 146").assertIsDisplayed()
        compose.onNodeWithText("Ver pedido atual · 2 itens · ${formatCents(1600)}").assertIsDisplayed()
        assertEquals(0, confirmed)
        compose.onNodeWithText("Ver pedido atual · 2 itens · ${formatCents(1600)}").performClick()
        compose.onNodeWithText("Confirmar pedido").performClick()
        assertEquals(1, confirmed)
    }

    @Test fun detailsNeverHideStaleWarningOrEnableFinancialActions() {
        var paid = 0
        var closed = 0
        compose.setContent { RodadaTheme { Surface {
            BalanceCard(tab.copy(serviceAssessmentStale = true), { paid++ }, { closed++ }, false, true)
        } } }
        compose.onNodeWithText("Subtotal original ${formatCents(3800)}").assertDoesNotExist()
        compose.onNodeWithText("Atualize a taxa de serviço no caixa antes de receber.").assertIsDisplayed()
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        compose.onNodeWithText("Fechar").assertIsNotEnabled()
        compose.onNodeWithText("Ver detalhes da conta").performClick()
        compose.onNodeWithText("Subtotal original ${formatCents(3800)}").assertIsDisplayed()
        compose.onNodeWithText("Recolher detalhes da conta").performClick()
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        assertEquals(0, paid)
        assertEquals(0, closed)
    }

    @Test fun pendingOrderKeepsEditingLockedAndExplicitReplayAvailable() {
        var confirmed = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(
                OperationsUiState(products = products, cart = listOf(CartLine(products.first(), 1)), orderIntentId = "pending"),
                TabDetail(tab, emptyList()), {}, { _, _ -> }, { _, _ -> }, { _, _ -> },
                { confirmed++ }, {}, {}, {}, {}, {}, {}, {}, {},
            )
        } } }
        compose.onNodeWithText("Ver pedido atual · 1 item · ${formatCents(800)}").performClick()
        compose.onNodeWithText("Editar").assertIsNotEnabled()
        compose.onNodeWithText("+").assertIsNotEnabled()
        compose.onNodeWithText("−").assertIsNotEnabled()
        compose.onNodeWithText("Confirmar pedido").performScrollTo().assertIsEnabled().performClick()
        assertEquals(1, confirmed)
    }

    @Test fun collapsedAccountPreservesOnlineBusyAndClosedGuards() {
        val currentTab = mutableStateOf(tab)
        val online = mutableStateOf(true)
        val busy = mutableStateOf(false)
        var paid = 0
        var closed = 0
        compose.setContent { RodadaTheme { Surface {
            BalanceCard(currentTab.value, { paid++ }, { closed++ }, busy.value, online.value)
        } } }
        compose.onNodeWithText("Pagar").assertIsEnabled()
        compose.onNodeWithText("Fechar").assertIsNotEnabled()
        compose.runOnIdle { online.value = false }
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        compose.runOnIdle { online.value = true; busy.value = true }
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        compose.runOnIdle { busy.value = false; currentTab.value = tab.copy(exposureCents = 0) }
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        compose.onNodeWithText("Fechar").assertIsEnabled()
        compose.runOnIdle { currentTab.value = currentTab.value.copy(state = "CLOSED") }
        compose.onNodeWithText("Fechada").assertIsNotEnabled()
        compose.onNodeWithText("Pagar").assertIsNotEnabled()
        assertEquals(0, paid)
        assertEquals(0, closed)
    }
}
