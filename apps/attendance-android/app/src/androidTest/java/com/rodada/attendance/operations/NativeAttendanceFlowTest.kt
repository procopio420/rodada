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
        compose.onNodeWithTag("catalog-category-Outros").assertIsDisplayed()
        compose.onNodeWithText("Saldo em aberto").assertDoesNotExist()
        compose.onNodeWithTag("workspace-Pedido atual").performClick()
        compose.onNodeWithText("Confirmar pedido").performScrollTo().assertIsDisplayed()
        compose.onNodeWithTag("workspace-Conta").performClick()
        compose.onNodeWithText("Saldo em aberto").assertIsDisplayed()
        compose.onNodeWithText(formatCents(1200)).assertIsDisplayed()
        compose.onNodeWithText("Confirmar pedido").assertDoesNotExist()
        compose.onNodeWithTag("workspace-Cardápio").performClick()
        compose.onNodeWithTag("catalog-category-Outros").assertIsDisplayed()
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
        compose.onNodeWithTag("catalog-category-Outros").assertIsNotEnabled()
        compose.onNodeWithText(product.name).assertDoesNotExist()
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

    @Test fun quickOrderCreatesTableTabOnlyAfterNameConfirmation() {
        val table = TableSummary("available", "01", "AVAILABLE", "STAFF", false, null, null)
        var opened = ""
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, false, {}, {}, {},
                tables = listOf(table, table.copy(id = "dirty", status = "DIRTY")), canOpenTableTabs = true,
                onNewTableTab = { id, name -> opened = "${id.id}:$name" })
        } } }
        compose.onNodeWithText("Nova comanda em mesa").performClick()
        compose.onNodeWithTag("quick-order-table-dirty").assertDoesNotExist()
        compose.onNodeWithTag("quick-order-table-available").performClick()
        assertEquals("", opened)
        compose.onNodeWithText("Abrir e pedir").assertIsNotEnabled()
        compose.onNodeWithText("Nome ou apelido").performTextInput("  Grupo  ")
        compose.onNodeWithText("Abrir e pedir").performClick()
        assertEquals("available:Grupo", opened)
        captureCriticalEvidence(compose, "quick-order-table-name", compose.onNode(isDialog()))
    }

    @Test fun quickOrderTableSelectionHandlesEmptyAndBackWithoutMutation() {
        var opened = 0
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, false, {}, {}, {},
                canOpenTableTabs = true, onNewTableTab = { _, _ -> opened++ })
        } } }
        compose.onNodeWithText("Nova comanda em mesa").performClick()
        compose.onNodeWithText("Nenhuma mesa disponível no momento.").assertIsDisplayed()
        compose.onNodeWithText("Voltar").performClick()
        compose.onNodeWithText("Nova comanda sem mesa").assertIsDisplayed()
        assertEquals(0, opened)
    }

    @Test fun quickOrderRevalidatesTableBeforeConfirmation() {
        val table = TableSummary("available", "01", "AVAILABLE", "STAFF", false, null, null)
        val tables = androidx.compose.runtime.mutableStateOf(listOf(table))
        var opened = 0
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, false, {}, {}, {}, tables = tables.value,
                canOpenTableTabs = true, onNewTableTab = { _, _ -> opened++ })
        } } }
        compose.onNodeWithText("Nova comanda em mesa").performClick()
        compose.onNodeWithTag("quick-order-table-available").performClick()
        compose.onNodeWithText("Nome ou apelido").performTextInput("Grupo")
        compose.runOnIdle { tables.value = listOf(table.copy(status = "OCCUPIED")) }
        compose.onNodeWithText("Abrir e pedir").assertIsNotEnabled()
        compose.onNodeWithText("A mesa não está mais disponível. Volte e escolha outra mesa.").assertIsDisplayed()
        compose.onNodeWithText("Voltar").performClick()
        compose.onNodeWithText("Nenhuma mesa disponível no momento.").assertIsDisplayed()
        assertEquals(0, opened)
    }

    @Test fun quickOrderHidesTableCreationWithoutCapability() {
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, false, {}, {}, {})
        } } }
        compose.onNodeWithText("Nova comanda em mesa").assertDoesNotExist()
        compose.onNodeWithText("Nova comanda sem mesa").assertIsDisplayed()
    }

    @Test fun quickOrderOccupiedTableKeepsOccupancyAndDetectsReplacement() {
        val occupancy = TableOccupancy("occupancy", 3, emptyList())
        val table = TableSummary("occupied", "02", "OCCUPIED", "STAFF", false, null, occupancy)
        val tables = androidx.compose.runtime.mutableStateOf(listOf(table))
        var opened: TableSummary? = null
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, false, {}, {}, {}, tables = tables.value,
                canOpenTableTabs = true, onNewTableTab = { selected, _ -> opened = selected })
        } } }
        val newButton = compose.onNodeWithText("Nova comanda sem mesa").fetchSemanticsNode().boundsInRoot
        val cancelButton = compose.onNodeWithText("Cancelar").fetchSemanticsNode().boundsInRoot
        org.junit.Assert.assertTrue(cancelButton.top >= newButton.bottom)
        captureCriticalEvidence(compose, "quick-order-actions", compose.onNode(isDialog()))
        compose.onNodeWithText("Nova comanda em mesa").performClick()
        compose.onNodeWithText("Mesa 02 · Ocupada").assertIsDisplayed().performClick()
        assertEquals(null, opened)
        compose.onNodeWithText("Nome ou apelido").performTextInput("Grupo")
        compose.onNodeWithText("Abrir e pedir").performClick()
        assertEquals(occupancy, opened?.activeOccupancy)
        compose.runOnIdle { tables.value = listOf(table.copy(activeOccupancy = occupancy.copy(generation = 4))) }
        compose.onNodeWithText("Abrir e pedir").assertIsNotEnabled()
    }

    @Test fun quickOrderDisablesCreationWhileBusy() {
        compose.setContent { RodadaTheme { Surface {
            QuickOrderDestinationDialog(emptyList(), true, true, {}, {}, {}, canOpenTableTabs = true)
        } } }
        compose.onNodeWithText("Nova comanda em mesa").assertIsNotEnabled()
        compose.onNodeWithText("Nova comanda sem mesa").assertIsNotEnabled()
    }

    @Test fun historyIsRequestedOnDemandForStaffWithoutReopenPermission() {
        var requested = 0
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(OperationsUiState(tabs = listOf(tab)), false, { _, _ -> }, {}, {}, {},
                onLoadHistory = { requested++ })
        } } }
        compose.onNodeWithContentDescription("Histórico de comandas").performClick()
        assertEquals(1, requested)
        compose.onNodeWithText("Nenhuma comanda no histórico disponível.").assertDoesNotExist()
    }

    @Test fun unifiedTablesSearchFindsTabAndSelectingDoesNotCreateAnything() {
        var selected = ""
        var created = 0
        var inspected = ""
        val table = TableSummary("table", "12", "OCCUPIED", "DIRECT", false, null,
            TableOccupancy("visit", 1, listOf(TableOccupancyTab("tab-a", "Comanda A", displayReference = "REF-A"))))
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(OperationsUiState(tables = listOf(table), tabs = listOf(tab),
                historyTabs = listOf(tab.copy(id = "closed-tab", displayLabel = "Comanda encerrada", state = "CLOSED")),
                historyLoaded = true), true, { _, _ -> }, {}, {}, {},
                canOpenTabs = true, onSelectTab = { selected = it }, onOpenStandaloneTab = { created++ },
                onInspectHistory = { inspected = it.orEmpty() })
        } } }
        compose.onNodeWithContentDescription("Buscar mesa ou comanda").performTextInput("REF-A")
        compose.onNodeWithTag("table-table").performScrollTo().performClick()
        compose.onNodeWithText("Comanda A").performScrollTo().performClick()
        assertEquals("tab-a", selected)
        assertEquals(0, created)
        compose.onNodeWithText("Voltar", useUnmergedTree = true).performClick()
        captureCriticalEvidence(compose, "native-tables", compose.onRoot())
        compose.onNodeWithContentDescription("Buscar mesa ou comanda").performTextClearance()
        compose.onNodeWithContentDescription("Histórico de comandas").performClick()
        compose.onNodeWithText("Comanda encerrada").performScrollTo().performClick()
        assertEquals("closed-tab", inspected)
        assertEquals("tab-a", selected)
        assertEquals(0, created)
    }
}
