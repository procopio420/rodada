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
mode="${RODADA_COMPOSE_CATALOG_FAULT:-false}"
if [[ "$mode" == true ]]; then
  "${ADB[@]}" shell am force-stop com.rodada.attendance
"${ADB[@]}" shell pm clear com.rodada.attendance
"${ADB[@]}" shell am instrument -w -e liveCompose true -e catalogFault true \
  -e tabLabel "$RODADA_COMPOSE_TAB_LABEL" -e class com.rodada.attendance.operations.LiveComposeOrderTest \
  com.rodada.attendance.test/androidx.test.runner.AndroidJUnitRunner > artifacts/android-catalog-instrumentation.txt &
instrument_pid=$!
trap '"$PYTHON" scripts/issue106-catalog-fault.py restore; kill "$instrument_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 90); do
  kill -0 "$instrument_pid" 2>/dev/null || { echo "Instrumentation exited before cart readiness; inspect its log"; exit 1; }
  if "${ADB[@]}" shell run-as com.rodada.attendance test -f files/catalog-cart-ready; then break; fi
  if [[ "$i" == 90 ]]; then echo "Compose cart did not become ready"; exit 1; fi
  sleep 1
done
"$PYTHON" scripts/issue106-catalog-fault.py unavailable
"${ADB[@]}" shell run-as com.rodada.attendance touch files/catalog-fault-applied
wait "$instrument_pid"
  grep -q 'OK (1 test)' artifacts/android-catalog-instrumentation.txt
  "$PYTHON" scripts/issue106-catalog-fault.py verify
  "${ADB[@]}" exec-out screencap -p > artifacts/android-catalog-rejected.png
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
