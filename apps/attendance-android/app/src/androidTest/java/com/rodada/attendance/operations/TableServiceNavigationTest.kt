package com.rodada.attendance.operations

import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextClearance
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

/** UI callbacks only; this fixture is not evidence of a server transaction. */
class TableServiceNavigationTest {
    @get:Rule val compose = createComposeRule()
    private val table = TableSummary("table", "12", "AVAILABLE", "DIRECT", false, null, null)

    @Test fun oneTapStartThenRequiredVisibleNameAndContextualOpen() {
        val state = mutableStateOf(OperationsUiState(tables = listOf(table)))
        val starts = mutableListOf<String>()
        var opened: Pair<String, String>? = null
        compose.setContent { RodadaTheme { TablesScreen(state.value, true, { _, _ -> }, {}, {}, {},
            staffId = "staff", canOpenTabs = true,
            onStartService = { id ->
                starts.add(id)
                state.value = state.value.copy(tables = listOf(table.copy(status = "OCCUPIED",
                    activeOccupancy = TableOccupancy("visit", 3, emptyList(), "staff", "Ana", 1))))
            }, onOpenTableTab = { occupancy, name -> opened = occupancy.id to name }) } }
        compose.onNodeWithTag("table-table").performClick()
        compose.onNodeWithText("Iniciar atendimento sem comanda").performScrollTo().performClick()
        assertEquals(listOf("table"), starts)
        compose.onNodeWithText("Atendimento: você").assertExists()
        compose.onNodeWithText("Nova comanda nesta mesa").performScrollTo().performClick()
        compose.onNodeWithText("Ocultar nome").assertDoesNotExist()
        compose.onNodeWithText("Nome ou apelido").assertExists()
        compose.onNodeWithText("Abrir e pedir").assertIsNotEnabled()
        compose.onNodeWithText("Nome ou apelido").performTextInput("   ")
        compose.onNodeWithText("Abrir e pedir").assertIsNotEnabled()
        compose.onNodeWithText("Nome ou apelido").performTextClearance()
        compose.onNodeWithText("Nome ou apelido").performTextInput("Grupo 7")
        compose.onNodeWithText("Abrir e pedir").performClick()
        assertEquals("visit" to "Grupo 7", opened)
    }

    @Test fun homonymsResolveByIdAndPendingIntentDisablesMutations() {
        val occupancy = TableOccupancy("visit", 1, listOf(
            TableOccupancyTab("a", "João", displayReference = "Comanda A"),
            TableOccupancyTab("b", "João", displayReference = "Comanda B")))
        val state = mutableStateOf(OperationsUiState(tables = listOf(table.copy(status = "OCCUPIED", activeOccupancy = occupancy))))
        var selected = ""
        compose.setContent { RodadaTheme { TablesScreen(state.value, true, { _, _ -> }, {}, {}, {},
            staffId = "staff", onSelectTab = { selected = it }) } }
        compose.onNodeWithTag("table-table").performClick()
        compose.onNodeWithText("João · Comanda B").performScrollTo().performClick()
        assertEquals("b", selected)
        compose.runOnIdle { state.value = state.value.copy(pendingTableService = RecoveryIntent.TableService(
            "id", "staff", "venue", "device", "key", 1, RecoveryState.CHECKING,
            "/hospitality/occupancies/visit/responsibility/claim/", "{}")) }
        compose.onNodeWithText("Assumir atendimento").performScrollTo().assertIsNotEnabled()
    }
    @Test fun moveLinkedTabRequiresOriginDestinationConfirmation() {
        val tab = TabSummary("linked", "João", "OPEN", 3, 700, 0, 700)
        val origin = table.copy(status = "OCCUPIED", activeOccupancy = TableOccupancy("origin", 1,
            listOf(TableOccupancyTab(tab.id, tab.displayLabel))))
        val destination = table.copy(id = "destination", label = "13", status = "OCCUPIED",
            activeOccupancy = TableOccupancy("destination-visit", 1, emptyList()))
        val state = OperationsUiState(tables = listOf(destination, origin), tabs = listOf(tab))
        var moved: Pair<String, String>? = null
        compose.setContent { RodadaTheme { TablesScreen(state, true, { _, _ -> error("Linked Tab must not use assign") }, {}, {}, {},
            canMoveTabs = true, onMoveTab = { visit, chosen -> moved = visit to chosen.id }) } }
        compose.onNodeWithTag("table-destination").performClick()
        compose.onAllNodesWithText("Vincular comanda existente")[0].performScrollTo().performClick()
        compose.onNodeWithText("João · linked · Mesa 12 · Mover").performClick()
        assertEquals(null, moved)
        compose.onNodeWithText("João · linked: Mesa 12 → Mesa 13. O saldo permanece nesta comanda.").assertExists()
        compose.onNodeWithText("Confirmar mudança de mesa").performClick()
        assertEquals("destination-visit" to "linked", moved)
    }

    @Test fun standaloneNameIsAlwaysVisibleRequiredAndLimited() {
        var opened: String? = null
        compose.setContent { RodadaTheme {
            OpenTabDialog(false, emptyList(), null, {}, {}, { label, _ -> opened = label })
        } }
        compose.onNodeWithText("Nome ou apelido").assertExists()
        compose.onNodeWithText("Abrir").assertIsNotEnabled()
        compose.onNodeWithText("Nome ou apelido").performTextInput("   ")
        compose.onNodeWithText("Abrir").assertIsNotEnabled()
        compose.onNodeWithText("Nome ou apelido").performTextClearance()
        compose.onNodeWithText("Nome ou apelido").performTextInput("x".repeat(121))
        assertEquals(120, compose.onNodeWithText("Nome ou apelido").fetchSemanticsNode().config[androidx.compose.ui.semantics.SemanticsProperties.EditableText].text.length)
        compose.onNodeWithText("Nome ou apelido").performTextClearance()
        compose.onNodeWithText("Nome ou apelido").performTextInput("  Grupo 7  ")
        compose.onNodeWithText("Abrir").performClick()
        assertEquals("Grupo 7", opened)
    }

}
