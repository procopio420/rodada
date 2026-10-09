package com.rodada.attendance.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Measures from night/Main.dc.html .nav/.nb/.ngo; system insets belong to AuthApp. */
object AttendanceNavTokens {
    val Height = 84.dp
    val ExpandedHeight = 112.dp
    val ExpandedCenter = 104.dp
    val Bottom = 8.dp
    val Center = 136.dp
    val Radius = 12.dp
    val Icon = 24.dp
    val Gap = 5.dp
    val Marker = 3.dp
    val KeyShadow = 4.dp
}

enum class AttendanceDestination { NOW, TABS, TABLES, CASH }

@Composable
fun AttendanceNavigation(
    selected: AttendanceDestination,
    canUseCash: Boolean,
    busy: Boolean,
    onSelect: (AttendanceDestination) -> Unit,
    onOpenTab: () -> Unit,
) {
    val expanded = LocalDensity.current.fontScale > 1.3f
    Column(Modifier.fillMaxWidth().background(RodadaVisual.Surface)) {
        // Operational extension absent from the export: retain all existing destinations.
        Row(Modifier.fillMaxWidth().testTag("attendance-extra"), horizontalArrangement = Arrangement.SpaceEvenly) {
            ExtraDestination("Mesas", AttendanceDestination.TABLES, selected, onSelect)
            if (canUseCash) ExtraDestination("Caixa", AttendanceDestination.CASH, selected, onSelect)
        }
        Box(Modifier.fillMaxWidth().height(if (expanded) AttendanceNavTokens.ExpandedHeight else AttendanceNavTokens.Height).testTag("attendance-nav")) {
            Box(Modifier.fillMaxWidth().height(1.dp).background(RodadaVisual.Border))
            Row(Modifier.fillMaxSize().padding(top = 1.dp, bottom = AttendanceNavTokens.Bottom)) {
                NavDestination("AGORA", AttendanceDestination.NOW, selected, Modifier.weight(1f), onSelect)
                Box(Modifier.width(if (expanded) AttendanceNavTokens.ExpandedCenter else AttendanceNavTokens.Center).fillMaxHeight().padding(start = 4.dp, end = 4.dp, top = 10.dp, bottom = 2.dp)) {
                    Column(
                        Modifier.fillMaxSize().clip(RoundedCornerShape(AttendanceNavTokens.Radius))
                            .background(if (busy) RodadaVisual.Control else RodadaVisual.Paper)
                            .drawWithContent {
                                drawContent()
                                drawRect(RodadaVisual.Ink.copy(alpha = .2f), topLeft = Offset(0f, size.height - AttendanceNavTokens.KeyShadow.toPx()), size = androidx.compose.ui.geometry.Size(size.width, AttendanceNavTokens.KeyShadow.toPx()))
                            }
                            .clickable(enabled = !busy, role = Role.Button, onClick = onOpenTab)
                            .testTag("attendance-order"),
                        verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        val ink = if (busy) RodadaVisual.Muted else RodadaVisual.Ink
                        if (expanded) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(AttendanceNavTokens.Gap)) {
                                OrderIcon(ink)
                                OrderLabel(ink)
                            }
                        } else {
                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                OrderIcon(ink)
                                OrderLabel(ink)
                            }
                        }
                    }
                }
                NavDestination("CONTAS", AttendanceDestination.TABS, selected, Modifier.weight(1f), onSelect)
            }
        }
    }
}

@Composable
private fun ExtraDestination(label: String, destination: AttendanceDestination, active: AttendanceDestination, onSelect: (AttendanceDestination) -> Unit) {
    Box(Modifier.padding(horizontal = 16.dp).sizeIn(minWidth = 44.dp, minHeight = 44.dp).semantics { selected = active == destination }
        .clickable(role = Role.Tab, onClick = { onSelect(destination) }), contentAlignment = Alignment.Center) {
        Text(label, color = if (active == destination) RodadaVisual.Paper else RodadaVisual.Muted)
    }
}

@Composable
private fun NavDestination(label: String, destination: AttendanceDestination, active: AttendanceDestination, modifier: Modifier, onSelect: (AttendanceDestination) -> Unit) {
    val color = if (active == destination) RodadaVisual.Paper else RodadaVisual.Subtle
    Box(modifier.fillMaxHeight().semantics { selected = active == destination }
        .clickable(role = Role.Tab, onClick = { onSelect(destination) }).testTag("attendance-${destination.name.lowercase()}")) {
        if (active == destination) Box(Modifier.align(Alignment.TopCenter).fillMaxWidth(.48f).height(AttendanceNavTokens.Marker).background(RodadaVisual.Paper))
        Column(Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(AttendanceNavTokens.Gap)) {
            Canvas(Modifier.size(AttendanceNavTokens.Icon)) {
                val u = size.width / 24f
                val stroke = Stroke(2.2f * u)
                if (destination == AttendanceDestination.NOW) {
                    drawCircle(color, 8f*u, Offset(12f*u,13f*u), style = stroke)
                    drawLine(color,Offset(12f*u,9f*u),Offset(12f*u,13f*u),2.2f*u)
                    drawLine(color,Offset(12f*u,13f*u),Offset(14.5f*u,15.5f*u),2.2f*u)
                    drawLine(color,Offset(9.5f*u,2.5f*u),Offset(14.5f*u,2.5f*u),2.2f*u)
                } else {
                    drawCircle(color,3.5f*u,Offset(9f*u,8f*u),style=stroke)
                    drawArc(color,180f,180f,false,Offset(2.5f*u,13.5f*u),androidx.compose.ui.geometry.Size(13f*u,13f*u),style=stroke)
                    drawArc(color,-90f,180f,false,Offset(12.5f*u,4.5f*u),androidx.compose.ui.geometry.Size(7f*u,7f*u),style=stroke)
                    drawArc(color,-90f,90f,false,Offset(15.5f*u,14.5f*u),androidx.compose.ui.geometry.Size(6f*u,11f*u),style=stroke)
                }
            }
            Text(label, color=color, style=TextStyle(fontFamily=RodadaVisual.Label,fontWeight=FontWeight.ExtraBold,fontSize=14.sp,letterSpacing=1.4.sp,lineHeight=if (LocalDensity.current.fontScale > 1.3f) 16.sp else TextUnit.Unspecified))
        }
    }
}

@Composable
private fun OrderIcon(ink: androidx.compose.ui.graphics.Color) {
    Canvas(Modifier.size(22.dp)) {
        val u = size.width / 24f
        drawLine(ink, Offset(12f*u, 5f*u), Offset(12f*u, 19f*u), 3f*u)
        drawLine(ink, Offset(5f*u, 12f*u), Offset(19f*u, 12f*u), 3f*u)
    }
}

@Composable
private fun OrderLabel(ink: androidx.compose.ui.graphics.Color) {
    Text("Pedir", color = ink,
        style = TextStyle(fontFamily = RodadaVisual.Label, fontWeight = FontWeight.Black, fontSize = 18.sp, letterSpacing = 1.44.sp))
}
