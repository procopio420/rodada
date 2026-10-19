package com.rodada.attendance.ui

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.rodada.attendance.R

/** PR212 Archivo uses the normal width axis, unlike the legacy condensed display headings. */
object AttendanceUx2 {
    val Font = FontFamily((listOf(400, 500, 700, 750, 800, 820, 850, 900).map { weight ->
        Font(R.font.archivo, weight = FontWeight(weight), variationSettings = FontVariation.Settings(
            FontVariation.weight(weight), FontVariation.width(100f)))
    }))
    fun text(size: Int, weight: Int = 500, lineHeight: Float = size * 1.45f) = TextStyle(
        fontFamily = Font, fontWeight = FontWeight(weight), fontSize = size.sp,
        lineHeight = lineHeight.sp, letterSpacing = 0.sp,
    )
}
