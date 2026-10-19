package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.*
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class AttendanceNowUx2Test {
    @get:Rule val compose = createComposeRule()
    private val state = OperationsUiState(serviceRequestsFresh = true, deliveryTasksFresh = true, connectivity = ConnectivityState.ONLINE,
        lastSyncedAtMillis = 42, serviceRequests = listOf(ServiceRequest("call-a", "BILL_REQUEST", "OPEN", "Mesa 12", null, 120,
            StaffTaskTarget.Tab("11111111-1111-4111-8111-111111111111"))),
        deliveryTasks = listOf(DeliveryTask("delivery-a", "OPEN", "Mesa 12", "Água", 2, "Ana", 180,
            fulfillmentStation = "BAR")))
    @Test fun twoQueuesPreserveSelectionAndOpeningOnlyRoutesTheExactTask() {
        var openedService: String? = null; var openedDelivery: String? = null
        compose.setContent { RodadaTheme { Surface {
            AttendanceNowScreen(state, { openedService = it.id }, { openedDelivery = it.id })
        } } }
        compose.onNodeWithTag("now-queue-Atendimentos").assertIsSelected().assertHeightIsAtLeast(50.dp)
        compose.onNodeWithTag("delivery-delivery-a").assertDoesNotExist()
        compose.onNodeWithTag("service-call-a").performClick()
        assertEquals("call-a", openedService); assertEquals(null, openedDelivery)
        compose.onNodeWithTag("now-queue-Entregas").performClick().assertIsSelected()
        compose.onNodeWithTag("service-call-a").assertDoesNotExist()
        compose.onNodeWithText("Bar · Mesa 12").assertIsDisplayed()
        compose.onNodeWithTag("delivery-delivery-a").performClick()
        assertEquals("delivery-a", openedDelivery)
        compose.onNodeWithText("ENTREGUE").assertDoesNotExist()
        compose.onNodeWithText("Assumir chamada").assertDoesNotExist()
        compose.onNodeWithTag("now-queue-Atendimentos").performClick()
        compose.onNodeWithTag("service-call-a").assertExists()
    }
    @Test fun queueFailureKeepsLastWorkWithUnknownCountAndRecoveryRestoresIt() {
        val shown = mutableStateOf(state)
        compose.setContent { RodadaTheme { Surface { AttendanceNowScreen(shown.value, {}, {}, initiallyShowDeliveries = true) } } }
        compose.onNodeWithTag("delivery-delivery-a").assertExists()
        captureCriticalEvidence(compose, "delivery-queue-fresh", compose.onRoot())
        compose.runOnIdle { shown.value = state.copy(deliveryTasksFresh = false, deliveryTasksError = "Entregas desatualizadas. Atualize para conferir.") }
        compose.onNodeWithTag("now-queue-freshness").assertIsDisplayed()
        compose.onNodeWithTag("delivery-delivery-a").assertExists()
        compose.onNodeWithText(" —").assertExists()
        captureCriticalEvidence(compose, "delivery-queue-stale", compose.onRoot())
        compose.runOnIdle { shown.value = state }
        compose.onNodeWithTag("now-queue-freshness").assertDoesNotExist()
        compose.onNodeWithTag("delivery-delivery-a").assertExists()
    }

    @Test fun unknownFreshnessNeverClaimsZeroTasksAndNeverDropsVisibleWork() {
        compose.setContent { RodadaTheme { Surface {
            AttendanceNowScreen(state.copy(serviceRequestsFresh = false, connectivity = ConnectivityState.OFFLINE), {}, {})
        } } }
        compose.onNodeWithTag("now-queue-freshness").assertExists()
        compose.onNodeWithTag("service-call-a").assertExists()
        compose.onNodeWithText("Nenhuma tarefa nesta fila.", substring = true).assertDoesNotExist()
        compose.onAllNodesWithText(" —").assertCountEquals(2)
    }
    @Test fun deliveryDetailDoesNotCompleteOnOpeningAndProtectsOtherOperators() {
        var completed = 0; var opened = 0
        compose.setContent { RodadaTheme {
            DeliveryTaskDetail(state.deliveryTasks.single().copy(claimedById = "other"), false, "me", {}, { opened++ }, { completed++ })
        } }
        compose.onNodeWithText("2× Água").assertIsDisplayed()
        compose.onNodeWithText("Registrar entrega por exceção").assertIsNotEnabled()
        assertEquals(0, completed); assertEquals(0, opened)
    }
    @Test fun prototypeShellKeepsPrimaryFooterVisibleAndMovesCapabilityActionsToOptions() {
        var cash = 0; var orders = 0
        compose.setContent { RodadaTheme { Column(Modifier.fillMaxSize()) {
            AttendanceHeader("Garçom", ConnectivityState.ONLINE, false, false, {}, {}, {}, "Bar de teste", true, { cash++ })
            androidx.compose.foundation.layout.Box(Modifier.weight(1f)) { AttendanceNowScreen(state, {}, {}) }
            AttendanceNavigation(AttendanceDestination.NOW, false, {}, { orders++ })
        } } }
        compose.onNodeWithTag("attendance-header").assertHeightIsEqualTo(72.dp)
        compose.onNodeWithTag("attendance-nav").assertIsDisplayed()
        compose.onNodeWithTag("attendance-order").assertHeightIsAtLeast(61.dp).performClick()
        assertEquals(1, orders); assertEquals(0, cash)
        compose.onNodeWithText("Caixa").assertDoesNotExist()
        compose.onNodeWithTag("attendance-options").performClick()
        compose.onNodeWithText("Caixa").assertIsDisplayed().performClick()
        assertEquals(1, cash)
    }
    @Test fun typedTableNavigationIsConsumedOnceAndBackDoesNotReopenOnRefresh() {
        val table = TableSummary("table", "12", "OCCUPIED", "DIRECT", false, null,
            TableOccupancy("visit", 7, listOf(TableOccupancyTab("tab-a", "Ana", displayReference = "A"), TableOccupancyTab("tab-b", "Bia", displayReference = "B"))))
        val tablesState = mutableStateOf(OperationsUiState(tables = listOf(table)))
        val target = mutableStateOf<StaffTaskTarget.Table?>(StaffTaskTarget.Table("table", "visit", 7))
        var selected: String? = null; var mutations = 0; var consumed = 0
        compose.setContent { RodadaTheme { Surface {
            TablesScreen(tablesState.value, true, { _, _ -> mutations++ }, { mutations++ }, { mutations++ }, { mutations++ },
                requestedTarget = target.value, onTargetConsumed = { consumed++; target.value = null },
                onSelectTab = { selected = it })
        } } }
        compose.onNodeWithText("Bia").performScrollTo().performClick()
        assertEquals("tab-b", selected); assertEquals(0, mutations); assertEquals(1, consumed)
        compose.onNodeWithText("Voltar", useUnmergedTree = true).performClick()
        compose.runOnIdle { tablesState.value = tablesState.value.copy(tables = listOf(table.copy(label = "12 atualizada"))) }
        compose.onNodeWithText("Bia").assertDoesNotExist()
        assertEquals(0, mutations); assertEquals(1, consumed)
    }
}
