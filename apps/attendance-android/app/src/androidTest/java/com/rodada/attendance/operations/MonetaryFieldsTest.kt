package com.rodada.attendance.operations

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import com.rodada.attendance.auth.AuthTokens
import com.rodada.attendance.auth.StoredSession
import org.json.JSONObject

class MonetaryFieldsTest {
    @get:Rule val compose = createComposeRule()

    @Test fun invalidPaymentRemainsBlockedAndDotDecimalKeepsExactCents() {
        var received: Triple<Long, PaymentMethod, String?>? = null
        compose.setContent { RodadaTheme {
            PaymentDialog(TabSummary("fixture", "Comanda de teste", "OPEN", 1, 3800, 1000, 2800),
                listOf(CashPoint("fixture-point", "Caixa de teste", "fixture-shift")),
                false, false, false, {}, {}, { cents, method, point -> received = Triple(cents, method, point) })
        } }
        val field = compose.onNode(hasSetTextAction() and hasText("Valor"))
        field.performScrollTo().performClick()
        assertEditorType(android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL)
        for (invalid in listOf("-3,00", "abc3,00", "3.000", "92233720368547758.08", "0", "28,01")) {
            field.performScrollTo().performTextReplacement(invalid)
            compose.onNodeWithText("Confirmar pagamento").assertIsNotEnabled()
            assertEquals(null, received)
        }
        field.performTextReplacement("3.00")
        compose.onNodeWithText("Confirmar pagamento").assertIsEnabled().performClick()
        assertEquals(Triple(300L, PaymentMethod.CASH, "fixture-point"), received)
    }

    @Test fun invalidPartialTransferDoesNotCreateZeroCommand() {
        val session = StoredSession(AuthTokens("", "", "", ""), "fixture-staff", "Operador de teste",
            "fixture-venue", "fixture", "Estabelecimento de teste", "MANAGER", "fixture-device", "UNTRUSTED", setOf("tab.transfer"))
        val source = JSONObject("""{"tab":{"state":"OPEN","version":1,"exposure_cents":800},"lines":[{"charge_id":"charge","available_cents":800,"unit_price_cents":800,"product_name":"Produto de teste","original_tab_id":"source"}]}""")
        var preview: JSONObject? = null
        var committed = 0
        compose.setContent { RodadaTheme {
            TabOperationsDialog(session, OperationsUiState(operationState = source, connectivity = ConnectivityState.ONLINE),
                {}, { preview = it }, { committed++ }, {}, {})
        } }
        compose.onNodeWithText("Dividir conta").performScrollTo().performClick()
        val field = compose.onNode(hasSetTextAction() and hasText("Ou valor parcial (R$)"))
        field.performScrollTo().performTextReplacement("abc3,00")
        compose.onNode(hasScrollAction()).performScrollToNode(hasText("Conferir transferência"))
        compose.onNodeWithText("Conferir transferência").assertIsNotEnabled()
        assertEquals(null, preview)
        field.performScrollTo().performTextReplacement("3.00")
        compose.onNode(hasScrollAction()).performScrollToNode(hasText("Conferir transferência"))
        compose.onNodeWithText("Conferir transferência").assertIsEnabled().performClick()
        assertEquals(300L, preview!!.getJSONArray("lines").getJSONObject(0).getLong("amount_cents"))
        assertEquals(0, committed)
    }

    @Test fun limitKeepsReasonPinAndExactDecimalBeforeApproval() {
        var approved: Long? = null
        var receivedPin: String? = null
        compose.setContent { RodadaTheme {
            LimitResolutionDialog(TabSummary("fixture", "Comanda de teste", "OPEN", 1, 800, 0, 800),
                true, false, null, {}, { cents, reason, pin, _, _ ->
                    approved = cents; receivedPin = pin; assertEquals("Revisão de teste", reason)
                })
        } }
        val amount = compose.onNode(hasSetTextAction() and hasText("Novo limite total (R$)"))
        amount.performScrollTo().performTextReplacement("-31,00")
        compose.onNodeWithText("Aprovar").assertIsNotEnabled()
        amount.performTextReplacement("31.00")
        compose.onNode(hasSetTextAction() and hasText("Motivo")).performScrollTo().performTextReplacement("Revisão de teste")
        compose.onNode(hasSetTextAction() and hasText("Seu PIN")).performScrollTo().performTextReplacement("1357")
        compose.onNodeWithText("Aprovar").assertIsEnabled().performClick()
        assertEquals(3100L, approved)
        assertEquals("1357", receivedPin)
    }
}

internal fun assertEditorType(requiredFlag: Int) {
    val automation = androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().uiAutomation
    val dump = android.os.ParcelFileDescriptor.AutoCloseInputStream(automation.executeShellCommand("dumpsys input_method"))
        .use { String(it.readBytes()) }
    val type = Regex("inputType=0x([0-9a-fA-F]+)").find(dump)?.groupValues?.get(1)?.toInt(16)
    assertTrue("Focused editor must report number class and required flags", type != null &&
        (type and android.text.InputType.TYPE_MASK_CLASS) == android.text.InputType.TYPE_CLASS_NUMBER && (type and requiredFlag) == requiredFlag)
}
