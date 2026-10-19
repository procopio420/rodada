package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Deterministic presentation tests; never evidence of a real financial mutation. */
class Ux2AccountPagesTest {
    @get:Rule val compose = createComposeRule()
    private val tab = TabDetail(TabSummary("1048", "Marina", "OPEN", 1, 2400, 0, 2400, tableLabel = "08", effectiveLimitCents = 20000, remainingCapacityCents = 17600, relationshipSnapshot = "REGULAR"), emptyList())

    @Test fun fullReceiptOnlyOffersCanonicalCloseWithOriginalCashPoint() {
        var command: List<Any?>? = null
        compose.setContent { RodadaTheme { Surface {
            Ux2ReceiptPage(OperationsUiState(cashPoints = listOf(CashPoint("cash", "Caixa principal", "shift"))), tab, {},
                { amount, method, point, close -> command = listOf(amount, method, point, close) }, {}, {})
        } } }
        compose.onNodeWithText("Receber conta.").assertIsDisplayed()
        captureCriticalEvidence(compose, "ux2-receipt-full", compose.onRoot())
        compose.onNodeWithText("Só registrar; manter comanda aberta").assertDoesNotExist()
        compose.onNodeWithText("Receber e encerrar comanda").performScrollTo().performClick()
        assertEquals(listOf(2400L, PaymentMethod.CASH, "cash", true), command)
    }

    @Test fun partialAndUnknownReceiptUseDistinctActions() {
        var pending = false
        val intent = RecoveryIntent.StartPayment("i", "s", "v", "d", "key", 1, RecoveryState.CHECKING,
            "tab", 2400, PaymentMethod.CASH, "cash", 1, true, "confirmed-payment")
        compose.setContent { RodadaTheme { Surface {
            Ux2ReceiptPage(OperationsUiState(pendingPayment = intent), tab, {}, { _, _, _, _ -> fail("Cannot submit another receipt") }, { pending = true }, {})
        } } }
        compose.onNodeWithText("Recebido; encerramento pendente.").assertExists()
        compose.onNodeWithText("Registrar recebimento").assertDoesNotExist()
        compose.onNodeWithText("Verificar recebimento e comanda").performScrollTo().performClick()
        assertTrue(pending)
        captureCriticalEvidence(compose, "ux2-receipt-confirmed-close-pending", compose.onRoot())
    }

    @Test fun zeroBalanceClosesDirectlyWithoutPaymentForm() {
        var closes = 0
        compose.setContent { RodadaTheme { Surface {
            Ux2AccountPage(OperationsUiState(), tab.copy(summary = tab.summary.copy(exposureCents = 0, paymentsCents = 2400)),
                {}, { fail("No payment for zero balance") }, { closes++ }, {}, {}, {}, {}, {}, {})
        } } }
        compose.onNodeWithText("Encerrar comanda").performScrollTo().performClick()
        assertEquals(1, closes)
        captureCriticalEvidence(compose, "ux2-account-zero", compose.onRoot())
    }
}
