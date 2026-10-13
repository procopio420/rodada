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
try {
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
    @{ platform = 'Android API36 emulator'; cases = $results; tests = 198; skipped = 0 } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'matrix.json') -Encoding utf8
} finally {
    & $Adb -s $Serial shell wm size 390x844
    & $Adb -s $Serial shell settings put system font_scale 1
}
