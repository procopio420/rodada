package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class TableReleaseTest {
    @get:Rule val compose = createComposeRule()
    private val table = TableSummary("table-a", "A", "OCCUPIED", "ENABLED", false, null,
        TableOccupancy("visit-a", 1, emptyList()))
    private val state = mutableStateOf(OperationsUiState(tables = listOf(table)))
    private val allowed = mutableStateOf(true)
    private val released = mutableListOf<String>()

    private fun render() {
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(state = state.value, canManageTables = allowed.value,
                onOccupy = { _, _ -> }, onAttachTab = { _, _ -> },
                onRelease = { released.add(it) }, onStartCleaning = {}, onCompleteCleaning = {})
        } } }
        compose.onNodeWithText("Liberar mesa").performScrollTo().performClick()
    }

    @Test fun cancellationHasNoMutationAndConfirmationUsesOriginalTable() {
        render()
        compose.onNodeWithText("Liberar mesa A?").assertIsDisplayed()
        compose.onNodeWithText("A ocupação será encerrada e o acesso atual dos clientes pelo QR será revogado. A mesa ficará aguardando limpeza.").assertIsDisplayed()
        captureCriticalEvidence(compose, "table-release", compose.onNode(isDialog()))
        compose.onNodeWithText("Cancelar").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(emptyList<String>(), released)
        compose.onNodeWithText("Liberar mesa").performClick()
        compose.onNodeWithText("Confirmar liberação").assertHeightIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("Confirmar liberação").assertDoesNotExist()
        assertEquals(listOf("table-a"), released)
    }

    @Test fun changedOccupancyNeverAdoptsNewVisit() {
        render()
        compose.runOnIdle { state.value = state.value.copy(tables = listOf(table.copy(activeOccupancy = TableOccupancy("visit-b", 2, emptyList())))) }
        compose.onNodeWithText("Confirmar liberação").assertIsNotEnabled()
        compose.onNodeWithText("A ocupação mudou. Cancele e confira a mesa novamente.").assertIsDisplayed()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(emptyList<String>(), released)
    }

    @Test fun busyOrLostPermissionBlocksConfirmationButAllowsCancellation() {
        render()
        compose.runOnIdle { state.value = state.value.copy(submitting = true) }
        compose.onNodeWithText("Confirmar liberação").assertIsNotEnabled()
        compose.runOnIdle { state.value = state.value.copy(submitting = false); allowed.value = false }
        compose.onNodeWithText("Confirmar liberação").assertIsNotEnabled()
        compose.onNodeWithText("Cancelar").assertIsEnabled().performClick()
        assertEquals(emptyList<String>(), released)
    }
}
