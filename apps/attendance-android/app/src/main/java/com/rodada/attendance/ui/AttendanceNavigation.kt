package com.rodada.attendance.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

enum class AttendanceDestination { NOW, TABS, TABLES, CASH }

/** The Web flow has one destination for physical tables and financial Tabs. */
@Composable
fun AttendanceNavigation(
    selected: AttendanceDestination,
    canUseCash: Boolean,
    busy: Boolean,
    onSelect: (AttendanceDestination) -> Unit,
    onOrder: () -> Unit,
    openTabLabel: String = "Pedir",
) {
    Column(Modifier.fillMaxWidth().testTag("attendance-nav").padding(horizontal = 16.dp, vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { onSelect(AttendanceDestination.TABLES) }, enabled = !busy,
                shape = RoundedCornerShape(8.dp), border = BorderStroke(1.dp, RodadaVisual.Border),
                colors = ButtonDefaults.outlinedButtonColors(containerColor = if (selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS)) RodadaVisual.Paper else RodadaVisual.Control, contentColor = if (selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS)) RodadaVisual.Ink else RodadaVisual.Paper),
                modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("attendance-tables").semantics { this.selected = selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS) }) { Text("Mesas e comandas") }
            OutlinedButton(onClick = { onSelect(AttendanceDestination.NOW) }, enabled = !busy,
                shape = RoundedCornerShape(8.dp), border = BorderStroke(1.dp, RodadaVisual.Border),
                colors = ButtonDefaults.outlinedButtonColors(containerColor = if (selected == AttendanceDestination.NOW) RodadaVisual.Paper else RodadaVisual.Control, contentColor = if (selected == AttendanceDestination.NOW) RodadaVisual.Ink else RodadaVisual.Paper),
                modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("attendance-now").semantics { this.selected = selected == AttendanceDestination.NOW }) { Text("Agora") }
        }
        if (canUseCash) RodadaOutlinedButton(onClick = { onSelect(AttendanceDestination.CASH) }, enabled = !busy,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).semantics { this.selected = selected == AttendanceDestination.CASH }) { Text("Caixa") }
    }
}