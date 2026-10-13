#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID=com.rodada.attendance
TEST=com.rodada.attendance.operations.LiveTableServiceDropReconciliationTest#stage
ADB=(adb)
if [[ -n "${ANDROID_SERIAL:-}" ]]; then ADB+=(-s "$ANDROID_SERIAL"); fi
export DJANGO_SETTINGS_MODULE=rodada_api.settings PYTHONPATH="$ROOT/apps/api"
table_id=$(python3 -c 'import json,os; print(json.load(open(os.environ["RODADA_POST_DROP_FIXTURE"]))["table_id"])')
run_stage() {
  local output
  output=$("${ADB[@]}" shell am instrument -w -e phase "$1" -e tableAction "$mode" -e tableId "$table_id" -e class "$TEST" "$APP_ID.test/androidx.test.runner.AndroidJUnitRunner")
  printf '%s\n' "$output"
  grep -q 'OK (1 test)' <<<"$output" || { echo "FAIL table $mode $1" >&2; exit 1; }
}
force_stop() {
  "${ADB[@]}" shell am start -W -n "$APP_ID/.MainActivity" >/dev/null
  local pid
  pid=$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r')
  test -n "$pid"
  "${ADB[@]}" shell am force-stop "$APP_ID"
  test -z "$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)"
  echo "PASS force-stopped live process $pid"
}
trap '"${ADB[@]}" shell svc wifi enable >/dev/null 2>&1 || true; "${ADB[@]}" shell svc data enable >/dev/null 2>&1 || true' EXIT
for mode in start open; do
  curl -fsS -X POST "http://127.0.0.1:8000/__fault/arm-table-$mode"
  run_stage capture
  python3 "$ROOT/scripts/verify-android-table-service-drop.py" "$mode" before
  force_stop
  "${ADB[@]}" shell svc wifi disable
  "${ADB[@]}" shell svc data disable
  run_stage offline
  force_stop
  curl -fsS -X POST http://127.0.0.1:8000/__fault/disarm
  "${ADB[@]}" shell svc wifi enable
  "${ADB[@]}" shell svc data enable
  sleep 4
  run_stage replay
  python3 "$ROOT/scripts/verify-android-table-service-drop.py" "$mode" after
  "${ADB[@]}" shell am force-stop "$APP_ID"
done
