package com.rodada.attendance.ui

import android.graphics.Bitmap
import android.os.ParcelFileDescriptor
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.material3.Surface
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.operations.ConnectivityState
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import java.io.ByteArrayOutputStream
import kotlin.math.ceil
import kotlin.math.floor

class AttendanceHeaderTest {
    @get:Rule val compose = createComposeRule()
    @Test fun longNameAndActionsFit() {
        var peaks = 0; var accounts = 0; var refreshes = 0
        compose.setContent { RodadaTheme { Surface { AttendanceHeader("Operador de teste com nome completo e sobrenomes", ConnectivityState.STALE, false, false, { peaks++ }, { accounts++ }, { refreshes++ }) } } }
        capture("header-long")
        assertTextFits()
        compose.onNodeWithContentDescription("Ativar modo pico").assertHeightIsAtLeast(44.dp).assertWidthIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("Atualizar").assertHeightIsAtLeast(44.dp).assertWidthIsAtLeast(44.dp).performClick()
        compose.onNodeWithText("Conta").assertHeightIsAtLeast(44.dp).assertWidthIsAtLeast(44.dp).performClick()
        assertEquals(1, peaks); assertEquals(1, accounts); assertEquals(1, refreshes)
    }
    @Test fun busyPreservesPeakAndCanonicalConnectivity() {
        var peaks = 0; var accounts = 0; var refreshes = 0
        compose.setContent { RodadaTheme { Surface { AttendanceHeader("Operador teste", ConnectivityState.RECONNECTING, true, true, { peaks++ }, { accounts++ }, { refreshes++ }) } } }
        capture("header-busy")
        assertTextFits()
        compose.onNodeWithText("Atualizar").assertIsNotEnabled()
        compose.onNodeWithText("Conta").assertIsNotEnabled()
        compose.onNodeWithContentDescription("Sair do modo pico").performClick()
        assertEquals(1, peaks); assertEquals(0, accounts); assertEquals(0, refreshes)
        compose.onNodeWithText("VERIFICANDO").assertExists()
        compose.onNodeWithText("ONLINE").assertDoesNotExist()
    }
    private fun assertTextFits() {
        compose.onAllNodes(SemanticsMatcher.keyIsDefined(SemanticsActions.GetTextLayoutResult), useUnmergedTree = true).fetchSemanticsNodes().forEach { node ->
            val layouts = mutableListOf<TextLayoutResult>()
            node.config[SemanticsActions.GetTextLayoutResult].action?.invoke(layouts)
            layouts.forEach { layout ->
                for (line in 0 until layout.lineCount) {
                    assertTrue("Text right clipped: ${layout.layoutInput.text}", ceil(layout.getLineRight(line)) <= layout.size.width)
                    assertTrue("Text left clipped: ${layout.layoutInput.text}", floor(layout.getLineLeft(line)) >= 0)
                    assertTrue("Text bottom clipped: ${layout.layoutInput.text}", ceil(layout.getLineBottom(line)) <= layout.size.height)
                    assertTrue("Text top clipped: ${layout.layoutInput.text}", floor(layout.getLineTop(line)) >= 0)
                }
            }
        }
    }
    private fun capture(name: String) {
        compose.waitForIdle()
        val metrics = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics
        val font = InstrumentationRegistry.getInstrumentation().targetContext.resources.configuration.fontScale
        val bytes = (0..1).map {
            ByteArrayOutputStream().also { out -> compose.onNodeWithTag("attendance-header").captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, out) }.toByteArray()
        }
        assertArrayEquals(bytes[0], bytes[1])
        val encoded = android.util.Base64.encodeToString(bytes[0], android.util.Base64.NO_WRAP)
        val shell = InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommandRw("sh")
        val file = "$name-w${metrics.widthPixels}-f${(font * 100).toInt()}.png"
        ParcelFileDescriptor.AutoCloseOutputStream(shell[1]).use { it.write("mkdir -p /data/local/tmp/rodada-header-evidence\necho $encoded | base64 -d > /data/local/tmp/rodada-header-evidence/$file\ntest -s /data/local/tmp/rodada-header-evidence/$file && echo saved\n".toByteArray()) }
        assertEquals("saved", ParcelFileDescriptor.AutoCloseInputStream(shell[0]).use { String(it.readBytes()).trim() })
    }
}
