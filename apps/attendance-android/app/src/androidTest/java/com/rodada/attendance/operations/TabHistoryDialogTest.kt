package com.rodada.attendance.operations

import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class TabHistoryDialogTest {
    @get:Rule val compose = createComposeRule()
    private val tab = TabSummary("history-fixture", "Visita", "CLOSED", 3, 1600, 1600, 0, tableLabel = "01")
    private val detail = TabDetail(tab, listOf(TabOrder("order", "", listOf(
        OrderItem("item", "Item do catálogo", 800, 2, 1600, "DELIVERED")))),
        listOf(TabPayment("payment", 1600, "CASH", "CONFIRMED", 0)))

    @Test fun historyOpensReadOnlyDetailsAndReturnsToList() {
        val state = mutableStateOf(OperationsUiState(historyTabs = listOf(tab), historyLoaded = true))
        var closes = 0
        compose.setContent { RodadaTheme {
            TabHistoryDialog(state.value, {}, { id -> state.value = state.value.copy(
                historyDetailId = id, historyDetail = if (id == null) null else detail) }, { closes++ })
        } }
        compose.onNodeWithText("Histórico da noite").assertExists()
        captureCriticalEvidence(compose, "night-history-list", compose.onNode(isDialog()))
        compose.onNodeWithText(tab.operationalLabel(true)).performClick()
        compose.onNodeWithText("Detalhes da comanda").assertExists()
        compose.onNodeWithText("Recebido").performScrollTo().assertIsDisplayed()
        captureCriticalEvidence(compose, "night-history-detail", compose.onNode(isDialog()))
        compose.onNodeWithText("Dinheiro · ${formatCents(1600)}").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Pagar").assertDoesNotExist()
        compose.onNodeWithText("Corrigir").assertDoesNotExist()
        compose.onNodeWithText("Voltar à lista").performClick()
        compose.onNodeWithText("Histórico da noite").assertExists()
        compose.onNodeWithText("Fechar histórico").performClick()
        assertEquals(1, closes)
    }

    @Test fun historyShowsLoadingErrorRetryAndEmptySearch() {
        val state = mutableStateOf(OperationsUiState(historyLoading = true))
        var reloads = 0
        compose.setContent { RodadaTheme { TabHistoryDialog(state.value, { reloads++ }, {}, {}) } }
        compose.onNodeWithText("Carregando histórico…").assertExists()
        compose.runOnIdle { state.value = state.value.copy(historyLoading = false, historyError = "Falha ao consultar") }
        compose.onNodeWithText("Tentar novamente").performClick()
        assertEquals(1, reloads)
        compose.runOnIdle { state.value = state.value.copy(historyError = null, historyLoaded = true) }
        compose.onNodeWithText("Nenhuma comanda encerrada nesta noite.").assertExists()
        compose.runOnIdle { state.value = state.value.copy(historyTabs = listOf(tab)) }
        compose.onNodeWithText("Buscar comanda").performTextInput("não existe")
        compose.onNodeWithText("Nenhuma comanda encontrada.").assertExists()
    }
}
