package com.rodada.attendance.auth

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import java.io.IOException

class AuthViewModel(
    private val repository: AuthRepository,
) : ViewModel() {
    var state by mutableStateOf(AuthUiState())
        private set

    init {
        restore()
    }

    fun restore() {
        state = state.copy(loading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching { repository.restoreSession() }
                .onSuccess { session ->
                    state = AuthUiState(loading = false, session = session)
                }
                .onFailure(::showFailure)
        }
    }

    fun login(
        venueSlug: String,
        loginIdentifier: String,
        pin: String,
    ) {
        launchAction {
            val session = repository.login(venueSlug, loginIdentifier, pin)
            state = AuthUiState(loading = false, session = session)
        }
    }

    fun switchOperator(
        loginIdentifier: String,
        pin: String,
    ) {
        val current = state.session ?: return
        launchAction {
            val next = repository.switchOperator(current, loginIdentifier, pin)
            state = AuthUiState(loading = false, session = next)
        }
    }

    fun reauthenticate(pin: String) {
        val current = state.session ?: return
        launchAction {
            val receipt = repository.reauthenticate(current, pin)
            state =
                state.copy(
                    loading = false,
                    errorMessage = null,
                    reauthValidUntil = receipt.validUntil,
                )
        }
    }

    fun lock() {
        val current = state.session ?: return
        launchAction(clearOnFailure = true) {
            repository.lock(current)
            state = AuthUiState(loading = false)
        }
    }

    fun logout() {
        val current = state.session ?: return
        launchAction(clearOnFailure = true) {
            repository.logout(current)
            state = AuthUiState(loading = false)
        }
    }

    fun dismissError() {
        state = state.copy(errorMessage = null)
    }

    private fun launchAction(
        clearOnFailure: Boolean = false,
        block: suspend () -> Unit,
    ) {
        state = state.copy(loading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching { block() }
                .onFailure { error ->
                    if (clearOnFailure) {
                        repository.clearLocalSession()
                        state = AuthUiState(loading = false)
                    } else {
                        showFailure(error)
                    }
                }
        }
    }

    private fun showFailure(error: Throwable) {
        val message =
            when (error) {
                is AuthApiException -> error.code + ": " + error.message
                is IOException -> "Sem conexão com o Rodada."
                else -> error.message ?: "Falha inesperada."
            }

        if (
            error is AuthApiException &&
                error.code in
                    setOf(
                        "SESSION_REVOKED",
                        "SESSION_SUPERSEDED",
                        "SESSION_EXPIRED",
                        "MEMBERSHIP_REVOKED",
                        "MEMBERSHIP_SUSPENDED",
                        "DEVICE_REVOKED",
                        "STAFF_INACTIVE",
                    )
        ) {
            repository.clearLocalSession()
            state = AuthUiState(loading = false, errorMessage = message)
            return
        }

        state = state.copy(loading = false, errorMessage = message)
    }

    companion object {
        fun factory(repository: AuthRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return AuthViewModel(repository) as T
                }
            }
    }
}
