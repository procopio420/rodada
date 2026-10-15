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
        waitText("Nova comanda sem mesa")
        try {
            compose.waitUntil(30_000) { compose.onAllNodes(hasText("Nova comanda sem mesa") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        } catch (failure: Throwable) {
            val instrumentation = InstrumentationRegistry.getInstrumentation()
            val file = java.io.File(instrumentation.targetContext.getExternalFilesDir(null), "issue106-ui-failure.png")
            java.io.FileOutputStream(file).use { output -> instrumentation.uiAutomation.takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG, 100, output) }
            println(compose.onAllNodes(isRoot()).printToString(maxDepth = 100))
            throw failure
        }
        compose.onNodeWithText("Nova comanda sem mesa").assertIsEnabled().performClick()
        waitText("Nome ou apelido (opcional)")
        compose.onNodeWithText("Nome ou apelido (opcional)").performTextInput(InstrumentationRegistry.getArguments().getString("tabLabel") ?: error("Missing isolated run label"))
        compose.onNodeWithText("Abrir", useUnmergedTree = false).performClick()
        for (product in listOf("Android Compose Test Meal", "Android Post Drop Test Soda")) {
            compose.onNodeWithTag("workspace-list").performScrollToNode(hasContentDescription("Adicionar $product"))
            compose.waitUntil(30_000) { compose.onAllNodes(hasContentDescription("Adicionar $product") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithContentDescription("Adicionar $product").assertIsEnabled().performClick()
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
