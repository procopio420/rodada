package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.MainActivity
import com.rodada.attendance.BuildConfig
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Opt-in UI proof. MainActivity uses production repositories and the disposable Django stack. */
class LiveComposeOrderTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun waitText(text: String) {
        compose.waitUntil(30_000) { compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty() }
    }

    @Test fun confirmThroughProductionCompose() {
        assumeTrue("Disposable runner only", InstrumentationRegistry.getArguments().getString("liveCompose") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:8101/")
        waitText("Estabelecimento")
        compose.onNodeWithText("Estabelecimento").performTextInput("android-post-drop-ci")
        compose.onNodeWithText("Operador").performTextInput("android-post-drop-operator")
        compose.onNodeWithText("PIN").performTextInput("2468")
        compose.onNodeWithText("Entrar").performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasTestTag("attendance-order") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("attendance-order").assertIsEnabled().performClick()
        val newTab = hasText("Nova comanda sem mesa") and hasAnyAncestor(isDialog())
        compose.waitUntil(30_000) { compose.onAllNodes(newTab and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNode(newTab).assertIsEnabled().performClick()
        waitText("Nome ou apelido")
        compose.onNodeWithText("Nome ou apelido").performTextInput(InstrumentationRegistry.getArguments().getString("tabLabel") ?: error("Missing isolated run label"))
        compose.onNodeWithText("Abrir", useUnmergedTree = false).performClick()
        compose.waitUntil(30_000) { compose.onAllNodesWithTag("workspace-list").fetchSemanticsNodes().isNotEmpty() }
        for (product in listOf("Android Compose Test Meal", "Android Post Drop Test Soda")) {
            compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Buscar no catálogo"))
            compose.onNodeWithText("Buscar no catálogo").performTextReplacement(product)
            compose.onNodeWithTag("catalog-category-Outros").assertIsEnabled().performClick()
            compose.onNode(hasText(product) and hasClickAction()).assertIsEnabled().performClick()
            compose.onNode(hasText("Adicionar ·", substring = true) and hasClickAction()).assertIsEnabled().performScrollTo().performClick()
            compose.onNodeWithText("Voltar às categorias").performClick()
        }
        waitText("Ver pedido atual · 2 itens · R$ 17,00")
        compose.onNodeWithTag("workspace-Pedido atual").performClick()
        waitText("Confirmar pedido")
        compose.onNodeWithText("Confirmar pedido").assertIsEnabled().performScrollTo().performClick()
        waitText("Pedido confirmado pelo servidor.")
        compose.onNodeWithTag("workspace-Conta").performClick()
        compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
        // No seeded state, callback mock, HTTP invocation or optimistic confirmation in this test.
    }
}
