package com.rodada.attendance.operations

import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.onNodeWithText
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

    @Test fun oneTapStartThenOptionalNameAndContextualOpen() {
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
        compose.onNodeWithText("Iniciar atendimento").performClick()
        assertEquals(listOf("table"), starts)
        compose.onNodeWithText("Atendimento: você").assertExists()
        compose.onNodeWithText("Nova comanda nesta mesa").performScrollTo().performClick()
        compose.onNodeWithText("Nome ou apelido (opcional)").assertExists()
        compose.onNodeWithText("Abrir e pedir").performClick()
        assertEquals("visit" to "", opened)
    }

    @Test fun homonymsResolveByIdAndPendingIntentDisablesMutations() {
        val occupancy = TableOccupancy("visit", 1, listOf(
            TableOccupancyTab("a", "João", displayReference = "Comanda A"),
            TableOccupancyTab("b", "João", displayReference = "Comanda B")))
        val state = mutableStateOf(OperationsUiState(tables = listOf(table.copy(status = "OCCUPIED", activeOccupancy = occupancy))))
        var selected = ""
        compose.setContent { RodadaTheme { TablesScreen(state.value, true, { _, _ -> }, {}, {}, {},
            staffId = "staff", onSelectTab = { selected = it }) } }
        compose.onNodeWithText("João · Comanda B").performScrollTo().performClick()
        assertEquals("b", selected)
        compose.runOnIdle { state.value = state.value.copy(pendingTableService = RecoveryIntent.TableService(
            "id", "staff", "venue", "device", "key", 1, RecoveryState.CHECKING,
            "/hospitality/occupancies/visit/responsibility/claim/", "{}")) }
        compose.onNodeWithText("Assumir atendimento").performScrollTo().assertIsNotEnabled()
    }
}
