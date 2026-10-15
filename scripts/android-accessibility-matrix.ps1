param(
    [Parameter(Mandatory = $true)][string]$Adb,
    [Parameter(Mandatory = $true)][string]$Serial,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
if (-not $Serial.StartsWith('emulator-')) { throw 'Use an isolated disposable emulator.' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$classes = @(
    'ui.AttendanceNavigationTest', 'ui.AttendanceHeaderTest', 'ui.PartySizeEditorTest',
    'cash.CashRecoveryScreenTest', 'operations.CriticalFieldsTest',
    'operations.LoginAccessibilityTest', 'operations.MonetaryFieldsTest',
    'operations.NowQueuesTest', 'operations.OrderDestinationTest',
    'operations.OrderWorkspaceTest', 'operations.RefundFieldsTest',
    'operations.RepeatOrderDialogTest', 'operations.TableReleaseTest'
) | ForEach-Object { 'com.rodada.attendance.' + $_ }
$results = @()
$animationSettings = @('window_animation_scale', 'transition_animation_scale', 'animator_duration_scale')
$originalAnimations = @{}
try {
    foreach ($setting in $animationSettings) {
        $originalAnimations[$setting] = (& $Adb -s $Serial shell settings get global $setting).Trim()
        & $Adb -s $Serial shell settings put global $setting 0
    }
    & $Adb -s $Serial shell am force-stop com.rodada.attendance
    & $Adb -s $Serial shell wm density 160
    foreach ($width in @(360, 390, 430)) {
        foreach ($font in @(1, 2)) {
            & $Adb -s $Serial shell wm size "${width}x844"
            & $Adb -s $Serial shell settings put system font_scale $font
            $log = Join-Path $OutputDirectory "width-$width-font-$font.txt"
            $output = & $Adb -s $Serial shell am instrument -w -e class ($classes -join ',') com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner 2>&1
            $output | Set-Content -LiteralPath $log -Encoding utf8
            $text = $output -join "`n"
            if ($LASTEXITCODE -ne 0 -or $text -notmatch 'OK \(33 tests\)' -or $text -match 'FAILURES|INSTRUMENTATION_FAILED|INSTRUMENTATION_STATUS_CODE: -[34]') {
                throw "Accessibility matrix failed: width=$width font=$font; see $log"
            }
            $results += @{ widthDp = $width; fontScale = $font; tests = 33; passed = $true }
            Write-Output "PASS: width=$width font=$font, 33 tests"
        }
    }
    @{ platform = 'Android API36 emulator'; nativeAnimationScale = 0; cases = $results; tests = 198; skipped = 0 } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'matrix.json') -Encoding utf8
} finally {
    foreach ($setting in $originalAnimations.Keys) {
        if ($originalAnimations[$setting] -eq 'null') {
            & $Adb -s $Serial shell settings delete global $setting | Out-Null
        } else {
            & $Adb -s $Serial shell settings put global $setting $originalAnimations[$setting]
        }
    }
    & $Adb -s $Serial shell wm size 390x844
    & $Adb -s $Serial shell settings put system font_scale 1
}
