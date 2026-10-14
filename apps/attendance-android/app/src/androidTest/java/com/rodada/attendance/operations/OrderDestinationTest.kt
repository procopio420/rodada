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

class OrderDestinationTest {
    @get:Rule val compose = createComposeRule()
    private val tabs = listOf(
        TabSummary("aaaaaaaa-1", "Comanda de teste", "OPEN", 1, 3800, 1000, 2800),
        TabSummary("bbbbbbbb-2", "Comanda de teste", "OPEN", 1, 800, 0, 800),
        TabSummary("cccccccc-3", "Comanda encerrada", "CLOSED", 1, 800, 800, 0),
    )
    private val state = mutableStateOf(OperationsUiState(tabs = tabs))
    private var created = 0
    private var selected: String? = null

    private fun render() {
        compose.setContent { RodadaTheme { Surface {
            TabList(state.value, showDeliveries = false, choosingOrderDestination = true,
                onOpenTab = { created++ }, onSelect = { selected = it }, onCompleteDelivery = {})
        } } }
    }

    @Test fun distinctDestinationsDoNotCreateAndNewTabIsExplicit() {
        render()
        compose.onNodeWithText("Escolha a comanda para pedir").assertIsDisplayed()
        compose.onNodeWithText("Comanda encerrada").assertDoesNotExist()
        compose.onAllNodesWithText("Comanda de teste", useUnmergedTree = true).assertCountEquals(2)
        captureCriticalEvidence(compose, "order-destination", compose.onRoot())
        compose.onNodeWithText("Comanda bbbbbbbb").performScrollTo().performClick()
        assertEquals("bbbbbbbb-2", selected)
        assertEquals(0, created)
        compose.onNodeWithText("Comanda aaaaaaaa").performScrollTo().performClick()
        assertEquals("aaaaaaaa-1", selected)
        assertEquals(0, created)
        compose.onNodeWithText("Nova comanda").performScrollTo().assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, created)
        assertEquals("aaaaaaaa-1", selected)
    }

    @Test fun emptyInventoryDoesNotCreateAutomatically() {
        state.value = OperationsUiState()
        render()
        compose.onNodeWithText("Nenhuma comanda aberta neste dispositivo.").assertIsDisplayed()
        assertEquals(0, created)
        assertEquals(null, selected)
        compose.onNodeWithText("Nova comanda").performClick()
        assertEquals(1, created)
    }

    @Test fun loadingAndBusyBlockDestinationAndCreation() {
        render()
        compose.runOnIdle { state.value = state.value.copy(loading = true) }
        compose.onNodeWithText("Nova comanda").assertIsNotEnabled()
        compose.onNodeWithText("Comanda aaaaaaaa").assertIsNotEnabled()
        compose.runOnIdle { state.value = state.value.copy(loading = false, submitting = true) }
        compose.onNodeWithText("Nova comanda").assertIsNotEnabled()
        compose.onNodeWithText("Comanda bbbbbbbb").assertIsNotEnabled()
        assertEquals(0, created)
        assertEquals(null, selected)
    }
}
