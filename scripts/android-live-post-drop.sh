#!/usr/bin/env bash
# End-to-end fault: REAL Android HTTP -> TCP reset after Django/PostgreSQL
# commit -> force stop -> offline restart -> original-key replay -> SQL check.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT/apps/attendance-android"
APP_ID="com.rodada.attendance"
TEST="com.rodada.attendance.operations.LivePostDropReconciliationTest#stage"
INSTRUMENTATION="$APP_ID.test/androidx.test.runner.AndroidJUnitRunner"
FIXTURE="${RODADA_POST_DROP_FIXTURE:-/tmp/rodada-android-live-fixture.json}"
MARKER="${RODADA_POST_DROP_MARKER:-/tmp/rodada-android-live-drop.json}"
ADB=(adb)
if [[ -n "${ANDROID_SERIAL:-}" ]]; then ADB+=( -s "$ANDROID_SERIAL" ); fi
command -v adb >/dev/null || { echo "adb is required" >&2; exit 2; }
"${ADB[@]}" get-state | grep -q device || { echo "Android device not connected" >&2; exit 2; }
test -f "$FIXTURE" || { echo "Missing disposable PostgreSQL fixture" >&2; exit 2; }

export DJANGO_SETTINGS_MODULE=rodada_api.settings
export PYTHONPATH="$ROOT/apps/api"
if [[ "${RODADA_SKIP_ANDROID_BUILD:-0}" != 1 ]]; then
  (cd "$ANDROID_DIR" && ./gradlew :app:assembleDebug :app:assembleDebugAndroidTest)
fi
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"

product_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["product_id"])' "$FIXTURE")

run_stage() {
  local stage="$1"
  local output
  output=$("${ADB[@]}" shell am instrument -w -e phase "$stage" \
      -e productId "$product_id" -e class "$TEST" "$INSTRUMENTATION")
  printf '%s\n' "$output"
  if ! grep -q 'OK (1 test)' <<<"$output"; then
    echo "FAIL: real Android backend stage $stage" >&2
    exit 1
  fi
}
force_stop_running() {
  # Instrumentation itself may have exited; launch the actual app process first.
  "${ADB[@]}" shell am start -W -n "$APP_ID/.MainActivity" >/dev/null
  local before
  before=$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)
  test -n "$before" || { echo "FAIL: no live app PID before force-stop" >&2; exit 1; }
  "${ADB[@]}" shell am force-stop "$APP_ID"
  if [[ -n "$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)" ]]; then
    echo "FAIL: process still running after force-stop" >&2
    exit 1
  fi
  echo "PASS: actual Android process $before force-stopped"
}

# The proxy does NOT synthesize the successful POST. It awaits Django HTTP 201,
# then RSTs the Android socket; zero response bytes reach HttpURLConnection.
run_stage capture
python3 "$ROOT/scripts/verify-android-live-post-drop.py" before --fixture "$FIXTURE" --marker "$MARKER"
python3 - <<'PY'
from urllib.request import Request, urlopen
request = Request("http://127.0.0.1:8000/__fault/disarm", data=b"", method="POST")
with urlopen(request, timeout=10) as response:
    assert response.status == 200
print("PASS: fault disarmed only after proven Django commit")
PY

force_stop_running
"${ADB[@]}" shell svc wifi disable
"${ADB[@]}" shell svc data disable
trap '"${ADB[@]}" shell svc wifi enable >/dev/null 2>&1 || true; "${ADB[@]}" shell svc data enable >/dev/null 2>&1 || true' EXIT
run_stage offline
force_stop_running
"${ADB[@]}" shell svc wifi enable
"${ADB[@]}" shell svc data enable
sleep 4

run_stage replay
python3 "$ROOT/scripts/verify-android-live-post-drop.py" after --fixture "$FIXTURE" --marker "$MARKER" \
    --receipt "$ROOT/artifacts/android-real-post-drop.json"
"${ADB[@]}" shell am force-stop "$APP_ID"
echo "PASS: real POST was committed and TCP response lost; Android recovered the same idempotency key after process death, exactly one order and one charge."
