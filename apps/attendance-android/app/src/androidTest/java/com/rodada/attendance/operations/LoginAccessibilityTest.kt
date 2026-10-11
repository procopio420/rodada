package com.rodada.attendance.operations

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.ime
import androidx.compose.runtime.SideEffect
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import com.rodada.attendance.auth.AuthUiState
import com.rodada.attendance.ui.LoginScreen
import com.rodada.attendance.ui.RodadaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class LoginAccessibilityTest {
    @get:Rule val compose = createComposeRule()
    @Test fun completeLoginRemainsReachableAndClearsPin() {
        var credentials: Triple<String,String,String>? = null
        var imeBottom = 0
        compose.setContent { RodadaTheme { Surface(modifier = Modifier.fillMaxSize().safeDrawingPadding()) {
            val bottom = WindowInsets.ime.getBottom(LocalDensity.current)
            SideEffect { imeBottom = bottom }
            LoginScreen(AuthUiState(loading = false)) { venue, operator, pin -> credentials = Triple(venue,operator,pin) }
        } } }
        // The screenshot intentionally precedes all test credential input.
        captureCriticalEvidence(compose, "login", compose.onRoot())
        compose.onNode(hasSetTextAction() and hasText("Estabelecimento")).performClick()
        compose.waitUntil(10_000) { imeBottom > 0 }
        captureCriticalEvidence(compose, "login-keyboard", compose.onRoot())
        val expanded = InstrumentationRegistry.getInstrumentation().targetContext.resources.configuration.fontScale > 1.3f
        for ((label,value) in listOf("Estabelecimento" to " release-demo ", "Operador" to " release-staff ", "PIN" to "1357")) {
            val field = compose.onNode(hasSetTextAction() and hasText(label))
            if (expanded || imeBottom > 0) field.performScrollTo()
            field.assertIsDisplayed().performTextReplacement(value)
        }
        val submit = compose.onNodeWithText("Entrar")
        if (expanded || imeBottom > 0) submit.performScrollTo()
        submit.assertIsDisplayed().assertHeightIsAtLeast(44.dp).assertIsEnabled().performClick()
        assertEquals(Triple("release-demo","release-staff","1357"),credentials)
        val pin = compose.onNode(hasSetTextAction() and hasText("PIN")).fetchSemanticsNode()
        assertEquals("",pin.config[SemanticsProperties.EditableText].text)
    }
}
