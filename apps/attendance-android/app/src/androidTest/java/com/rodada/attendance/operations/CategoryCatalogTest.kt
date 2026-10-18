package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class CategoryCatalogTest {
    @get:Rule val compose = createComposeRule()
    private val product = Product("fixture-product", "Produto do catálogo", 800, true, "BAR", "AVAILABLE", category = "Bebidas")
    @Test fun allIncludesMultipleCategoriesAndRespectsSearch() {
        val second = product.copy(id = "fixture-food", name = "Porção do catálogo", category = "Porções")
        compose.setContent { RodadaTheme { Surface {
            CategoryCatalog(OperationsUiState(products = listOf(product, second), connectivity = ConnectivityState.ONLINE), "tab-fixture", false, { _, _, _ -> }, {})
        } } }
        compose.onNodeWithTag("catalog-category-all").assertTextContains("2 itens").performClick()
        compose.onNodeWithText(product.name).assertExists()
        compose.onNodeWithText(second.name).assertExists()
        compose.onNodeWithText("Voltar às categorias").performClick()
        compose.onNodeWithText("Buscar no catálogo").performTextInput(second.name)
        compose.onNodeWithTag("catalog-category-all").assertTextContains("1 itens").performClick()
        compose.onNode(hasText(second.name) and hasAnyAncestor(hasTestTag("category-products"))).assertExists()
        compose.onNode(hasText(product.name) and hasAnyAncestor(hasTestTag("category-products"))).assertDoesNotExist()
    }
    @Test fun categoryThenProductThenQuantityAndCustomizationOnlyChangesDraftOnAdd() {
        val state = mutableStateOf(OperationsUiState(products = listOf(product), connectivity = ConnectivityState.ONLINE))
        var reviewed = 0
        compose.setContent { androidx.compose.ui.window.Dialog(onDismissRequest = {}) { RodadaTheme { Surface {
            CategoryCatalog(state.value, "tab-fixture", false, { p, s, q -> state.value = state.value.copy(cart = addDraftQuantity(state.value.cart, p, s, q)!!) }, { reviewed++ })
        } } } }
        compose.onNodeWithText(product.name).assertDoesNotExist()
        compose.onNodeWithText("Buscar no catálogo").performTextInput(product.name)
        captureCriticalEvidence(compose, "category-home", compose.onNode(isDialog()))
        compose.onNodeWithTag("catalog-category-Bebidas").performClick()
        captureCriticalEvidence(compose, "category-products", compose.onAllNodes(isDialog()).onLast())
        compose.onNode(hasText(product.name) and hasClickAction() and hasAnyAncestor(hasTestTag("category-products"))).performClick()
        assertTrue(state.value.cart.isEmpty())
        compose.onNodeWithContentDescription("Aumentar quantidade escolhida").performClick().performClick()
        compose.onNodeWithTag("chosen-quantity").assertTextEquals("3")
        captureCriticalEvidence(compose, "category-quantity", compose.onAllNodes(isDialog()).onLast())
        compose.onNodeWithText("Personalizar", substring = false).performClick()
        compose.onNodeWithText("Pedido especial (opcional)").performTextInput("Separado")
        compose.onNodeWithText("Adicionar · ${formatCents(2400)}").performScrollTo().performClick()
        assertEquals(3, state.value.cart.single().quantity)
        assertEquals("Separado", state.value.cart.single().customization.note)
        compose.onNodeWithText("Ver pedido atual · 3 itens").performClick()
        assertEquals(1, reviewed)
    }
    @Test fun cancelAndCatalogChangeNeverInsertOrEnableAnUnavailableProduct() {
        val state = mutableStateOf(OperationsUiState(products = listOf(product), connectivity = ConnectivityState.ONLINE))
        var added = 0
        compose.setContent { RodadaTheme { Surface {
            CategoryCatalog(state.value, "tab-fixture", false, { _, _, _ -> added++ }, {})
        } } }
        compose.onNodeWithTag("catalog-category-Bebidas").performClick()
        compose.onNode(hasText(product.name) and hasClickAction() and hasAnyAncestor(hasTestTag("category-products"))).performClick()
        compose.onNodeWithText("Voltar", substring = false).performScrollTo().performClick()
        assertEquals(0, added)
        compose.onNode(hasText(product.name) and hasClickAction() and hasAnyAncestor(hasTestTag("category-products"))).performClick()
        compose.runOnIdle { state.value = state.value.copy(products = listOf(product.copy(availability = "UNAVAILABLE"))) }
        compose.onNodeWithText("Adicionar · ${formatCents(800)}").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText("Produto indisponível ou catálogo desatualizado.").assertExists()
        assertEquals(0, added)
    }
}
