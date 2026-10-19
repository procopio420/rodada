package com.rodada.attendance.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp

// TABS is retained for restoring existing saved navigation state.
enum class AttendanceDestination { NOW, TABS, TABLES, CASH }

/** PR212 fixed footer. Cash remains in the header options, gated by capability. */
@Composable
fun AttendanceNavigation(
    selected: AttendanceDestination,
    busy: Boolean,
    onSelect: (AttendanceDestination) -> Unit,
    onOrder: () -> Unit,
) {
    Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface).testTag("attendance-nav")) {
        HorizontalDivider(color = RodadaVisual.Border, thickness = 1.dp)
        Row(Modifier.fillMaxWidth().padding(7.dp)) {
            @Composable fun Item(label: String, glyph: String, tag: String, weight: Float, active: Boolean, middle: Boolean = false, action: () -> Unit) {
                val color = if (middle) RodadaVisual.Ink else if (active) RodadaVisual.Paper else RodadaVisual.Muted
                Column(Modifier.weight(weight).heightIn(min = 61.dp).clip(RoundedCornerShape(8.dp))
                    .background(if (middle) RodadaVisual.Paper else androidx.compose.ui.graphics.Color.Transparent)
                    .clickable(enabled = !busy, role = Role.Button, onClick = action).testTag(tag)
                    .semantics { this.selected = active },
                    horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    Text(glyph, style = AttendanceUx2.text(23, lineHeight = 23f), color = color)
                    Spacer(Modifier.height(4.dp))
                    Text(label, style = AttendanceUx2.text(if (middle) 13 else 11, if (middle) 850 else 750), color = color)
                }
            }
            Item("Agora", "◷", "attendance-now", 1f, selected == AttendanceDestination.NOW) { onSelect(AttendanceDestination.NOW) }
            Item("Pedir", "＋", "attendance-order", 1.15f, false, true, onOrder)
            Item("Mesas", "▦", "attendance-tables", 1f, selected in setOf(AttendanceDestination.TABLES, AttendanceDestination.TABS)) { onSelect(AttendanceDestination.TABLES) }
        }
    }
}
