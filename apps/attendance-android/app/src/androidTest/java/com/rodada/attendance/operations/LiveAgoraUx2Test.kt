package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.BuildConfig
import com.rodada.attendance.MainActivity
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Real MainActivity/repositories; opt-in disposable Django/PostgreSQL runner only. */
class LiveAgoraUx2Test {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun authenticatedQueuesAndReturnKeepTheOriginalContext() {
        val args = InstrumentationRegistry.getArguments()
        assumeTrue("Disposable runner only", args.getString("liveAgora") == "true")
        val expectedApi = args.getString("expectedApiBaseUrl") ?: error("Missing isolated API")
        check(expectedApi.matches(Regex("http://10\\.0\\.2\\.2:[0-9]{4,5}/")))
        check(BuildConfig.RODADA_API_BASE_URL == expectedApi)
        compose.waitUntil(30_000) { compose.onAllNodesWithText("Estabelecimento").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Estabelecimento").performTextInput(args.getString("venueSlug") ?: "android-post-drop-ci")
        compose.onNodeWithText("Operador").performTextInput("android-post-drop-operator")
        compose.onNodeWithText("PIN").performTextInput("2468")
        // Dismiss a visible IME, then tap the real button after its viewport settles.
        if (androidx.core.view.ViewCompat.getRootWindowInsets(compose.activity.window.decorView)?.isVisible(androidx.core.view.WindowInsetsCompat.Type.ime()) == true) {
            InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK)
            compose.waitUntil(10_000) {
                androidx.core.view.ViewCompat.getRootWindowInsets(compose.activity.window.decorView)?.isVisible(androidx.core.view.WindowInsetsCompat.Type.ime()) != true
            }
        }
        compose.waitForIdle()
        if (compose.onAllNodes(hasText("Entrar") and hasAnyAncestor(hasScrollAction())).fetchSemanticsNodes().isNotEmpty()) {
            compose.onNodeWithText("Entrar").performScrollTo()
        }
        compose.onNodeWithText("Entrar").assertIsDisplayed().performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasTestTag("attendance-order") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("attendance-now").assertIsSelected()
        compose.onNodeWithTag("now-queue-Atendimentos").assertIsSelected()
        captureCriticalEvidence(compose, "live-agora-service", compose.onRoot())
        if (args.getString("shellJourney") == "true") {
            compose.onNodeWithTag("attendance-tables").performClick()
            captureCriticalEvidence(compose, "live-shell-tables", compose.onRoot())
            compose.onNodeWithTag("table-${args.getString("tableId") ?: error("Missing fixture table")}").performClick()
            compose.onAllNodes(isDialog()).assertCountEquals(0)
            captureCriticalEvidence(compose, "live-shell-table", compose.onRoot())
            compose.onNode(hasText("Marina", substring = true) and hasClickAction()).performScrollTo().performClick()
            compose.waitUntil(30_000) { compose.onAllNodesWithTag("ux2-tab-pages").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithTag("attendance-header").assertIsDisplayed()
            compose.onAllNodes(isDialog()).assertCountEquals(0)
            captureCriticalEvidence(compose, "live-shell-tab", compose.onRoot())
            compose.onNodeWithText("＋ Adicionar itens").performClick()
            compose.onNodeWithContentDescription("Adicionar Chopp Pilsen").performScrollTo().performClick()
            captureCriticalEvidence(compose, "live-shell-catalog", compose.onRoot())
            compose.onNode(hasText("Ver resumo ·", substring = true) and hasClickAction()).performScrollTo().performClick()
            compose.waitUntil(10_000) { compose.onAllNodesWithText("Resumo do pedido.").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("1× Chopp Pilsen").assertExists()
            captureCriticalEvidence(compose, "live-shell-review", compose.onRoot())
            compose.onNodeWithText("‹  Voltar").performScrollTo().performClick()
            compose.onNodeWithText("Adicionar itens.").assertExists()
            compose.onNodeWithText("‹  Voltar").performScrollTo().performClick()
            compose.waitUntil(10_000) { compose.onAllNodesWithText("Marina", substring = false).fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithText("Marina", substring = false).assertExists()
            compose.onNodeWithText("‹  Voltar").performScrollTo().performClick()
            compose.onNodeWithText("Mesa 08").assertExists()
            compose.onNodeWithText("Voltar").performClick()
            compose.onNodeWithTag("tables-list").assertExists()
            return
        }
        compose.onNodeWithTag("now-queue-Entregas").performClick().assertIsSelected()
        captureCriticalEvidence(compose, "live-agora-delivery", compose.onRoot())
        compose.onNodeWithTag("attendance-tables").performClick()
        compose.onNodeWithTag("attendance-now").performClick()
        compose.onNodeWithTag("now-queue-Entregas").assertIsSelected()
        compose.onNodeWithTag("now-queue-Atendimentos").performClick()
        args.getString("serviceTaskId")?.let { id ->
            if (args.getString("revokeBeforeOpen") == "true") {
                val files = InstrumentationRegistry.getInstrumentation().targetContext.filesDir
                java.io.File(files, "task-readback-ready").writeText("ready")
                compose.waitUntil(60_000) { java.io.File(files, "task-readback-revoked").exists() }
                if (args.getString("refreshBeforeTask") == "true") {
                    compose.onNodeWithTag("attendance-options").performClick()
                    compose.onNodeWithText("Atualizar").performClick()
                    compose.onNodeWithTag("attendance-options").performClick()
                    compose.onNodeWithText("Atualizar").assertIsNotEnabled()
                    InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK)
                }
                compose.onNodeWithTag("service-$id").performScrollTo().performClick()
                compose.waitUntil(30_000) { compose.onAllNodes(hasText("Em uso ·", substring = true)).fetchSemanticsNodes().isNotEmpty() }
                compose.onNodeWithTag("workspace-Conta").assertDoesNotExist()
                compose.onNodeWithText("Saldo em aberto").assertDoesNotExist()
                // Explicit selection is now required; opening the stale Guest row selected no Tab.
                args.getString("fallbackTabName")?.let { name ->
                    compose.onNode(hasText(name, substring = false) and hasClickAction()).performScrollTo().performClick()
                    compose.waitUntil(30_000) { compose.onAllNodesWithText("Saldo em aberto").fetchSemanticsNodes().isNotEmpty() }
                    compose.onNodeWithText("Assumir chamada").assertExists()
                    compose.onNodeWithText("Concluir chamada").assertExists()
                    captureCriticalEvidence(compose, "live-agora-explicit-fallback", compose.onRoot())
                    listOf("Assumir chamada", "Concluir chamada").forEach { label ->
                        val layouts = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
                        compose.onNodeWithText(label, useUnmergedTree = true).performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
                        check(layouts.single().lineCount <= 2) { "Action label must remain readable: $label" }
                        check(!layouts.single().hasVisualOverflow) { "Action label overflow: $label lines=${layouts.single().lineCount} size=${layouts.single().size} width=${layouts.single().didOverflowWidth} height=${layouts.single().didOverflowHeight}" }
                        compose.onNodeWithText(label).assertHeightIsAtLeast(androidx.compose.ui.unit.Dp(48f))
                    }
                    // Leaving the workspace ends the task-origin navigation. Reopening the
                    // same Tab manually must not restore the old call.
                    compose.onNodeWithText("← Mesas e comandas").performClick()
                    compose.onNode(hasText(name, substring = false) and hasClickAction()).performScrollTo().performClick()
                    compose.waitUntil(30_000) { compose.onAllNodesWithTag("workspace-Conta").fetchSemanticsNodes().isNotEmpty() }
                    compose.onNodeWithText("Assumir chamada").assertDoesNotExist()
                    compose.onNodeWithText("Concluir chamada").assertDoesNotExist()
                    captureCriticalEvidence(compose, "live-agora-manual-return", compose.onRoot())

                }
                return
            }
            compose.onNodeWithTag("service-$id").performScrollTo().performClick()
            compose.waitUntil(30_000) { compose.onAllNodesWithTag("workspace-Conta").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithTag("workspace-Conta").assertExists()
            compose.onNodeWithText("Saldo em aberto").assertExists()
            compose.onNodeWithText("Assumir chamada").assertExists()
            compose.onNodeWithText("← Mesas e comandas").assertIsDisplayed().performClick()
            compose.onNodeWithTag("now-queue-Atendimentos").assertIsSelected()
        }
    }
}
