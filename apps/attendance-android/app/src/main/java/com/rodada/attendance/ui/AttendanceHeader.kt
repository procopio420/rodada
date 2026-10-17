package com.rodada.attendance.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.rodada.attendance.R
import com.rodada.attendance.operations.ConnectivityState
import com.rodada.attendance.operations.label

/** PR212 compact header. Operational options remain accessible through its metadata. */
@Composable
fun AttendanceHeader(
    staffName: String,
    connectivity: ConnectivityState,
    busy: Boolean,
    peak: Boolean,
    onTogglePeak: () -> Unit,
    onOpenAccount: () -> Unit,
    onRefresh: () -> Unit,
    venueName: String = "",
    canUseCash: Boolean = false,
    onOpenCash: () -> Unit = {},
    onOpenRecovery: () -> Unit = {},
    pendingCount: Int = 0,
) {
    var options by remember { mutableStateOf(false) }
    val horizontalInset = if (LocalConfiguration.current.screenWidthDp <= 375) 15.dp else 22.dp
    Column(Modifier.fillMaxWidth().testTag("attendance-header")) {
        Row(Modifier.fillMaxWidth().heightIn(min = 71.dp).padding(horizontal = horizontalInset),
            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Image(painterResource(R.drawable.rodada_wordmark), "Rodada", Modifier.width(113.dp).height(42.dp))
            Box(Modifier.weight(1f), contentAlignment = Alignment.CenterEnd) {
                Column(Modifier.fillMaxWidth().heightIn(min = 44.dp).clickable { options = true }
                    .testTag("attendance-options").semantics { contentDescription = "Opções do atendimento" },
                    horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.Center) {
                    if (venueName.isNotBlank()) {
                        Text(venueName, modifier = Modifier.fillMaxWidth(), style = AttendanceUx2.text(13, 750, 15.6f), maxLines = 1,
                            overflow = TextOverflow.Ellipsis, textAlign = TextAlign.End)
                        Spacer(Modifier.height(5.dp))
                    }
                    Text("$staffName · ${when(connectivity) {
                        ConnectivityState.ONLINE -> "online"
                        ConnectivityState.RECONNECTING -> "verificando"
                        ConnectivityState.STALE -> "desatualizado"
                        ConnectivityState.OFFLINE -> "sem sinal"
                    }}", style = AttendanceUx2.text(11, lineHeight = 13.2f), color = RodadaVisual.Muted,
                        modifier = Modifier.fillMaxWidth().testTag("attendance-connectivity").semantics { contentDescription = connectivity.label() },
                        maxLines = 1, overflow = TextOverflow.Ellipsis, textAlign = TextAlign.End)
                }
                DropdownMenu(expanded = options, onDismissRequest = { options = false }) {
                    Column(Modifier.padding(horizontal = 12.dp, vertical = 8.dp)) {
                        Text(venueName, style = MaterialTheme.typography.bodySmall)
                        Text(staffName, style = MaterialTheme.typography.bodySmall)
                    }
                    DropdownMenuItem(text = { Text("Conta") }, enabled = !busy,
                        onClick = { options = false; onOpenAccount() })
                    DropdownMenuItem(text = { Text("Atualizar") }, enabled = !busy,
                        onClick = { options = false; onRefresh() })
                    DropdownMenuItem(text = { Text(if (peak) "Sair do modo pico" else "Ativar modo pico") },
                        onClick = { options = false; onTogglePeak() })
                    if (canUseCash) DropdownMenuItem(text = { Text("Caixa") }, enabled = !busy,
                        onClick = { options = false; onOpenCash() })
                    DropdownMenuItem(text = { Text("Pendências locais · $pendingCount") },
                        onClick = { options = false; onOpenRecovery() })
                }
            }
        }
        HorizontalDivider(color = RodadaVisual.Border, thickness = 1.dp)
    }
}
