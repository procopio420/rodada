package com.rodada.attendance.operations

import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.dp
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import android.graphics.Bitmap
import android.os.ParcelFileDescriptor
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayOutputStream

class CriticalFieldsTest {
    @get:Rule val compose = createComposeRule()
    private val longName = "Produto de teste com nome completo e ingredientes adicionais"

    @Test fun catalogKeepsFullIdentityAndCanonicalPrice() {
        var clicks = 0
        compose.setContent { RodadaTheme { Surface {
            CatalogProductButton(Product("fixture", longName, 123456, true, "KITCHEN", "AVAILABLE"), true, true) { clicks++ }
        } } }
        captureCriticalEvidence(compose, "catalog", compose.onNode(hasClickAction()))
        val text = compose.onNodeWithText(longName, useUnmergedTree = true)
        val layouts = mutableListOf<TextLayoutResult>()
        text.performSemanticsAction(SemanticsActions.GetTextLayoutResult) { it(layouts) }
        assertFalse("Product identity must not be ellipsized", layouts.single().hasVisualOverflow)
        compose.onNodeWithText(formatCents(123456), useUnmergedTree = true).assertIsDisplayed().assertWidthIsAtLeast(44.dp)
        val prices = mutableListOf<TextLayoutResult>()
        compose.onNodeWithText(formatCents(123456), useUnmergedTree = true).performSemanticsAction(SemanticsActions.GetTextLayoutResult) { it(prices) }
        assertEquals("Price must remain one legible line", 1, prices.single().lineCount)
        assertFalse("Price clipping: size=${prices.single().size}, width=${prices.single().didOverflowWidth}, height=${prices.single().didOverflowHeight}, lineRight=${prices.single().getLineRight(0)}, lineBottom=${prices.single().getLineBottom(0)}", prices.single().hasVisualOverflow)
        compose.onNode(hasClickAction()).assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(1, clicks)
    }

    @Test fun paymentWarningAndDecisionsRemainReachable() {
        var paid = 0
        var dismissed = 0
        compose.setContent { RodadaTheme {
            PaymentDialog(TabSummary("fixture", "Comanda teste", "OPEN", 1, 600, 0, 600), emptyList(), false, false, false,
                {}, { dismissed++ }, { _, _, _ -> paid++ })
        } }
        captureCriticalEvidence(compose, "payment", compose.onNode(isDialog()))
        compose.onNodeWithText("Abra ou selecione um caixa com turno ativo antes de receber dinheiro.").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Confirmar pagamento").assertIsNotEnabled()
        val confirm = compose.onNodeWithText("Confirmar pagamento").fetchSemanticsNode().boundsInRoot
        val cancel = compose.onNodeWithText("Cancelar").fetchSemanticsNode().boundsInRoot
        assertFalse("Payment decisions must not overlap", confirm.overlaps(cancel))
        compose.onNodeWithText("Cancelar").assertHeightIsAtLeast(44.dp).performClick()
        assertEquals(0, paid)
        assertEquals(1, dismissed)
    }

    @Test fun activeCashKeepsAmountMethodAndDestination() {
        var received: Triple<Long, PaymentMethod, String?>? = null
        compose.setContent { RodadaTheme {
            PaymentDialog(TabSummary("fixture", "Comanda teste", "OPEN", 1, 600, 0, 600),
                listOf(CashPoint("fixture-point", "Caixa de teste com identificação completa", "fixture-shift")),
                false, false, false, {}, {}, { amount, method, point -> received = Triple(amount, method, point) })
        } }
        compose.onNode(hasSetTextAction()).performTextReplacement("3,00")
        compose.onNodeWithText("Confirmar pagamento").assertHeightIsAtLeast(44.dp).assertIsEnabled().performClick()
        assertEquals(Triple(300L, PaymentMethod.CASH, "fixture-point"), received)
    }

}

internal fun captureCriticalEvidence(compose: ComposeContentTestRule, name: String, node: SemanticsNodeInteraction) {
        compose.waitForIdle()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val metrics = instrumentation.targetContext.resources.displayMetrics
        val font = instrumentation.targetContext.resources.configuration.fontScale
        val bytes = (0..1).map {
            ByteArrayOutputStream().also { output -> node.captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, output) }.toByteArray()
        }
        assertArrayEquals(bytes[0], bytes[1])
        val encoded = android.util.Base64.encodeToString(bytes[0], android.util.Base64.NO_WRAP)
        val shell = instrumentation.uiAutomation.executeShellCommandRw("sh")
        val file = "$name-w${metrics.widthPixels}-f${(font * 100).toInt()}.png"
        ParcelFileDescriptor.AutoCloseOutputStream(shell[1]).use { it.write("mkdir -p /data/local/tmp/rodada-critical-evidence\necho $encoded | base64 -d > /data/local/tmp/rodada-critical-evidence/$file\ntest -s /data/local/tmp/rodada-critical-evidence/$file && echo saved\n".toByteArray()) }
        assertEquals("saved", ParcelFileDescriptor.AutoCloseInputStream(shell[0]).use { String(it.readBytes()).trim() })
}
