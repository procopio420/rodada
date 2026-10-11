#!/usr/bin/env bash
# Real process-death recovery proof on a disposable emulator/device.
# DOES NOT submit to a provider or call a production API.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT/apps/attendance-android"
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
  if ! grep -q 'OK (1 test)' <<<"$output"; then
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
