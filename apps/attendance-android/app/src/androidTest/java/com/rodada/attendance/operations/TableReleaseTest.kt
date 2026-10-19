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
    private val state = mutableStateOf(OperationsUiState(tables = listOf(table), deliveryTasksFresh = true, connectivity = ConnectivityState.ONLINE))
    private val allowed = mutableStateOf(true)
    private val released = mutableListOf<String>()
    private val releasedTargets = mutableListOf<TableReleaseCommand>()

    private fun render() {
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(state = state.value, canManageTables = allowed.value,
                onOccupy = { _, _ -> }, onAttachTab = { _, _ -> },
                onRelease = { released.add(it.tableId); releasedTargets.add(it) }, onStartCleaning = {}, onCompleteCleaning = {})
        } } }
        compose.onNodeWithTag("table-table-a").performClick()
        compose.onNodeWithText("Grupo saiu · Liberar mesa").performScrollTo().performClick()
    }

    @Test fun cancellationHasNoMutationAndConfirmationUsesOriginalTable() {
        render()
        compose.onNodeWithText("Liberar mesa A?").assertIsDisplayed()
        compose.onNodeWithText("A ocupação será encerrada e o acesso atual dos clientes pelo QR será revogado. A mesa ficará aguardando limpeza.").assertIsDisplayed()
        captureCriticalEvidence(compose, "table-release", compose.onNode(isDialog()))
        compose.onNodeWithText("Cancelar").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(emptyList<String>(), released)
        compose.onNodeWithText("Grupo saiu · Liberar mesa").performClick()
        compose.onNodeWithText("Confirmar liberação").assertHeightIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("Confirmar liberação").assertDoesNotExist()
        assertEquals(listOf("table-a"), released)
        assertEquals(listOf(TableReleaseCommand("table-a", "visit-a", 1)), releasedTargets)
    }

    @Test fun staleDispatchWhileDialogOpenBlocksRelease() {
        render()
        compose.runOnIdle { state.value = state.value.copy(deliveryTasksFresh = false) }
        compose.onNodeWithText("Confirmar liberação").assertIsNotEnabled()
        compose.onAllNodesWithText("Entregas desatualizadas. Atualize antes de liberar a mesa.").onFirst().assertExists()
        captureCriticalEvidence(compose, "table-release-stale-dispatch", compose.onNode(isDialog()))
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(emptyList<String>(), released)
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
    @Test fun readyDeliveryArrivingDuringConfirmationBlocksReleaseWithoutCompletingWork() {
        render()
        compose.runOnIdle { state.value = state.value.copy(deliveryTasks = listOf(
            DeliveryTask("ready", "OPEN", "A", "Água", 1, "", 0, StaffTaskTarget.Table("table-a", "visit-a", 1))
        )) }
        compose.onNodeWithText("Confirmar liberação").assertIsNotEnabled()
        compose.onNodeWithText("Cancelar").performClick()
        assertEquals(emptyList<String>(), released)
        assertEquals("OPEN", state.value.deliveryTasks.single().state)
    }

}
