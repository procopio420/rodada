package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class AccountAppearanceTest {
    @get:Rule val compose = createComposeRule()
    private val product = Product("account-product", "Bebida do catálogo", 800, true, "BAR", "AVAILABLE")
    private val summary = TabSummary("account-fixture", "Comanda de teste", "OPEN", 1, 4800, 0, 4800, tableLabel = "Mesa 01")
    private val orders = (1..3).map { index -> TabOrder("order-$index", "2026-10-17T18:00:00Z", listOf(
        OrderItem("item-$index", product.name, 800, 2, 1600, "DELIVERED", productId = product.id))) }

    @Test fun accountVisualJourneyPreservesBalanceAndHistory() {
        var writes = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(
                state = OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 1)), connectivity = ConnectivityState.ONLINE),
                tab = TabDetail(summary, orders), onBack = {}, onAdd = { _, _ -> writes++ }, onEdit = { _, _ -> writes++ }, onQuantity = { _, _ -> writes++ },
                onConfirmOrder = { writes++ }, onPay = { writes++ }, onClose = { writes++ }, onAdjustPricing = { writes++ }, onOperations = { writes++ },
                onResolveLimit = { writes++ }, onCorrectItem = { writes++ }, onRefundPayment = { writes++ }, onSettleCorrection = { writes++ })
        } } }
        compose.onNodeWithTag("workspace-Conta").performClick()
        compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
        compose.onNodeWithText(formatCents(4800)).assertIsDisplayed()
        captureCriticalEvidence(compose, "account-overview", compose.onRoot())
        compose.onNodeWithTag("workspace-list").performScrollToNode(hasText("Mais uma rodada"))
        captureCriticalEvidence(compose, "account-history", compose.onRoot())
        assertEquals(0, writes)
    }

    @Test fun accountActionsDisclosurePreservesCallbacksAndGuards() {
        val busy = mutableStateOf(false)
        val online = mutableStateOf(true)
        val current = mutableStateOf(summary)
        var adjustments = 0; var operations = 0; var limits = 0
        compose.setContent { RodadaTheme { Surface {
            AccountActions(current.value, busy.value, online.value, { adjustments++ }, { operations++ }, { limits++ })
        } } }
        compose.onNodeWithText("Ajustar conta / serviço").assertDoesNotExist()
        compose.onNodeWithText("Ações da conta").performClick()
        compose.onNodeWithText("Ajustar conta / serviço").assertIsEnabled().performClick()
        compose.onNodeWithText("Operações da comanda").assertIsEnabled().performClick()
        compose.onNodeWithText("Solicitar / aprovar limite").assertIsEnabled().performClick()
        assertEquals(1, adjustments); assertEquals(1, operations); assertEquals(1, limits)
        compose.runOnIdle { online.value = false }
        compose.onNodeWithText("Ajustar conta / serviço").assertIsNotEnabled()
        compose.onNodeWithText("Solicitar / aprovar limite").assertIsNotEnabled()
        compose.onNodeWithText("Operações da comanda").assertIsEnabled()
        compose.runOnIdle { busy.value = true }
        compose.onNodeWithText("Operações da comanda").assertIsNotEnabled()
        compose.runOnIdle { busy.value = false; current.value = summary.copy(state = "CLOSED") }
        compose.onNodeWithText("Solicitar / aprovar limite").assertDoesNotExist()
    }

    @Test fun confirmedHistoryKeepsCancelledLinesReadOnlyAndUsesHistoricalAmounts() {
        val delivered = orders.first().items.single()
        val cancelled = delivered.copy(id = "cancelled", productName = "Item cancelado", state = "CANCELLED")
        var corrected = ""; var repeated = 0
        compose.setContent { RodadaTheme { Surface {
            ConfirmedOrderCard(orders.first().copy(items = listOf(delivered, cancelled)), true, true, { repeated++ }, { corrected = it.id })
        } } }
        compose.onAllNodesWithText(formatCents(1600)).assertCountEquals(2)
        compose.onNodeWithText("Cancelado").assertExists()
        compose.onAllNodesWithText("Corrigir").assertCountEquals(1)
        compose.onNodeWithText("Corrigir").performClick()
        assertEquals(delivered.id, corrected)
        compose.onNodeWithText("Mais uma rodada").performClick()
        assertEquals(1, repeated)
    }
}
