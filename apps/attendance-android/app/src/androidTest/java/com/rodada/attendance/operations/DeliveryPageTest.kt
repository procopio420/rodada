package com.rodada.attendance.operations

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.assertEquals

class DeliveryPageTest {
    @get:Rule val compose = createComposeRule()
    private val task = DeliveryTask("original-task", "OPEN", "Mesa 08", "Chopp Pilsen", 2, "Rafael", 30,
        StaffTaskTarget.Unavailable, "BAR", "original-item", "original-order", itemState = "READY", tabReference = "#1049")
    @Test fun openingAndBackNeverCompleteWhileClosedTabTargetIsNotRequired() {
        var back = 0; var completed = 0
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { Column(Modifier.fillMaxSize()) { com.rodada.attendance.ui.AttendanceHeader("Lucas", ConnectivityState.ONLINE, false, false, {}, {}, {}, venueName = "Bar do Aderlan")
Box(Modifier.weight(1f)) { DeliveryTaskDetail(task, false, "staff", { back++ }, {}, { completed++ }) } } } } }
        compose.onNodeWithText("Levar pedido.").assertIsDisplayed()
        compose.onNodeWithText("2× Chopp Pilsen").assertExists()
        compose.onNodeWithText("Origem · Bar").assertExists()
        assertEquals(0, completed)
        captureCriticalEvidence(compose, "ux2-delivery-page", compose.onRoot())
        compose.onNodeWithText("Voltar sem entregar").performScrollTo().performClick()
        assertEquals(1, back); assertEquals(0, completed)
    }
    @Test fun rivalOwnershipCannotComplete() {
        var completed = 0
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { DeliveryTaskDetail(task.copy(claimedById = "other"), false, "staff", {}, {}, { completed++ }) } } }
        compose.onNodeWithText("Confirmar entrega").assertIsDisplayed().assertIsNotEnabled()
        assertEquals(0, completed)
    }
    @Test fun missingTaskDoesNotOfferMutation() {
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { DeliveryTaskDetail(null, false, "staff", {}, {}, {}) } } }
        compose.onNodeWithText("Confirmar entrega").assertDoesNotExist()
        compose.onNodeWithText("‹  Voltar").performClick()
    }
    @Test fun changedProductionStateCannotAppearReadyOrComplete() {
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { DeliveryTaskDetail(task.copy(itemState = "DELIVERED"), false, "staff", {}, {}, {}) } } }
        compose.onNodeWithText("Pronto para entrega").assertDoesNotExist()
        compose.onNodeWithText("Entregue").assertExists()
        compose.onNodeWithText("Confirmar entrega").assertIsNotEnabled()
    }

    @Test fun busyBackIsReadOnlyAndDoesNotClearOrRepeatTheMutation() {
        var completed = 0; var backs = 0
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { DeliveryTaskDetail(task, true, "staff", { backs++ }, {}, { completed++ }) } } }
        compose.onNodeWithText("Confirmar entrega").assertIsNotEnabled()
        compose.onNodeWithText("Voltar sem entregar").performScrollTo().performClick()
        assertEquals(1, backs); assertEquals(0, completed)
    }

    @Test fun pickedUpRemainsDeliverableWithoutClaimOnOpening() {
        var completed = 0
        compose.setContent { RodadaTheme { Surface(color = com.rodada.attendance.ui.RodadaVisual.Ground) { DeliveryTaskDetail(task.copy(itemState = "PICKED_UP"), false, "staff", {}, {}, { completed++ }) } } }
        compose.onAllNodesWithText("Em entrega").assertCountEquals(2)
        compose.onNodeWithText("Pronto para entrega").assertDoesNotExist()
        compose.onNodeWithText("Confirmar entrega").assertIsEnabled()
        assertEquals(0, completed)
        compose.onNodeWithText("Confirmar entrega").performClick()
        assertEquals(1, completed)
    }

}
