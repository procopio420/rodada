package com.rodada.attendance.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.rodada.attendance.operations.*
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import java.io.IOException

class PartySizeEditorTest {
    @get:Rule val compose = createComposeRule()

    @Test fun unknownConflictAndSamePayloadRetry() {
        var current = PartySizeSnapshot(null, 0, null)
        val commands = mutableListOf<PartySizeCommand>()
        compose.setContent { RodadaTheme { PartySizeEditor(load = { current }, save = { command ->
            commands += command
            when (commands.size) {
                1 -> { current = PartySizeSnapshot(3, 1, "GUEST"); throw OperationsApiException(409, "VERSION_CONFLICT", "Quantidade alterada.") }
                2 -> throw IOException("test-only lost response")
                else -> PartySizeSnapshot(4, 2, "STAFF").also { current = it }
            }
        }) } }
        compose.onNodeWithText("Pessoas na ocupação").performClick()
        compose.onNodeWithText("Quantidade não informada").assertIsDisplayed()
        compose.onNodeWithText("Quantidade de pessoas").performTextInput("4")
        compose.onNodeWithText("Confirmar quantidade").performClick()
        compose.waitUntil { commands.size == 1 }
        compose.onNodeWithText("3 pessoa(s) · Informado pelo cliente").assertExists()
        compose.onNodeWithText("Confirmar quantidade").performClick()
        compose.waitUntil { commands.size == 2 }
        compose.onNodeWithText("Verificar mesma quantidade").performClick()
        compose.waitUntil { commands.size == 3 }
        compose.onNodeWithText("Quantidade confirmada.").assertExists()
        assertEquals(commands[1], commands[2])
        assertEquals(1, commands[1].version)
    }
}
