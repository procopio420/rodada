package com.rodada.attendance

import android.os.Bundle
import android.os.Build
import android.content.pm.PackageManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.rodada.attendance.ui.RodadaTheme
import com.rodada.attendance.auth.AuthRepository
import com.rodada.attendance.auth.AuthViewModel
import com.rodada.attendance.cash.CashRepository
import com.rodada.attendance.cash.CashShiftViewModel
import com.rodada.attendance.corrections.CorrectionsRepository
import com.rodada.attendance.operations.OperationsRepository
import com.rodada.attendance.operations.OperationsViewModel
import com.rodada.attendance.operations.PendingMutationIntentStore
import com.rodada.attendance.refunds.RefundsRepository
import com.rodada.attendance.ui.AuthApp

class MainActivity : ComponentActivity() {
    private val authRepository by lazy { AuthRepository(applicationContext) }
    private val pendingMutationIntentStore by lazy { PendingMutationIntentStore(applicationContext) }
    private val authViewModel: AuthViewModel by viewModels {
        AuthViewModel.factory(authRepository)
    }
    private val operationsViewModel: OperationsViewModel by viewModels {
        OperationsViewModel.factory(
            repository = OperationsRepository(authRepository),
            pendingMutationIntentStore = pendingMutationIntentStore,
            authRepository = authRepository,
            correctionsRepository = CorrectionsRepository(authRepository),
            refundsRepository = RefundsRepository(authRepository),
        )
    }
    private val cashShiftViewModel: CashShiftViewModel by viewModels {
        CashShiftViewModel.factory(CashRepository(authRepository), authRepository, pendingMutationIntentStore)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (BuildConfig.DEBUG && Build.VERSION.SDK_INT >= 37 &&
            checkSelfPermission("android.permission.ACCESS_LOCAL_NETWORK") != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf("android.permission.ACCESS_LOCAL_NETWORK"), 22)
        }
        setContent {
            RodadaTheme {
                AuthApp(authViewModel, operationsViewModel, cashShiftViewModel)
            }
        }
    }
}
