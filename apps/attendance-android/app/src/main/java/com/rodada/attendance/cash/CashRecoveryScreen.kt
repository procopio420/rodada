package com.rodada.attendance.cash

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.rodada.attendance.operations.RecoveryIntent
import com.rodada.attendance.operations.evidence
import com.rodada.attendance.ui.RodadaOutlinedButton
import com.rodada.attendance.ui.RodadaVisual

data class CashRecoveryContext(
    val intentId: String? = null,
    val loading: Boolean = false,
    val original: RecoveryIntent? = null,
    val detail: CashShiftDetail? = null,
    val errorMessage: String? = null,
)

@Composable
internal fun CashRecoveryScreen(state: CashRecoveryContext, onRefresh: () -> Unit, onBack: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Conferir turno original", style = MaterialTheme.typography.headlineSmall)
            Text("Consulta do registro original. Abrir esta tela não repete a operação.")
            RodadaOutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Voltar às pendências") }
        }
        if (state.loading) item { Text("Consultando turno original…") }
        state.errorMessage?.let { message -> item { Text(message, color = RodadaVisual.Amber) } }
        state.original?.let { original -> item {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(original.evidence().label, style = MaterialTheme.typography.titleMedium)
                Text("Registro ${original.id}")
                Text("Estado guardado: ${original.evidence().status}", color = RodadaVisual.Amber)
                when (original) {
                    is RecoveryIntent.CashMovement -> {
                        Text("${original.kind.name.cashRecoveryKindLabel()} · ${formatCashCents(original.amountCents)} guardados")
                        if (original.reason.isNotBlank()) Text(original.reason)
                    }
                    is RecoveryIntent.CashClose -> Text("Contagem guardada: ${formatCashCents(original.countedAmountCents)}")
                    else -> Unit
                }
            }
        } }
        state.detail?.let { detail ->
            item {
                Text("Turno ${detail.shift.id}", style = MaterialTheme.typography.titleMedium)
                Text("Data operacional: ${detail.shift.businessDate}")
                Text("${detail.shift.status.cashRecoveryStatusLabel()} · versão ${detail.shift.version}")
                Text("Esta leitura não confirma o resultado da pendência. Valores ou motivos semelhantes não comprovam a mesma operação; peça à gerência para reconciliar o registro original.", color = RodadaVisual.Amber)
                Text("Movimentos consultados: ${detail.movements.size}")
            }
            items(detail.movements, key = { it.id }) { movement ->
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("${movement.kind.cashRecoveryKindLabel()} · ${formatCashCents(movement.amountCents)}")
                    Text("Movimento ${movement.id}")
                    Text(movement.occurredAt)
                    if (movement.reason.isNotBlank()) Text(movement.reason)
                }
            }
        }
        item {
            RodadaOutlinedButton(onClick = onRefresh, enabled = !state.loading, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text("Atualizar turno original") }
        }
    }
}

private fun String.cashRecoveryStatusLabel() = when (this) {
    "OPEN" -> "Aberto"
    "COUNTING" -> "Em contagem"
    "CLOSED" -> "Encerrado"
    else -> "Estado a conferir"
}

private fun String.cashRecoveryKindLabel() = when (this) {
    "SUPPLY" -> "Suprimento"
    "WITHDRAWAL" -> "Sangria"
    "LATE_CORRECTION", "CORRECTION" -> "Correção de caixa"
    "OPENING_FLOAT" -> "Fundo inicial"
    "CASH_PAYMENT" -> "Recebimento"
    "CASH_REFUND" -> "Estorno"
    else -> "Movimento de caixa"
}
