#!/usr/bin/env bash
# Real process-death recovery proof on a disposable emulator/device.
# DOES NOT submit to a provider or call a production API.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT/apps/attendance-android"
source "$ROOT/scripts/lib/android-instrumentation-result.sh"
APP_ID="com.rodada.attendance"
INSTRUMENTATION="$APP_ID.test/androidx.test.runner.AndroidJUnitRunner"
TEST="com.rodada.attendance.operations.ForceStopOrderRecoveryTest#stagedRecovery"
ADB=(adb)
if [[ -n "${ANDROID_SERIAL:-}" ]]; then ADB+=( -s "$ANDROID_SERIAL" ); fi

command -v adb >/dev/null || { echo "adb is required" >&2; exit 2; }
"${ADB[@]}" get-state | grep -q device || { echo "Connect an emulator/device via adb." >&2; exit 2; }
if [[ "${RODADA_SKIP_ANDROID_BUILD:-0}" != 1 ]]; then
  (cd "$ANDROID_DIR" && ./gradlew :app:assembleDebug :app:assembleDebugAndroidTest)
fi
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"

run_stage() {
  local stage="$1"
  local output
  output=$("${ADB[@]}" shell am instrument -w -e phase "$stage" -e class "$TEST" "$INSTRUMENTATION")
  printf '%s\n' "$output"
  if ! android_instrumentation_succeeded "$output" 1; then
    echo "FAILED: Android process-stage $stage" >&2
    exit 1
  fi
}

# Each force-stop must target an ACTUALLY RUNNING application, not merely
# an instrumentation process which may exit after finishing the test method.
force_stop_running_app() {
  "${ADB[@]}" shell am start -W -n "$APP_ID/.MainActivity" >/dev/null
  local pid
  pid=$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)
  if [[ -z "$pid" ]]; then
    echo "Android app process was not running; force-stop proof invalid" >&2
    exit 1
  fi
  "${ADB[@]}" shell am force-stop "$APP_ID"
  if [[ -n "$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)" ]]; then
    echo "App did not exit after force-stop" >&2
    exit 1
  fi
}
# Keystore/preferences survive force-stop; never use pm clear or reinstall.
run_stage prepare
force_stop_running_app
"${ADB[@]}" shell svc wifi disable
"${ADB[@]}" shell svc data disable
trap '"${ADB[@]}" shell svc wifi enable >/dev/null 2>&1 || true; "${ADB[@]}" shell svc data enable >/dev/null 2>&1 || true' EXIT
run_stage offline
force_stop_running_app
"${ADB[@]}" shell svc wifi enable
run_stage ambiguous
"${ADB[@]}" shell am force-stop "$APP_ID"
echo "PASS: encrypted original-session pending order survived forced termination, offline start, and ambiguous retry."
echo "NOTE: This validates persistence, not a live backend POST. Full-shift API idempotency has separate PostgreSQL tests."

# Spec 027 UI contracts on the same disposable emulator; no merchant/network mutation.
ui_output=$("${ADB[@]}" shell am instrument -w -e class com.rodada.attendance.operations.TableServiceNavigationTest "$INSTRUMENTATION")
printf '%s\n' "$ui_output"
if ! android_instrumentation_succeeded "$ui_output" 4; then
  echo "FAILED: Spec 027 table-service navigation" >&2
  exit 1
fi
echo "PASS: Spec 027 one-tap start, contextual optional-name open, homonyms and pending-intent gates."

nav_output=$("${ADB[@]}" shell am instrument -w -e class com.rodada.attendance.ui.AttendanceNavigationTest "$INSTRUMENTATION")
printf '%s\n' "$nav_output"
android_instrumentation_succeeded "$nav_output" 3 || { echo "FAILED: navigation geometry and Nova comanda label" >&2; exit 1; }
# Production text at mobile widths and enlarged system font; no baseline relaxation.
trap '"${ADB[@]}" shell settings put system font_scale 1 >/dev/null 2>&1 || true; "${ADB[@]}" shell wm size reset >/dev/null 2>&1 || true; "${ADB[@]}" shell wm density reset >/dev/null 2>&1 || true; "${ADB[@]}" shell svc wifi enable >/dev/null 2>&1 || true; "${ADB[@]}" shell svc data enable >/dev/null 2>&1 || true' EXIT
for width in 360 390 430; do
  "${ADB[@]}" shell wm density 160
  "${ADB[@]}" shell wm size "${width}x844"
  "${ADB[@]}" shell settings put system font_scale 1.5
  fit_output=$("${ADB[@]}" shell am instrument -w -e class 'com.rodada.attendance.operations.OrderDestinationTest#productionNewTabLabelFitsAndOpensOnce' "$INSTRUMENTATION")
  printf '%s\n' "$fit_output"
  android_instrumentation_succeeded "$fit_output" 1 || { echo "FAILED Nova comanda at $width px / font 1.5" >&2; exit 1; }
done
