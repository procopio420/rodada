package com.rodada.attendance.operations

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
        compose.onNodeWithText("Buscar no cardápio").performTextInput("inexistente")
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
            Ux2TabPages(OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 2)), connectivity = ConnectivityState.ONLINE, orderIntentId = "immutable"), tab,
                "Pedido atual", {}, {}, { _, _ -> }, { _, _ -> }, { _, _ -> }, { sends++ }, { _, _ -> }, {})
        } } }
        compose.onNodeWithText("Editar configuração").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithContentDescription("Adicionar Água").assertIsNotEnabled()
        compose.onNodeWithText("Verificar mesmo pedido").performScrollTo().performClick()
        assertEquals(1, sends)
    }
}
