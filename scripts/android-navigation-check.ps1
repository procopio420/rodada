# Spec 023 V05 partial. Use a booted API 36 emulator at the requested width / 160 dpi.
param(
    [ValidateSet(360,390,430)][int]$Width = 390,
    [ValidateSet('1.0','2.0')][string]$FontScale = '1.0'
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
if (-not $env:JAVA_HOME -or -not $env:ANDROID_HOME) { throw 'Set JAVA_HOME and ANDROID_HOME first.' }
$taskAdb = Join-Path $env:ANDROID_HOME 'platform-tools/adb.exe'
$taskSerial = $env:ANDROID_SERIAL
if (-not $taskSerial) { throw 'Set ANDROID_SERIAL to the isolated emulator.' }
if ((& $taskAdb -s $taskSerial shell getprop sys.boot_completed).Trim() -ne '1') { throw 'Emulator must finish booting before running tests.' }
if ((& $taskAdb -s $taskSerial shell getprop ro.build.version.sdk).Trim() -ne '36') { throw 'This comparison contract fixes API 36.' }
$taskDisplay = @(& $taskAdb -s $taskSerial shell wm size)[-1].Trim()
if ($taskDisplay -notmatch "(?:Physical|Override) size: ${Width}x844") { throw 'Display does not match the requested comparison width.' }
$taskDensity = @(& $taskAdb -s $taskSerial shell wm density)[-1].Trim()
if ($taskDensity -notmatch '(?:Physical|Override) density: 160$') { throw 'Use density 160: one physical pixel per dp.' }
if ((& $taskAdb -s $taskSerial shell settings get system font_scale).Trim() -ne $FontScale) { throw 'Font scale does not match the requested comparison.' }
Push-Location (Join-Path $taskRoot 'apps/attendance-android')
try {
    # Discard only previous generated instrumentation XML, so an empty run cannot reuse old success.
    $taskOutputRoot = [IO.Path]::GetFullPath((Join-Path (Get-Location) 'app/build/outputs/androidTest-results/connected/debug'))
    if (Test-Path -LiteralPath $taskOutputRoot) {
        Get-ChildItem -LiteralPath $taskOutputRoot -Filter 'TEST-*.xml' | ForEach-Object { Remove-Item -LiteralPath $_.FullName }
    }
    & ./gradlew.bat testDebugUnitTest assembleDebug lintDebug connectedDebugAndroidTest --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Android checks failed.' }
    $taskResults = Get-ChildItem 'app/build/outputs/androidTest-results/connected/debug' -Filter 'TEST-*.xml'
    $taskCount = 0
    foreach ($taskResult in $taskResults) {
        [xml]$taskXml = Get-Content -LiteralPath $taskResult.FullName -Raw
        foreach ($taskSuite in $taskXml.testsuites.testsuite) {
            if ($taskSuite.name -eq 'com.rodada.attendance.ui.AttendanceNavigationTest') {
                $taskCount += [int]$taskSuite.tests
                if ([int]$taskSuite.failures -gt 0 -or [int]$taskSuite.errors -gt 0 -or [int]$taskSuite.skipped -gt 0) { throw 'Navigation tests did not all pass.' }
            }
        }
    }
    if ($taskCount -ne 2) { throw 'Expected exactly two executed navigation tests; build success alone is insufficient.' }
} finally { Pop-Location }
