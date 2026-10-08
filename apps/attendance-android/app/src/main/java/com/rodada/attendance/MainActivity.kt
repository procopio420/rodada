package com.rodada.attendance

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.AuthViewModel
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.operations.OperationsRepository
import com.rodada.attendance.operations.OperationsViewModel
import com.rodada.attendance.operations.PendingMutationIntentStore
import com.rodada.attendance.refunds.RefundsRepository
import com.rodada.attendance.ui.AuthApp

class MainActivity : ComponentActivity() {
    private val authRepository by lazy { AuthRepository(applicationContext) }
    private val authViewModel: AuthViewModel by viewModels {
        AuthViewModel.factory(authRepository)
    }
    private val operationsViewModel: OperationsViewModel by viewModels {
        OperationsViewModel.factory(
            repository = OperationsRepository(authRepository),
            pendingMutationIntentStore = PendingMutationIntentStore(applicationContext),
            authRepository = authRepository,
            correctionsRepository = CorrectionsRepository(authRepository),
            refundsRepository = RefundsRepository(authRepository),
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                AuthApp(authViewModel, operationsViewModel)
            }
        }
    }
}
