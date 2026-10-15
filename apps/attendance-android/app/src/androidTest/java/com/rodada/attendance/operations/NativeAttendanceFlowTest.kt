package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class NativeAttendanceFlowTest {
    @get:Rule val compose = createComposeRule()
    private val tab = TabSummary("tab-a", "Comanda A", "OPEN", 1, 1200, 0, 1200)
    private val product = Product("product", "Produto do catálogo", 800, true, "BAR", "AVAILABLE")

    @Test fun taskNavigationDoesNotSendOrMixDraftWithCanonicalBalance() {
        var sent = 0
        var backs = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(OperationsUiState(products = listOf(product), cart = listOf(CartLine(product, 2)), connectivity = ConnectivityState.ONLINE),
                TabDetail(tab, emptyList()), { backs++ }, { _, _ -> }, { _, _ -> }, { _, _ -> }, { sent++ },
                {}, {}, {}, {}, {}, {}, {}, {})
        } } }
        compose.onNodeWithText(product.name).assertIsDisplayed()
        compose.onNodeWithText("Saldo em aberto").assertDoesNotExist()
        compose.onNodeWithTag("workspace-Pedido atual").performClick()
        compose.onNodeWithText("Confirmar pedido").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("workspace-Conta").performClick()
        compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
        compose.onNodeWithText(formatCents(1200)).assertIsDisplayed()
        compose.onNodeWithText("Confirmar pedido").assertDoesNotExist()
        compose.onNodeWithTag("workspace-Cardápio").performClick()
        compose.onNodeWithText(product.name).assertIsDisplayed()
        compose.onNodeWithText("← Mesas e comandas").assertHeightIsAtLeast(48.dp).performClick()
        assertEquals(1, backs)
        assertEquals(0, sent)
        captureCriticalEvidence(compose, "native-catalog", compose.onRoot())
    }

    @Test fun ambiguousOrderBlocksBackAndUnavailableProductBlocksAddition() {
        var backs = 0
        var added = 0
        compose.setContent { RodadaTheme { Surface {
            TabWorkspace(OperationsUiState(products = listOf(product.copy(availability = "UNAVAILABLE")), orderIntentId = "original-key", connectivity = ConnectivityState.ONLINE),
                TabDetail(tab, emptyList()), { backs++ }, { _, _ -> added++ }, { _, _ -> }, { _, _ -> }, {},
                {}, {}, {}, {}, {}, {}, {}, {})
        } } }
        compose.onNodeWithText("← Mesas e comandas").assertIsNotEnabled()
        compose.onNodeWithText("Indisponível").assertIsDisplayed()
        compose.onNodeWithContentDescription("Adicionar ${product.name}").assertIsNotEnabled()
        assertEquals(0, backs)
        assertEquals(0, added)
    }

    @Test fun quickOrderPicksTabWithoutSubmittingOrOpeningAnything() {
        var selected = ""
        var opened = 0
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(listOf(tab), canOpenTabs = true, busy = false,
                onSelect = { selected = it }, onNewTab = { opened++ }, onDismiss = {})
        } } }
        compose.onNodeWithText("Buscar comanda ou mesa").performTextInput("Comanda A")
        compose.onNodeWithTag("quick-order-tab-tab-a").performClick()
        assertEquals("tab-a", selected)
        assertEquals(0, opened)
    }

    @Test fun historyIsRequestedOnDemandForStaffWithoutReopenPermission() {
        var requested = 0
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(OperationsUiState(tabs = listOf(tab)), false, { _, _ -> }, {}, {}, {},
                onLoadHistory = { requested++ })
        } } }
        compose.onNodeWithText("Histórico de comandas").performScrollTo().performClick()
        assertEquals(1, requested)
        compose.onNodeWithText("Nenhuma comanda no histórico disponível.").assertDoesNotExist()
    }

    @Test fun unifiedTablesSearchFindsTabAndSelectingDoesNotCreateAnything() {
        var selected = ""
        var created = 0
        val table = TableSummary("table", "12", "OCCUPIED", "DIRECT", false, null,
            TableOccupancy("visit", 1, listOf(TableOccupancyTab("tab-a", "Comanda A", displayReference = "REF-A"))))
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(OperationsUiState(tables = listOf(table), tabs = listOf(tab),
                historyTabs = listOf(tab.copy(id = "closed-tab", displayLabel = "Comanda encerrada", state = "CLOSED")),
                historyLoaded = true), true, { _, _ -> }, {}, {}, {},
                canOpenTabs = true, onSelectTab = { selected = it }, onOpenStandaloneTab = { created++ })
        } } }
        compose.onNodeWithText("Buscar mesa ou comanda").performTextInput("REF-A")
        compose.onNodeWithTag("table-table").performScrollTo().performClick()
        compose.onNodeWithText("Comanda A · REF-A").performScrollTo().performClick()
        assertEquals("tab-a", selected)
        assertEquals(0, created)
        compose.onNodeWithText("Voltar", useUnmergedTree = true).performClick()
        captureCriticalEvidence(compose, "native-tables", compose.onRoot())
        compose.onNodeWithText("Buscar mesa ou comanda").performTextClearance()
        compose.onNodeWithContentDescription("Histórico de comandas").performClick()
        compose.onNodeWithTag("other-tab-closed-tab").performScrollTo().performClick()
        assertEquals("closed-tab", selected)
    }
}
