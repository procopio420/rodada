package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class ExceptionalRecoveryScreenTest {
    @get:Rule val compose = createComposeRule()
    private val original = RecoveryIntent.Refund("record-original", "staff", "venue", "device", "key", 42,
        RecoveryState.CHECKING, RefundRecoveryKind.SETTLE_CORRECTION, "payment-original", "correction-original", 1234, "Original reason", null)
    private val detail = TabDetail(TabSummary("tab-original", "Original tab", "CLOSED", 7, 100, 100, 0),
        listOf(TabOrder("order", "", listOf(OrderItem("item-original", "Original item", 100, 1, 100, "CANCELLED")))),
        listOf(TabPayment("payment-original", 100, "CASH", "REFUNDED", 100)))
    private val context = ExceptionalRecoveryContext(original,
        ExceptionalRecoveryTarget("tab-original", "item-original", "payment-original", "correction-original", "APPLIED"), detail)

    @Test fun closedTabAndAppliedCorrectionExposeOriginalTargetsWithoutReplayActions() {
        var reads = 0; var returns = 0
        compose.setContent { RodadaTheme { Surface { ExceptionalRecoveryScreen(context, false, { reads++ }, { returns++ }) } } }
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Estorno guardado: ${formatCents(1234)}"))
        compose.onNodeWithText("Estorno guardado: ${formatCents(1234)}").performScrollTo().assertIsDisplayed()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Item original: 1 Original item"))
        compose.onNodeWithText("Item original: 1 Original item").performScrollTo().assertIsDisplayed()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Estado consultado do item: Cancelado"))
        compose.onNodeWithText("Estado consultado do item: Cancelado").performScrollTo().assertIsDisplayed()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Pagamento payment-original"))
        compose.onNodeWithText("Pagamento payment-original").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Dinheiro · Estornado").performScrollTo().assertIsDisplayed()
        captureCriticalEvidence(compose, "exception-original", compose.onRoot())
        compose.onNodeWithText("Confirmar estorno").assertDoesNotExist()
        compose.onNodeWithText("Cancelar item").assertDoesNotExist()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Atualizar operação original"))
        compose.onNodeWithText("Atualizar operação original").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, reads)
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Voltar às pendências"))
        compose.onNodeWithText("Voltar às pendências").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, returns)
    }

    @Test fun busyDisablesBothReadAndReturn() {
        compose.setContent { RodadaTheme { Surface { ExceptionalRecoveryScreen(context, true, {}, {}) } } }
        compose.onNodeWithText("Voltar às pendências").assertIsNotEnabled()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Atualizar operação original"))
        compose.onNodeWithText("Atualizar operação original").assertIsNotEnabled()
    }
}
