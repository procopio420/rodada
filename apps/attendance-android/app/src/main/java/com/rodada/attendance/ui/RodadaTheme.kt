package com.rodada.attendance.ui

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rodada.attendance.R

/** Shared spec 022 tokens; fonts are bundled OFL faces, never downloaded on device. */
object RodadaVisual {
    val Ground = Color(0xFF120F0C)
    val Surface = Color(0xFF1B1713)
    val Control = Color(0xFF252019)
    val Border = Color(0xFF3A3228)
    val Paper = Color(0xFFF3ECE1)
    val Ink = Color(0xFF17130F)
    val Muted = Color(0xFFBBAE9B)
    val Amber = Color(0xFFF5A524)
    val Success = Color(0xFF93DB8C)
    val Danger = Color(0xFFFF5D47)
    val Info = Color(0xFF82B8FF)
    val Money = Color(0xFFC3A6FF)
    val Body = FontFamily(Font(R.font.archivo_body))
    val Heading = FontFamily(Font(R.font.archivo_heading, FontWeight.Black))
    val Label = FontFamily(Font(R.font.archivo_label, FontWeight.ExtraBold))
    val Number = FontFamily(Font(R.font.jetbrains_mono))
}

// Compatibility for payment/operations components introduced on main.
val RodadaMono = RodadaVisual.Number

@Composable
fun RodadaTheme(content: @Composable () -> Unit) {
    val base = Typography()
    val body = TextStyle(fontFamily = RodadaVisual.Body, fontSize = 16.sp, lineHeight = 22.sp)
    val title = TextStyle(fontFamily = RodadaVisual.Heading, fontWeight = FontWeight.Black, fontSize = 32.sp, lineHeight = 34.sp)
    val label = TextStyle(fontFamily = RodadaVisual.Label, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, letterSpacing = .8.sp)
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = RodadaVisual.Paper, onPrimary = RodadaVisual.Ink,
            secondary = RodadaVisual.Amber, onSecondary = RodadaVisual.Ink,
            tertiary = RodadaVisual.Info, onTertiary = RodadaVisual.Ink,
            background = RodadaVisual.Ground, onBackground = RodadaVisual.Paper,
            surface = RodadaVisual.Surface, onSurface = RodadaVisual.Paper,
            surfaceVariant = RodadaVisual.Control, onSurfaceVariant = RodadaVisual.Muted,
            surfaceContainer = RodadaVisual.Control,
            surfaceContainerLow = RodadaVisual.Surface,
            surfaceContainerLowest = RodadaVisual.Ground,
            surfaceContainerHigh = RodadaVisual.Control,
            surfaceContainerHighest = RodadaVisual.Control,
            surfaceTint = Color.Transparent,
            outline = RodadaVisual.Border, error = RodadaVisual.Danger,
        ),
        typography = base.copy(
            headlineLarge = title.copy(fontSize = 46.sp, lineHeight = 46.sp),
            headlineMedium = title, headlineSmall = title.copy(fontSize = 28.sp),
            titleLarge = title.copy(fontSize = 24.sp, lineHeight = 28.sp),
            titleMedium = body.copy(fontSize = 20.sp, fontWeight = FontWeight.Bold),
            titleSmall = body.copy(fontWeight = FontWeight.Bold),
            bodyLarge = body, bodyMedium = body.copy(fontSize = 15.sp),
            bodySmall = body.copy(fontSize = 14.sp, lineHeight = 20.sp),
            labelLarge = label, labelMedium = label.copy(fontSize = 14.sp),
            labelSmall = label.copy(fontSize = 12.sp),
        ),
        shapes = Shapes(extraSmall = RoundedCornerShape(4.dp), small = RoundedCornerShape(4.dp), medium = RoundedCornerShape(8.dp), large = RoundedCornerShape(12.dp), extraLarge = RoundedCornerShape(12.dp)),
        content = content,
    )
}

@Composable
fun RodadaButton(onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, content: @Composable RowScope.() -> Unit) {
    Button(onClick = onClick, modifier = modifier.heightIn(min = 56.dp), enabled = enabled, shape = RoundedCornerShape(8.dp), content = content)
}

@Composable
fun RodadaOutlinedButton(onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, content: @Composable RowScope.() -> Unit) {
    OutlinedButton(onClick = onClick, modifier = modifier.heightIn(min = 48.dp), enabled = enabled, shape = RoundedCornerShape(8.dp), colors = ButtonDefaults.outlinedButtonColors(contentColor = RodadaVisual.Paper), content = content)
}
