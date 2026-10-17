package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Rule
import org.junit.Test

class TablePresentationInstrumentedTest {
    @get:Rule val compose = createComposeRule()
    @Test fun allStatesRemainReadableAndTableOpensAsPageWithBusyProtection() {
        val statuses = listOf("AVAILABLE", "OCCUPIED", "DIRTY", "CLEANING", "OUT_OF_SERVICE")
        val tables = statuses.mapIndexed { index, status -> TableSummary("table-$index", "${index + 1}", status, "DIRECT", false, null, null) }
        val state = mutableStateOf(OperationsUiState(tables = tables, connectivity = ConnectivityState.ONLINE))
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(state.value, true, { _, _ -> }, {}, {}, {})
        } } }
        compose.onNodeWithText("Todas").assertDoesNotExist()
        for (index in tables.indices) {
            val card = compose.onNodeWithTag("table-table-$index")
            compose.onNodeWithTag("tables-list").performScrollToNode(hasTestTag("table-table-$index"))
            try { card.assertIsDisplayed() } catch (failure: AssertionError) {
                captureCriticalEvidence(compose, "status-layout-failure", compose.onRoot())
                throw failure
            }
        }
        compose.onNodeWithTag("tables-list").performScrollToNode(hasTestTag("table-table-0"))
        compose.onNodeWithTag("table-table-0").performClick()
        compose.onNodeWithText("Sem ocupação ativa").assertIsDisplayed()
        compose.runOnIdle { state.value = state.value.copy(submitting = true) }
        compose.onNodeWithText("Voltar").assertIsNotEnabled()
        compose.runOnIdle { state.value = state.value.copy(submitting = false) }
        compose.onNodeWithText("Voltar").performClick()
        compose.onNodeWithText("Sem ocupação ativa").assertDoesNotExist()
        captureCriticalEvidence(compose, "table-statuses-web-style", compose.onRoot())
    }
    @Test fun releaseAndSequentialCleaningFollowCanonicalStatus() {
        val occupied = TableSummary("flow", "8", "OCCUPIED", "DIRECT", false, null, TableOccupancy("visit", 1, emptyList()))
        val state = mutableStateOf(OperationsUiState(tables = listOf(occupied), connectivity = ConnectivityState.ONLINE))
        var released = false
        var started = false
        var completed = false
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(state.value, true, { _, _ -> }, { released = true }, { started = true }, { completed = true })
        } } }
        compose.onNodeWithTag("table-flow").performClick()
        compose.onNodeWithText("Grupo saiu · Liberar mesa", substring = false).performScrollTo().performClick()
        compose.onNodeWithText("Confirmar liberação").performClick()
        org.junit.Assert.assertTrue(released)
        compose.onNodeWithText("Voltar").assertExists()
        compose.runOnIdle { state.value = state.value.copy(tables = listOf(occupied.copy(status = "DIRTY", activeOccupancy = null))) }
        compose.onNodeWithText("Voltar").assertDoesNotExist()
        compose.onNodeWithTag("table-flow").performClick()
        compose.onNodeWithText("Iniciar limpeza").performClick()
        org.junit.Assert.assertTrue(started)
        org.junit.Assert.assertFalse(completed)
        compose.onNodeWithText("Mesa limpa · Disponibilizar").assertDoesNotExist()
        compose.runOnIdle { state.value = state.value.copy(tables = listOf(occupied.copy(status = "CLEANING", activeOccupancy = null))) }
        compose.onNodeWithText("Mesa limpa · Disponibilizar").performClick()
        org.junit.Assert.assertTrue(completed)
        compose.onNodeWithText("Voltar").assertExists()
        compose.runOnIdle { state.value = state.value.copy(tables = listOf(occupied.copy(status = "AVAILABLE", activeOccupancy = null))) }
        compose.onNodeWithText("Voltar").assertDoesNotExist()
        compose.onNodeWithText("Disponível", substring = true).assertIsDisplayed()
    }

}
