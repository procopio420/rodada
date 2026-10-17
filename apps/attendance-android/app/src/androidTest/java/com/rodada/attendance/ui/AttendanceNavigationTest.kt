package com.rodada.attendance.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class AttendanceNavigationTest {
    @get:Rule val compose = createComposeRule()
    @Test fun unifiedDestinationAndCashAreExplicitAndDoNotCreateOrders() {
        var chosen: AttendanceDestination? = null
        var orders = 0
        compose.setContent { RodadaTheme { AttendanceNavigation(AttendanceDestination.TABLES, false, { chosen = it }, { orders++ }) } }
        compose.onNodeWithTag("attendance-tables").assertIsSelected().assertHeightIsAtLeast(48.dp)
        compose.onNodeWithText("CONTAS").assertDoesNotExist()
        compose.onNodeWithTag("attendance-now").performClick()
        assertEquals(AttendanceDestination.NOW, chosen)
        compose.onNodeWithText("Caixa").assertDoesNotExist()
        compose.onNodeWithTag("attendance-tables").performClick()
        assertEquals(AttendanceDestination.TABLES, chosen)
        compose.onNodeWithTag("attendance-order").assertHeightIsAtLeast(56.dp).performClick()
        assertEquals(1, orders)
    }
    @Test fun busyDisablesNavigationAndMissingCapabilityHidesCash() {
        compose.setContent { RodadaTheme { AttendanceNavigation(AttendanceDestination.NOW, true, {}, {}) } }
        compose.onNodeWithText("Caixa").assertDoesNotExist()
        compose.onNodeWithTag("attendance-tables").assertIsNotEnabled()
        compose.onNodeWithTag("attendance-now").assertIsSelected().assertIsNotEnabled()
        compose.onNodeWithTag("attendance-order").assertIsNotEnabled()
    }

    @Test fun restoredLegacyTabsDestinationUsesUnifiedEntry() {
        var chosen: AttendanceDestination? = null
        compose.setContent { RodadaTheme { AttendanceNavigation(AttendanceDestination.TABS, false, { chosen = it }, {}) } }
        compose.onNodeWithTag("attendance-tables").assertIsSelected().performClick()
        assertEquals(AttendanceDestination.TABLES, chosen)
        compose.onNodeWithText("CONTAS").assertDoesNotExist()
    }
}
