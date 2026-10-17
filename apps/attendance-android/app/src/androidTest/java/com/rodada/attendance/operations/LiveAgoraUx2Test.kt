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
        compose.onNodeWithText("Estabelecimento").performTextInput("android-post-drop-ci")
        compose.onNodeWithText("Operador").performTextInput("android-post-drop-operator")
        compose.onNodeWithText("PIN").performTextInput("2468")
        compose.onNodeWithText("Entrar").performClick()
        compose.waitUntil(30_000) { compose.onAllNodes(hasTestTag("attendance-order") and isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("attendance-now").assertIsSelected()
        compose.onNodeWithTag("now-queue-Atendimentos").assertIsSelected()
        captureCriticalEvidence(compose, "live-agora-service", compose.onRoot())
        compose.onNodeWithTag("now-queue-Entregas").performClick().assertIsSelected()
        captureCriticalEvidence(compose, "live-agora-delivery", compose.onRoot())
        compose.onNodeWithTag("attendance-tables").performClick()
        compose.onNodeWithTag("attendance-now").performClick()
        compose.onNodeWithTag("now-queue-Entregas").assertIsSelected()
        compose.onNodeWithTag("now-queue-Atendimentos").performClick()
        args.getString("serviceTaskId")?.let { id ->
            compose.onNodeWithTag("service-$id").performScrollTo().performClick()
            compose.waitUntil(30_000) { compose.onAllNodesWithTag("workspace-Conta").fetchSemanticsNodes().isNotEmpty() }
            compose.onNodeWithTag("workspace-Conta").assertExists()
            compose.onNodeWithText("Saldo em aberto").assertExists()
            compose.onNodeWithText("← Mesas e comandas").assertIsDisplayed().performClick()
            compose.onNodeWithTag("now-queue-Atendimentos").assertIsSelected()
        }
    }
}
