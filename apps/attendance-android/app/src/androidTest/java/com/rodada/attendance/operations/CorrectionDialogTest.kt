package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.corrections.CorrectionAction
import com.rodada.attendance.corrections.CorrectionCommand
import com.rodada.attendance.corrections.apiKind
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class CorrectionDialogTest {
    @get:Rule val compose = createComposeRule()
    private val item = OrderItem("item-fixture", "Item do catálogo", 800, 3, 2400, "DELIVERED")

    @Test fun cancelDeliveredRequiresReasonPinValidQuantityAndExplicitReview() {
        val commands = mutableListOf<CorrectionCommand>()
        compose.setContent { RodadaTheme { CorrectionDialog(item, emptyList(), false, {}, { command, _ -> commands += command }) } }
        val submit = compose.onNodeWithText("Cancelar", substring = false)
        submit.assertIsNotEnabled()
        compose.onNodeWithText("Motivo").performTextInput("Lançamento duplicado no teste")
        submit.assertIsNotEnabled()
        compose.onNodeWithText("Seu PIN").performTextInput("0".repeat(4))
        compose.onNodeWithContentDescription("Diminuir quantidade").assertIsNotEnabled()
        compose.onNodeWithContentDescription("Aumentar quantidade").performClick()
        compose.onNodeWithContentDescription("Quantidade: 2").assertExists()
        compose.onNodeWithContentDescription("Aumentar quantidade").performClick()
        compose.onNodeWithContentDescription("Aumentar quantidade").assertIsNotEnabled()
        compose.onNodeWithContentDescription("Diminuir quantidade").performClick()
        compose.onNodeWithContentDescription("Quantidade: 2").assertExists()
        submit.performClick()
        assertTrue(commands.isEmpty())
        compose.onNodeWithText("Confirmar cancelamento de 2 de 3 unidades de Item do catálogo.").assertExists()
        compose.onNodeWithText("Confirmar cancelamento").performClick()
        assertEquals(1, commands.size)
        assertEquals(CorrectionAction.CANCEL, commands.single().action)
        assertEquals("WRONG_ITEM_ENTERED", commands.single().apiKind)
        assertEquals(2, commands.single().quantity)
        compose.onNodeWithText("Motivo").assertDoesNotExist()
        compose.onNodeWithText("Motivo: Lançamento duplicado no teste").assertExists()
        compose.onNodeWithText("Quantidade a cancelar").assertDoesNotExist()
        compose.onNodeWithText("Seu PIN").performTextInput("0".repeat(4))
        compose.onNodeWithText("Confirmar cancelamento").performClick()
        assertEquals(commands[0], commands[1])
        captureCriticalEvidence(compose, "correction-quantity-review", compose.onNode(isDialog()))
    }

    @Test fun singleItemStillRequiresPinAndCancelDoesNotSubmit() {
        var writes = 0; var dismissed = 0
        compose.setContent { RodadaTheme { CorrectionDialog(item.copy(quantity = 1, lineTotalCents = 800), emptyList(), false, { dismissed++ }, { _, _ -> writes++ }) } }
        compose.onNodeWithText("Quantidade a cancelar: 1").assertExists()
        compose.onNodeWithText("Motivo").performTextInput("Item lançado a mais")
        compose.onNodeWithText("Cancelar", substring = false).assertIsNotEnabled()
        compose.onNodeWithText("Voltar", substring = false).performClick()
        assertEquals(0, writes); assertEquals(1, dismissed)
    }
}
