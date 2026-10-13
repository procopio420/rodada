package com.rodada.attendance.cash

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.operations.*
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class CashRecoveryScreenTest {
    @get:Rule val compose = createComposeRule()
    private val original = RecoveryIntent.CashClose("close-original", "staff", "venue", "device", "key", 42,
        RecoveryState.CHECKING, "original-shift", 1234, 0, 7)
    private val shift = CashShiftSnapshot("original-shift", "original-point", "2026-10-12", "CLOSED", 0,
        1234, 1234, 0, "NOT_REQUIRED", 8, null, 1234, 0, 1234)

    @Test fun originalClosedShiftOffersOnlyReadAndReturn() {
        var reads = 0; var returns = 0
        compose.setContent { RodadaTheme { Surface { CashRecoveryScreen(CashRecoveryContext(original.id, original = original,
            detail = CashShiftDetail(shift, emptyList())), { reads++ }, { returns++ }) } } }
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Turno original-shift"))
        compose.onNodeWithText("Turno original-shift").assertIsDisplayed()
        compose.onNodeWithText("Encerrado · versão 8").assertIsDisplayed()
        compose.onNodeWithText("Contagem guardada: ${formatCashCents(1234)}").assertExists()
        compose.onNodeWithText("Suprimento").assertDoesNotExist()
        compose.onNodeWithText("Sangria").assertDoesNotExist()
        compose.onNodeWithText("Fechar caixa").assertDoesNotExist()
        captureCriticalEvidence(compose, "cash-original", compose.onRoot())
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Atualizar turno original"))
        compose.onNodeWithText("Atualizar turno original").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, reads)
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Voltar às pendências"))
        compose.onNodeWithText("Voltar às pendências").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, returns)
    }

    @Test fun loadingNeverPresentsAnotherShiftOrAnOutcome() {
        compose.setContent { RodadaTheme { Surface { CashRecoveryScreen(CashRecoveryContext("original", loading = true), {}, {}) } } }
        compose.onNodeWithText("Consultando turno original…").assertIsDisplayed()
        compose.onNodeWithText("Atualizar turno original").assertIsNotEnabled()
        compose.onNodeWithText("Encerrado", substring = true).assertDoesNotExist()
    }

    @Test fun failurePreservesReviewAndOffersOnlyReadRetry() {
        var reads = 0
        compose.setContent { RodadaTheme { Surface { CashRecoveryScreen(CashRecoveryContext("original",
            errorMessage = "Turno indisponível. Não repita a operação."), { reads++ }, {}) } } }
        compose.onNodeWithText("Turno indisponível. Não repita a operação.").assertIsDisplayed()
        compose.onNodeWithText("Atualizar turno original").assertIsEnabled().performClick()
        assertEquals(1, reads)
        compose.onNodeWithText("Encerrado", substring = true).assertDoesNotExist()
    }
}
