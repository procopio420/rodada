package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class NowQueuesTest {
    @get:Rule val compose = createComposeRule()
    private val order = RecoveryIntent.ConfirmOrder("original-order", "staff", "venue", "device", "original-key", 42,
        RecoveryState.PENDING, "tab", listOf(PendingOrderLine("product", 2)))
    private val state = OperationsUiState(
        serviceRequests = (1..30).map { ServiceRequest("call-$it", "SERVICE_REQUEST", "OPEN", "Destino $it", null, it.toLong()) },
        serviceRequestsFresh = true, deliveryTasksFresh = true, connectivity = ConnectivityState.ONLINE, lastSyncedAtMillis = 42,
        deliveryTasks = listOf(DeliveryTask("task", "OPEN", "Destino da entrega", "Produto pronto", 2, "Comanda de teste", 120)),
        queuedOrders = listOf(order), recoveryEvidence = listOf(order.evidence()), recoveryEvidenceReadable = true)

    @Test fun peakShowsReadyFirstAndFiltersNeverSubmitCommands() {
        var submitted = 0
        compose.setContent { RodadaTheme { Surface { TabList(state, true, peak = true,
            onOpenTab = { submitted++ }, onSelect = { submitted++ }, onCompleteDelivery = { submitted++ },
            onServiceAction = { _, _ -> submitted++ }, onOpenRecovery = { submitted++ }) } } }
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("2 Produto pronto"))
        compose.onNodeWithText("2 Produto pronto").assertIsDisplayed()
        compose.onNodeWithText("CHAMADAS DE ATENDIMENTO").assertDoesNotExist()
        compose.onNode(hasScrollToNodeAction()).performScrollToNode(hasText("Prontos primeiro · chamadas e pendências nos filtros"))
        compose.onNodeWithText("Prontos primeiro · chamadas e pendências nos filtros").assertIsDisplayed()
        compose.onNodeWithText("Chamadas\n30").assertHeightIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("CHAMADAS DE ATENDIMENTO").assertIsDisplayed()
        compose.onNodeWithText("2 Produto pronto").assertDoesNotExist()
        compose.onNodeWithText("Pendências\n1").performClick()
        compose.onNodeWithText("PENDÊNCIAS LOCAIS").assertIsDisplayed()
        assertEquals(0, submitted)
        captureCriticalEvidence(compose, "now-pending", compose.onRoot())
    }

    @Test fun recoveryOpensOnlyOriginalRecordWithoutCheckingOrSubmitting() {
        val opened = mutableListOf<String>(); var checks = 0
        compose.setContent { RodadaTheme { Surface { RecoveryPanel(state, { opened.add(it) }, { checks++ }) } } }
        compose.onNodeWithText("Verificar esta operação · original").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(listOf("original-order"), opened); assertEquals(0, checks)
        assertEquals("original-key", order.idempotencyKey)
        assertEquals(2, order.lines.single().quantity)
    }

    @Test fun blockedSessionNeverOffersRecoveryAndBusyDisablesOpening() {
        compose.setContent { RodadaTheme { Surface { RecoveryPanel(state.copy(submitting = true,
            queuedOrders = emptyList(), recoveryEvidence = listOf(order.evidence(), order.copy(id = "blocked").evidence(true))), {}, {}) } } }
        compose.onNodeWithText("Verificar esta operação · original").assertIsNotEnabled()
        compose.onNodeWithText("Outra sessão: revisão pela gerência. Não repita a operação.").assertExists()
        compose.onAllNodesWithText("Verificar esta operação", substring = true).assertCountEquals(1)
    }

    @Test fun filtersExposeSelectionAndUnknownCountsWithoutMutations() {
        var chosen: NowQueue? = null
        compose.setContent { RodadaTheme { Surface { NowQueueNavigation(NowQueue.READY, nowQueueCounts(OperationsUiState()), { chosen = it }) } } }
        compose.onNodeWithText("• Prontos\n—").assertIsSelected().assertHeightIsAtLeast(44.dp)
        compose.onNodeWithText("Chamadas\n—").assertIsNotSelected().performClick()
        assertEquals(NowQueue.CALLS, chosen)
    }
}
