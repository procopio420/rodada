package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import com.rodada.attendance.refunds.DirectRefundCommand
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class RefundFieldsTest {
    @get:Rule val compose = createComposeRule()
    private val payment = TabPayment("fixture-payment",600,"CASH","CONFIRMED",0)
    @Test fun authorizedRefundKeepsCentsReasonAndStableIntent() {
        val commands = mutableListOf<DirectRefundCommand>()
        val pins = mutableListOf<String>()
        compose.setContent { RodadaTheme {
            RefundDialog(RefundTarget.Payment(payment),listOf(payment),
                listOf(CashPoint("fixture-point","Caixa de teste com identificação completa","fixture-shift")),
                false,{}, { command,pin -> commands.add(command as DirectRefundCommand);pins.add(pin) })
        } }
        captureCriticalEvidence(compose,"refund",compose.onNode(isDialog()))
        compose.onNodeWithText("Confirme sua identidade como operador autorizado; o PIN não é salvo.").performScrollTo().assertIsDisplayed()
        val confirm = compose.onNodeWithText("Confirmar estorno")
        confirm.assertIsNotEnabled()
        compose.onNode(hasSetTextAction() and hasText("Motivo")).performScrollTo().performTextReplacement(" motivo de teste ")
        compose.onNode(hasSetTextAction() and hasText("Valor do estorno")).performScrollTo().performTextReplacement("3,00")
        val pin = compose.onNode(hasSetTextAction() and hasText("Seu PIN"))
        pin.performScrollTo().performTextReplacement("1357")
        confirm.assertHeightIsAtLeast(44.dp).assertIsEnabled().performClick()
        assertEquals(300L,commands[0].amountCents);assertEquals("motivo de teste",commands[0].reason)
        assertEquals("fixture-payment",commands[0].paymentId);assertEquals("fixture-point",commands[0].cashPointId)
        assertEquals("1357",pins[0])
        confirm.assertIsNotEnabled()
        pin.performScrollTo().performTextReplacement("1357")
        confirm.performClick()
        assertEquals(commands[0].idempotencyKey,commands[1].idempotencyKey)
        assertFalse(compose.onNodeWithText("Cancelar").fetchSemanticsNode().boundsInRoot.overlaps(confirm.fetchSemanticsNode().boundsInRoot))
        compose.onNodeWithText("Cancelar").assertHeightIsAtLeast(44.dp)
    }
}
