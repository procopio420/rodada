package com.rodada.attendance.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.rodada.attendance.operations.ConnectivityState
import com.rodada.attendance.operations.label

/** Production header shared with instrumentation; state and callbacks remain canonical. */
@Composable
fun AttendanceHeader(
    staffName: String,
    connectivity: ConnectivityState,
    busy: Boolean,
    peak: Boolean,
    onTogglePeak: () -> Unit,
    onOpenAccount: () -> Unit,
    onRefresh: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth().testTag("attendance-header").padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            Text("● rodada", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Black)
            Text(staffName, style = MaterialTheme.typography.bodySmall)
            Text(
                when (connectivity) {
                    ConnectivityState.ONLINE -> "ONLINE"
                    ConnectivityState.RECONNECTING -> "VERIFICANDO"
                    ConnectivityState.STALE -> "DESATUALIZADO"
                    ConnectivityState.OFFLINE -> "SEM SINAL"
                },
                modifier = Modifier.semantics { contentDescription = connectivity.label() },
                style = MaterialTheme.typography.labelSmall,
                color = if (connectivity == ConnectivityState.ONLINE) RodadaVisual.Success else RodadaVisual.Amber,
            )
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = onTogglePeak, modifier = Modifier.heightIn(min = 44.dp).semantics { contentDescription = if (peak) "Sair do modo pico" else "Ativar modo pico" }) { Text(if (peak) "Pico ●" else "Pico", color = RodadaVisual.Amber) }
            TextButton(onClick = onRefresh, enabled = !busy, modifier = Modifier.heightIn(min = 44.dp)) { Text("Atualizar") }
            RodadaOutlinedButton(onClick = onOpenAccount, enabled = !busy) { Text("Conta") }
        }
    }
}
