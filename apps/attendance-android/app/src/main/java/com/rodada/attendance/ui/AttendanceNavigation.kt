package com.rodada.attendance.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
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
            RodadaOutlinedButton(onClick = { onSelect(AttendanceDestination.NOW) }, enabled = !busy,
                tone = if (selected == AttendanceDestination.NOW) RodadaButtonTone.ACTIVE else RodadaButtonTone.NEUTRAL,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("attendance-now").semantics { this.selected = selected == AttendanceDestination.NOW }) { Text("Agora") }
            RodadaButton(onClick = onOrder, enabled = !busy,
                modifier = Modifier.weight(1.2f).heightIn(min = 56.dp).testTag("attendance-order")) { Text("+ Pedir") }
            RodadaOutlinedButton(onClick = { onSelect(AttendanceDestination.TABLES) }, enabled = !busy,
                tone = if (selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS)) RodadaButtonTone.ACTIVE else RodadaButtonTone.NEUTRAL,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("attendance-tables").semantics { this.selected = selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS) }) { Text("Mesas") }
        }
        if (canUseCash) RodadaOutlinedButton(onClick = { onSelect(AttendanceDestination.CASH) }, enabled = !busy,
            tone = if (selected == AttendanceDestination.CASH) RodadaButtonTone.ACTIVE else RodadaButtonTone.NEUTRAL,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).semantics { this.selected = selected == AttendanceDestination.CASH }) { Text("Caixa") }
    }
}