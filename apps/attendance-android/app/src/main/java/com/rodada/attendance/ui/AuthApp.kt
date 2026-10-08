package com.rodada.attendance.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import com.rodada.attendance.ui.RodadaButton as Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import com.rodada.attendance.ui.RodadaOutlinedButton as OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.rodada.attendance.auth.AuthUiState
import com.rodada.attendance.auth.AuthViewModel
import com.rodada.attendance.auth.StoredSession
import com.rodada.attendance.cash.CashShiftViewModel
import com.rodada.attendance.operations.AttendanceScreen
import com.rodada.attendance.operations.OperationsViewModel

@Composable
fun AuthApp(
    viewModel: AuthViewModel,
    operationsViewModel: OperationsViewModel,
    cashShiftViewModel: CashShiftViewModel,
) {
    val state = viewModel.state
    var accountVisible by rememberSaveable { mutableStateOf(false) }

    Surface(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.fillMaxSize()) {
            if (state.session == null) {
                LoginScreen(state = state, onLogin = viewModel::login)
            } else {
                if (accountVisible) {
                    SessionScreen(
                        state = state,
                        session = state.session,
                        onBackToOperations = { accountVisible = false },
                        onSwitchOperator = viewModel::switchOperator,
                        onReauthenticate = viewModel::reauthenticate,
                        onLock = viewModel::lock,
                        onLogout = viewModel::logout,
                    )
                } else {
                    AttendanceScreen(
                        session = state.session,
                        viewModel = operationsViewModel,
                        cashShiftViewModel = cashShiftViewModel,
                        onOpenAccount = { accountVisible = true },
                    )
                }
            }

            state.errorMessage?.let { message ->
                Surface(
                    modifier =
                        Modifier
                            .align(Alignment.BottomCenter)
                            .fillMaxWidth()
                            .padding(16.dp),
                    tonalElevation = 6.dp,
                    shadowElevation = 6.dp,
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = message,
                            modifier = Modifier.weight(1f),
                            color = MaterialTheme.colorScheme.error,
                        )
                        TextButton(onClick = viewModel::dismissError) {
                            Text("Fechar")
                        }
                    }
                }
            }

            if (state.loading) {
                CircularProgressIndicator(
                    modifier =
                        Modifier
                            .align(Alignment.TopCenter)
                            .padding(top = 24.dp),
                )
            }
        }
    }
}

@Composable
private fun LoginScreen(
    state: AuthUiState,
    onLogin: (String, String, String) -> Unit,
) {
    var venueSlug by rememberSaveable { mutableStateOf("") }
    var loginIdentifier by rememberSaveable { mutableStateOf("") }
    var pin by rememberSaveable { mutableStateOf("") }

    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("Rodada Atendimento", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Entre rápido no estabelecimento. O PIN nunca é salvo pelo app.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(24.dp))

        OutlinedTextField(
            value = venueSlug,
            onValueChange = { venueSlug = it },
            label = { Text("Estabelecimento") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = loginIdentifier,
            onValueChange = { loginIdentifier = it },
            label = { Text("Operador") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = pin,
            onValueChange = { pin = it },
            label = { Text("PIN") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
        )
        Spacer(Modifier.height(20.dp))
        Button(
            onClick = {
                onLogin(venueSlug.trim(), loginIdentifier.trim(), pin)
                pin = ""
            },
            enabled =
                !state.loading &&
                    venueSlug.isNotBlank() &&
                    loginIdentifier.isNotBlank() &&
                    pin.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Entrar")
        }
    }
}

@Composable
private fun SessionScreen(
    state: AuthUiState,
    session: StoredSession,
    onBackToOperations: () -> Unit,
    onSwitchOperator: (String, String) -> Unit,
    onReauthenticate: (String) -> Unit,
    onLock: () -> Unit,
    onLogout: () -> Unit,
) {
    var switchIdentifier by rememberSaveable { mutableStateOf("") }
    var switchPin by rememberSaveable { mutableStateOf("") }
    var reauthPin by rememberSaveable { mutableStateOf("") }
    val trusted = session.deviceTrustState == "TRUSTED"

    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        TextButton(onClick = onBackToOperations, enabled = !state.loading) {
            Text("← Atendimento")
        }
        Text("Operador ativo", style = MaterialTheme.typography.labelLarge)
        Text(session.staffDisplayName, style = MaterialTheme.typography.headlineMedium)
        Text(session.venueName.ifBlank { session.venueSlug })
        Text("Função: " + session.role)
        Text("Device: " + session.deviceTrustState)

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick = onLock, enabled = !state.loading) {
                Text("Bloquear")
            }
            TextButton(onClick = onLogout, enabled = !state.loading) {
                Text("Sair")
            }
        }

        Spacer(Modifier.height(16.dp))
        Text("Trocar operador", style = MaterialTheme.typography.titleMedium)
        if (!trusted) {
            Text(
                "A troca rápida só é liberada em dispositivo confiável.",
                color = MaterialTheme.colorScheme.error,
            )
        }
        OutlinedTextField(
            value = switchIdentifier,
            onValueChange = { switchIdentifier = it },
            label = { Text("Próximo operador") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = switchPin,
            onValueChange = { switchPin = it },
            label = { Text("PIN do próximo operador") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
        )
        Button(
            onClick = {
                onSwitchOperator(switchIdentifier.trim(), switchPin)
                switchPin = ""
            },
            enabled =
                trusted &&
                    !state.loading &&
                    switchIdentifier.isNotBlank() &&
                    switchPin.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Trocar operador")
        }

        Spacer(Modifier.height(16.dp))
        Text("Confirmar ação privilegiada", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            value = reauthPin,
            onValueChange = { reauthPin = it },
            label = { Text("Seu PIN") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
        )
        Button(
            onClick = {
                onReauthenticate(reauthPin)
                reauthPin = ""
            },
            enabled = !state.loading && reauthPin.isNotBlank(),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Confirmar identidade")
        }

        state.reauthValidUntil?.let {
            Text(
                "Identidade confirmada recentemente.",
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
