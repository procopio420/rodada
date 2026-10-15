package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.MainActivity
import com.rodada.attendance.BuildConfig
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Read the same Guest/Web contextual Tabs after real Bar/Kitchen READY actions. */
class LiveComposeReadbackTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun waitFor(matcher: SemanticsMatcher) {
        compose.waitUntil(30_000) { compose.onAllNodes(matcher).fetchSemanticsNodes().isNotEmpty() }
    }
    @Test fun readBothContextualTabsWithoutMutation() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue(args.getString("liveReadback") == "true")
        check(BuildConfig.RODADA_API_BASE_URL == "http://10.0.2.2:8101/")
        waitFor(hasText("Estabelecimento"))
        compose.onNodeWithText("Estabelecimento").performTextInput("android-post-drop-ci")
        compose.onNodeWithText("Operador").performTextInput("android-post-drop-operator")
        compose.onNodeWithText("PIN").performTextInput("2468")
        compose.onNodeWithText("Entrar").performClick()
        waitFor(hasTestTag("attendance-tables") and isEnabled())
        compose.onNodeWithTag("attendance-tables").performClick()
        val tableTag = "table-${args.getString("tableId") ?: error("Missing table") }"
        for (key in listOf("tabOne", "tabTwo")) {
            waitFor(hasTestTag("tables-list"))
            compose.onNodeWithText("Buscar mesa ou comanda").performTextClearance()
            compose.onNodeWithText("Buscar mesa ou comanda").performTextInput(args.getString("tableLabel") ?: error("Missing table label"))
            compose.onNodeWithTag("tables-list").performScrollToNode(hasTestTag(tableTag))
            compose.onNodeWithTag(tableTag).performClick()
            val tab = hasText(args.getString(key) ?: error("Missing Tab label"), substring = true) and hasClickAction() and hasAnyAncestor(isDialog())
            waitFor(tab and isEnabled())
            compose.onNode(tab).performClick()
            waitFor(hasTestTag("workspace-Conta") and isEnabled())
            compose.onNodeWithTag("workspace-Conta").performClick()
            waitFor(hasTestTag("workspace-list"))
            compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Pronto"))
            compose.waitUntil(30_000) { compose.onAllNodesWithText("Pronto").fetchSemanticsNodes().size == 2 }
            compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Saldo em aberto"))
            compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
            compose.onNodeWithText("R$ 17,00").assertIsDisplayed()
            compose.onNodeWithText("← Mesas e comandas").performClick()
        }
        // No confirm/payment/fulfillment action, direct HTTP client or seeded Compose state.
    }
}
