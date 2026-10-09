package com.rodada.attendance.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.asAndroidBitmap
import android.graphics.Bitmap
import androidx.test.platform.app.InstrumentationRegistry
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.text.TextLayoutResult
import org.junit.Assert.assertTrue
import org.junit.Assert.assertEquals
import org.junit.Assert.assertArrayEquals
import android.os.ParcelFileDescriptor
import org.junit.Rule
import org.junit.Test
import java.io.File

@android.annotation.TargetApi(31)
class AttendanceNavigationTest {
    @get:Rule val compose = createComposeRule()

    @Test fun geometryAndActions() {
        var chosen: AttendanceDestination? = null
        var orders = 0
        compose.setContent { RodadaTheme { AttendanceNavigation(AttendanceDestination.NOW, true, false, { chosen = it }, { orders++ }) } }
        val expanded = InstrumentationRegistry.getInstrumentation().targetContext.resources.configuration.fontScale > 1.3f
        compose.onNodeWithTag("attendance-nav").assertHeightIsEqualTo(if (expanded) 112.dp else 84.dp).assertWidthIsEqualTo((InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.widthPixels / InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.density).dp)
        compose.onNodeWithTag("attendance-order").assertWidthIsEqualTo(if (expanded) 96.dp else 128.dp).assertHeightIsEqualTo(if (expanded) 91.dp else 63.dp)
        compose.onNodeWithTag("attendance-now").assertIsSelected()
        capture("nav-now")
        assertLabelsFit()
        compose.onNodeWithTag("attendance-tabs").assertIsNotSelected().performClick()
        assertEquals(AttendanceDestination.TABS, chosen)
        compose.onNodeWithText("Mesas").assertWidthIsAtLeast(44.dp).assertHeightIsAtLeast(44.dp).performClick(); assertEquals(AttendanceDestination.TABLES, chosen)
        compose.onNodeWithText("Caixa").assertWidthIsAtLeast(44.dp).assertHeightIsAtLeast(44.dp).performClick(); assertEquals(AttendanceDestination.CASH, chosen)
        compose.onNodeWithTag("attendance-order").performClick(); assertEquals(1, orders)
    }

    @Test fun busyAndAdjacentDestination() {
        var orders = 0
        compose.setContent { RodadaTheme { AttendanceNavigation(AttendanceDestination.TABS, false, true, {}, { orders++ }) } }
        compose.onNodeWithText("Caixa").assertDoesNotExist()
        compose.onNodeWithText("Mesas").assertExists()
        compose.onNodeWithTag("attendance-tabs").assertIsSelected()
        compose.onNodeWithTag("attendance-now").assertIsNotSelected()
        compose.onNodeWithTag("attendance-order").assertIsNotEnabled().performClick()
        assertEquals(0, orders)
        capture("nav-tabs-busy")
        assertLabelsFit()
    }

    private fun assertLabelsFit() {
        for (label in listOf("AGORA", "CONTAS", "Pedir", "Mesas")) {
            val layouts = mutableListOf<TextLayoutResult>()
            compose.onNodeWithText(label, useUnmergedTree = true).performSemanticsAction(SemanticsActions.GetTextLayoutResult) { action -> assertTrue(action(layouts)) }
            assertTrue("Missing text layout: $label", layouts.isNotEmpty())
            layouts.forEach { layout ->
                for (line in 0 until layout.lineCount) {
                    assertTrue("Horizontal text clipping: $label", kotlin.math.floor(layout.getLineLeft(line)).toInt() >= 0 && kotlin.math.ceil(layout.getLineRight(line)).toInt() <= layout.size.width)
                    assertTrue("Vertical text clipping: $label", kotlin.math.floor(layout.getLineTop(line)).toInt() >= 0 && kotlin.math.ceil(layout.getLineBottom(line)).toInt() <= layout.size.height)
                }
            }
        }
    }

    private fun capture(baseName: String) {
        val metrics = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics
        val fontScale = InstrumentationRegistry.getInstrumentation().targetContext.resources.configuration.fontScale
        val name = if (metrics.widthPixels == 390 && fontScale == 1f) baseName else "$baseName-w${metrics.widthPixels}-f${(fontScale * 100).toInt()}"
        compose.mainClock.advanceTimeBy(1000)
        compose.waitForIdle()
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val dir = File(context.getExternalFilesDir(null), "v05-evidence").apply { mkdirs() }
        repeat(2) { index ->
            compose.onNodeWithTag("attendance-nav").captureToImage().asAndroidBitmap().let { bitmap ->
                File(dir, "$name-$index.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
            }
        }
        assertArrayEquals(File(dir, "$name-0.png").readBytes(), File(dir, "$name-1.png").readBytes())
        // AGP uninstalls the test app after execution; retain evidence in a shell-owned directory.
        repeat(2) { index ->
            val encoded = android.util.Base64.encodeToString(File(dir, "$name-$index.png").readBytes(), android.util.Base64.NO_WRAP)
            val shell = InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommandRw("sh")
            val script = "mkdir -p /data/local/tmp/rodada-v05-evidence\necho $encoded | base64 -d > /data/local/tmp/rodada-v05-evidence/$name-$index.png\ntest -s /data/local/tmp/rodada-v05-evidence/$name-$index.png && echo saved\n"
            ParcelFileDescriptor.AutoCloseOutputStream(shell[1]).use { it.write(script.toByteArray()) }
            val output = ParcelFileDescriptor.AutoCloseInputStream(shell[0]).use { String(it.readBytes()).trim() }
            assertEquals("saved", output)
        }
    }
}
