package com.rodada.attendance.ui

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.rodada.attendance.R

// Spec 021 / docs/design/system.md: shared semantics, no dynamic device palette.
private val Paper = Color(0xFFF3ECE1)
private val Ink = Color(0xFF17130F)
private val Ground = Color(0xFF120F0C)
private val Surface = Color(0xFF1B1713)
private val Raised = Color(0xFF252019)
private val Muted = Color(0xFFBBAE9B)
private val Amber = Color(0xFFF5A524)
private val Blue = Color(0xFF82B8FF)
private val Danger = Color(0xFFFF5D47)

private val RodadaColors = darkColorScheme(
    primary = Paper, onPrimary = Ink,
    primaryContainer = Raised, onPrimaryContainer = Paper,
    secondary = Blue, onSecondary = Ink,
    secondaryContainer = Color(0xFF15253B), onSecondaryContainer = Blue,
    tertiary = Amber, onTertiary = Ink,
    tertiaryContainer = Color(0xFF3A2A10), onTertiaryContainer = Amber,
    background = Ground, onBackground = Paper,
    surface = Surface, onSurface = Paper,
    surfaceVariant = Raised, onSurfaceVariant = Muted,
    surfaceContainerLowest = Ground, surfaceContainerLow = Surface,
    surfaceContainer = Raised, surfaceContainerHigh = Color(0xFF312A21),
    surfaceContainerHighest = Color(0xFF312A21), surfaceDim = Ground,
    surfaceBright = Raised, surfaceTint = Amber,
    inverseSurface = Paper, inverseOnSurface = Ink, inversePrimary = Ink,
    outline = Color(0xFF4D4335), outlineVariant = Color(0xFF3A3228),
    error = Danger, onError = Ink,
    errorContainer = Color(0xFF3D1712), onErrorContainer = Danger,
)

private val Archivo = FontFamily(
    Font(R.font.archivo, FontWeight.Normal),
    Font(R.font.archivo, FontWeight.Medium),
    Font(R.font.archivo, FontWeight.SemiBold),
    Font(R.font.archivo, FontWeight.Bold),
    Font(R.font.archivo, FontWeight.ExtraBold),
    Font(R.font.archivo, FontWeight.Black),
)
val RodadaMono = FontFamily(Font(R.font.jetbrains_mono, FontWeight.Medium))

private val BaseType = Typography()
private val RodadaType = Typography(
    displayLarge = BaseType.displayLarge.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    displayMedium = BaseType.displayMedium.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    displaySmall = BaseType.displaySmall.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    headlineLarge = BaseType.headlineLarge.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    headlineMedium = BaseType.headlineMedium.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    headlineSmall = BaseType.headlineSmall.copy(fontFamily = Archivo, fontWeight = FontWeight.Black),
    titleLarge = BaseType.titleLarge.copy(fontFamily = Archivo),
    titleMedium = BaseType.titleMedium.copy(fontFamily = Archivo),
    titleSmall = BaseType.titleSmall.copy(fontFamily = Archivo),
    bodyLarge = BaseType.bodyLarge.copy(fontFamily = Archivo),
    bodyMedium = BaseType.bodyMedium.copy(fontFamily = Archivo),
    bodySmall = BaseType.bodySmall.copy(fontFamily = Archivo, fontSize = 14.sp),
    labelLarge = BaseType.labelLarge.copy(fontFamily = Archivo),
    labelMedium = BaseType.labelMedium.copy(fontFamily = Archivo, fontSize = 14.sp),
    labelSmall = BaseType.labelSmall.copy(fontFamily = Archivo, fontSize = 14.sp),
)

@Composable
fun RodadaTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = RodadaColors,
        typography = RodadaType,
        shapes = Shapes(
            extraSmall = RoundedCornerShape(4.dp), small = RoundedCornerShape(4.dp),
            medium = RoundedCornerShape(8.dp), large = RoundedCornerShape(8.dp),
            extraLarge = RoundedCornerShape(8.dp),
        ),
        content = content,
    )
}
