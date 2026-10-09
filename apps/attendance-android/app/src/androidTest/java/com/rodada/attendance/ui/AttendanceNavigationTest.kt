package com.rodada.attendance.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.asAndroidBitmap
import android.graphics.Bitmap
import androidx.test.platform.app.InstrumentationRegistry
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
        compose.onNodeWithTag("attendance-nav").assertHeightIsEqualTo(84.dp).assertWidthIsEqualTo(390.dp)
        compose.onNodeWithTag("attendance-order").assertWidthIsEqualTo(128.dp).assertHeightIsEqualTo(63.dp)
        compose.onNodeWithTag("attendance-now").assertIsSelected()
        capture("nav-now")
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
    }

    private fun capture(name: String) {
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
