#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${RODADA_TEST_PYTHON:-python3}"
# Fail before clearing the emulator app or making any network request.
"$PYTHON" -c 'import sys; sys.path.insert(0,"scripts"); from cross_surface_fixture import require_disposable_database; require_disposable_database()'
ADB=(adb)
if [[ -n "${ANDROID_SERIAL:-}" ]]; then ADB+=(-s "$ANDROID_SERIAL"); fi
[[ "$("${ADB[@]}" shell getprop ro.kernel.qemu | tr -d '\r')" == 1 ]] || { echo 'Disposable emulator required'; exit 2; }
(cd apps/attendance-android && ./gradlew :app:assembleDebug :app:assembleDebugAndroidTest -ProdadaApiBaseUrl=http://10.0.2.2:8101/)
"${ADB[@]}" install -r apps/attendance-android/app/build/outputs/apk/debug/app-debug.apk
"${ADB[@]}" install -r apps/attendance-android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
export RODADA_COMPOSE_TAB_LABEL="Android-Compose-acceptance-$("$PYTHON" -c 'import uuid; print(uuid.uuid4().hex[:12])')"
export PYTHONPATH="$ROOT/apps/api"
mkdir -p artifacts
"${ADB[@]}" shell getprop ro.build.version.sdk | tr -d '\r' > artifacts/android-emulator-api.txt
if [[ "${RODADA_COMPOSE_READBACK:-false}" == true ]]; then
  read -r table_id table_label tab_one tab_two < <("$PYTHON" - <<'PYARGS'
import json,re,os,sys
sys.path.insert(0,"scripts")
from pathlib import Path
from cross_surface_fixture import require_disposable_database
require_disposable_database()
import django;django.setup()
from django.db import connection
from cross_surface_fixture import require_connected_database,database_instance_identity
from modules.hospitality.models import Table
from modules.ordering.models import Tab
require_connected_database(connection)
r=json.loads(Path("artifacts/browser-origins-sql.json").read_text())
assert r["database_instance_id"]==database_instance_identity(connection)
values=[r["table_id"],Table.objects.get(pk=r["table_id"],venue_id=r["venue_id"]).label]+[Tab.objects.get(pk=pk,venue_id=r["venue_id"]).display_label for pk in r["tab_ids"]]
assert len(values)==4 and all(re.fullmatch(r"[A-Za-z0-9_-]+",v) for v in values)
print(*values)
PYARGS
)
  "${ADB[@]}" shell am force-stop com.rodada.attendance
  "${ADB[@]}" shell pm clear com.rodada.attendance
  "${ADB[@]}" shell am instrument -w -e liveReadback true -e tableId "$table_id" -e tableLabel "$table_label" -e tabOne "$tab_one" -e tabTwo "$tab_two" \
    -e class com.rodada.attendance.operations.LiveComposeReadbackTest \
    com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner | tee artifacts/android-context-readback-instrumentation.txt
  grep -q 'OK (1 test)' artifacts/android-context-readback-instrumentation.txt
  "$PYTHON" scripts/verify-browser-origins.py
  cp artifacts/browser-origins-sql.json artifacts/android-context-readback-sql.json
  "${ADB[@]}" exec-out screencap -p > artifacts/android-context-readback.png
  "${ADB[@]}" shell am force-stop com.rodada.attendance
  exit 0
fi
mode="${RODADA_COMPOSE_CATALOG_FAULT:-false}"
if [[ "$mode" == true ]]; then
  export RODADA_CATALOG_PROOF_PREFIX=android-catalog
  if [[ "${RODADA_COMPOSE_OFFLINE_CATALOG:-false}" == true ]]; then export RODADA_CATALOG_PROOF_PREFIX=android-offline-conflict; fi
  if [[ "${RODADA_COMPOSE_OFFLINE_REVOCATION:-false}" == true ]]; then export RODADA_CATALOG_PROOF_PREFIX=android-offline-revocation; fi
  fault_applied=false
  restore_catalog_fault() {
    local result=$?
    trap - EXIT
    "${ADB[@]}" shell svc wifi enable || result=1
    "${ADB[@]}" shell svc data enable || result=1
    if [[ "$fault_applied" == true ]]; then "$PYTHON" scripts/issue106-catalog-fault.py restore || result=1; fi
    kill "$instrument_pid" 2>/dev/null || true
    exit "$result"
  }
  "${ADB[@]}" shell am force-stop com.rodada.attendance
"${ADB[@]}" shell pm clear com.rodada.attendance
"${ADB[@]}" shell am instrument -w -e liveCompose true -e catalogFault true -e offlineFault "${RODADA_COMPOSE_OFFLINE_CATALOG:-false}" -e revocationFault "${RODADA_COMPOSE_OFFLINE_REVOCATION:-false}" \
  -e tabLabel "$RODADA_COMPOSE_TAB_LABEL" -e foreignTabId "$("$PYTHON" -c 'import json,os; print(json.load(open(os.environ["RODADA_POST_DROP_FIXTURE"]))["foreign_tab_id"])')" \
  -e class com.rodada.attendance.operations.LiveComposeOrderTest \
  com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner > "artifacts/$RODADA_CATALOG_PROOF_PREFIX-instrumentation.txt" &
instrument_pid=$!
trap restore_catalog_fault EXIT
wait_app_marker() {
  for i in $(seq 1 90); do
    kill -0 "$instrument_pid" 2>/dev/null || { echo "Instrumentation exited before $1; inspect its log"; exit 1; }
    if "${ADB[@]}" shell run-as com.rodada.attendance test -f "files/$1"; then return; fi
    if [[ "$i" == 90 ]]; then echo "Timed out waiting for $1"; return 1; fi
    sleep 1
  done
}
wait_app_marker catalog-cart-ready
if [[ "${RODADA_COMPOSE_OFFLINE_CATALOG:-false}" == true ]]; then
  "${ADB[@]}" shell svc wifi disable
  "${ADB[@]}" shell svc data disable
  "${ADB[@]}" shell run-as com.rodada.attendance touch files/catalog-fault-applied
  wait_app_marker offline-intent-ready
  if [[ "${RODADA_COMPOSE_OFFLINE_REVOCATION:-false}" == true ]]; then
    export RODADA_REVOKED_SESSION_ID="$("${ADB[@]}" shell run-as com.rodada.attendance cat files/offline-session-id | tr -d '\r')"
    "$PYTHON" scripts/issue106-catalog-fault.py revoke
  else
    "$PYTHON" scripts/issue106-catalog-fault.py unavailable
    fault_applied=true
  fi
  "${ADB[@]}" shell svc wifi enable
  "${ADB[@]}" shell svc data enable
  if [[ "${RODADA_COMPOSE_OFFLINE_REVOCATION:-false}" == true ]]; then
    "${ADB[@]}" shell run-as com.rodada.attendance touch files/revocation-applied
    wait_app_marker expiry-session-id
    export RODADA_EXPIRED_SESSION_ID="$("${ADB[@]}" shell run-as com.rodada.attendance cat files/expiry-session-id | tr -d '\r')"
    "$PYTHON" scripts/issue106-catalog-fault.py expire
    "${ADB[@]}" shell run-as com.rodada.attendance touch files/expiry-applied
  fi
else
  "$PYTHON" scripts/issue106-catalog-fault.py unavailable
  fault_applied=true
  "${ADB[@]}" shell run-as com.rodada.attendance touch files/catalog-fault-applied
fi
wait "$instrument_pid"
  grep -q 'OK (1 test)' "artifacts/$RODADA_CATALOG_PROOF_PREFIX-instrumentation.txt"
  "$PYTHON" scripts/issue106-catalog-fault.py verify
  "${ADB[@]}" exec-out screencap -p > "artifacts/$RODADA_CATALOG_PROOF_PREFIX-rejected.png"
  "${ADB[@]}" shell am force-stop com.rodada.attendance
  exit 0
fi
"${ADB[@]}" shell am force-stop com.rodada.attendance
"${ADB[@]}" shell pm clear com.rodada.attendance
"${ADB[@]}" shell am instrument -w -e liveCompose true \
  -e tabLabel "$RODADA_COMPOSE_TAB_LABEL" -e class com.rodada.attendance.operations.LiveComposeOrderTest \
  com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner | tee artifacts/android-compose-instrumentation.txt
grep -q 'OK (1 test)' artifacts/android-compose-instrumentation.txt
export PYTHONPATH="$ROOT/apps/api"
"$PYTHON" scripts/verify-android-compose-order.py
"${ADB[@]}" exec-out screencap -p > artifacts/android-compose-confirmed.png
"${ADB[@]}" shell am force-stop com.rodada.attendance
