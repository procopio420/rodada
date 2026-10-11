#!/usr/bin/env bash
# A truly severed Android uplink WHILE a real order POST is awaiting its
# post-commit response. CI uses the emulator's actual eth0 link (not svc wifi).
# A disposable physical phone can instead cut its wlan0 radio.
# Backend: exclusively disposable Django/PostgreSQL; no live merchant or PSP.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="com.rodada.attendance"
ANDROID_DIR="$ROOT/apps/attendance-android"
TEST="com.rodada.attendance.operations.LivePostDropReconciliationTest#stage"
INSTRUMENTATION="$APP_ID.test/androidx.test.runner.AndroidJUnitRunner"
MODE="${RODADA_NETWORK_CUT_MODE:-emulator-link}"
FIXTURE="${RODADA_POST_DROP_FIXTURE:-/tmp/rodada-android-live-fixture.json}"
MARKER="${RODADA_POST_DROP_MARKER:-/tmp/rodada-android-live-drop.json}"
ADB=(adb)
if [[ -n "${ANDROID_SERIAL:-}" ]]; then ADB+=(-s "$ANDROID_SERIAL"); fi

command -v adb >/dev/null || { echo "FAIL: adb required" >&2; exit 2; }
"${ADB[@]}" get-state | grep -q device || { echo "FAIL: no Android connected" >&2; exit 2; }
test -f "$FIXTURE" || { echo "FAIL: isolated fixture absent" >&2; exit 2; }
case "${POSTGRES_DB:-}" in rodada_android_post_drop*) ;; *) echo "FAIL: dedicated disposable PostgreSQL required" >&2; exit 2;; esac
case "${POSTGRES_HOST:-}" in 127.0.0.1|localhost) ;; *) echo "FAIL: no remote/shared database" >&2; exit 2;; esac

product_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["product_id"])' "$FIXTURE")
case "$MODE" in
  emulator-link)
    HOST_IP="10.0.2.2"
    API_URL="http://10.0.2.2:8000/"
    # Google APIs images are debuggable; fail closed if root is unavailable.
    "${ADB[@]}" root | tee /tmp/rodada-android-adb-root.log
    sleep 2
    "${ADB[@]}" shell id -u | tr -d '\r' | grep -qx 0 || {
      echo "FAIL: emulator root unavailable; cannot sever actual uplink" >&2; exit 2;
    }
    IFACE="eth0"
    ;;
  physical-wifi)
    test -n "${ANDROID_SERIAL:-}" || { echo "FAIL: explicit Android serial required" >&2; exit 2; }
    test "${RODADA_DISPOSABLE_PHONE_ACK:-}" = "I_CONFIRM_DISPOSABLE_TEST_PHONE" || {
      echo "FAIL: this installs a debug app and changes Wi-Fi/data; use a disposable phone and explicit consent" >&2; exit 2;
    }
    HOST_IP="${RODADA_TEST_LAN_IP:?Set numeric LAN IPv4 address of test laptop}"
    [[ "$HOST_IP" =~ ^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)[0-9.]+$ ]] || {
      echo "FAIL: LAN address required (no public server)" >&2; exit 2;
    }
    API_URL="http://$HOST_IP:8000/"
    IFACE="wlan0"
    # Cellular fallback would undermine proof of Wi-Fi isolation.
    "${ADB[@]}" shell svc data disable
    ;;
  *) echo "FAIL: RODADA_NETWORK_CUT_MODE must be emulator-link or physical-wifi" >&2; exit 2;;
esac

# Verify the actual routed Android interface before the original POST.
route_before=$("${ADB[@]}" shell ip route get "$HOST_IP" 2>&1 | tr -d '\r')
echo "ROUTE_BEFORE: $route_before"
grep -q "dev $IFACE" <<< "$route_before" || {
  echo "FAIL: Android HTTP traffic is not routed on target interface $IFACE" >&2; exit 2;
}

network_is_down=0
cleanup() {
  if [[ "$network_is_down" == 1 ]]; then
    if [[ "$MODE" == emulator-link ]]; then
      "${ADB[@]}" shell ip link set "$IFACE" up >/dev/null 2>&1 || true
    else
      "${ADB[@]}" shell svc wifi enable >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT

if [[ "${RODADA_SKIP_ANDROID_BUILD:-0}" != 1 ]]; then
  (cd "$ANDROID_DIR" && ./gradlew :app:assembleDebug :app:assembleDebugAndroidTest)
fi
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"
"${ADB[@]}" install -r "$ANDROID_DIR/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"

run_stage() {
  local stage="$1" output
  output=$("${ADB[@]}" shell am instrument -w -e phase "$stage" \
    -e productId "$product_id" -e baseUrl "$API_URL" -e class "$TEST" "$INSTRUMENTATION")
  printf '%s\n' "$output"
  grep -q 'OK (1 test)' <<< "$output" || { echo "FAIL: instrumentation stage $stage" >&2; exit 1; }
}
force_stop_running() {
  "${ADB[@]}" shell am start -W -n "$APP_ID/.MainActivity" >/dev/null
  local pid
  pid=$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)
  test -n "$pid" || { echo "FAIL: no real Android app PID" >&2; exit 1; }
  "${ADB[@]}" shell am force-stop "$APP_ID"
  test -z "$("${ADB[@]}" shell pidof "$APP_ID" | tr -d '\r' || true)" || {
    echo "FAIL: force-stop did not kill app" >&2; exit 1;
  }
  echo "PASS: force-stop killed Android PID $pid"
}

# Launch production HTTP client asynchronously while the proxy is holding the
# REAL Django/Postgres 201 response; cut the Android uplink while still in POST.
capture_log=$(mktemp)
"${ADB[@]}" shell am instrument -w -e phase capture \
  -e productId "$product_id" -e baseUrl "$API_URL" -e class "$TEST" "$INSTRUMENTATION" \
  > "$capture_log" 2>&1 &
capture_pid=$!

held=0
for i in $(seq 1 60); do
  if python3 - "$MARKER" <<'PY'
import json,sys
try:
    x=json.load(open(sys.argv[1]))
    assert x["hold_response"] and x["holding"] >= 1
    assert x["events"][0]["upstream_status"] == 201
    assert not x["released_after_cut"]
except (OSError,ValueError,AssertionError,KeyError,IndexError):
    sys.exit(1)
PY
  then held=1; break; fi
  if ! kill -0 "$capture_pid" 2>/dev/null; then
    cat "$capture_log"
    echo "FAIL: Android exited before backend 201 was held" >&2; exit 1
  fi
  sleep 0.15
done
test "$held" == 1 || { cat "$capture_log"; echo "FAIL: no live committed POST held" >&2; exit 1; }
kill -0 "$capture_pid" 2>/dev/null || { echo "FAIL: POST no longer in flight" >&2; exit 1; }
echo "PASS: real Django HTTP 201 committed; Android POST still blocked awaiting response"

if [[ "$MODE" == emulator-link ]]; then
  "${ADB[@]}" shell ip link set "$IFACE" down
else
  "${ADB[@]}" shell svc wifi disable
fi
network_is_down=1
# Verification is fail-closed. Merely disabling Android Wi-Fi without removing
# the actual route (e.g. emulator still using eth0) cannot pass this test.
route_after=$("${ADB[@]}" shell ip route get "$HOST_IP" 2>&1 | tr -d '\r' || true)
link_after=$("${ADB[@]}" shell ip -o link show dev "$IFACE" 2>&1 | tr -d '\r' || true)
echo "ROUTE_AFTER_CUT: $route_after"
echo "LINK_AFTER_CUT: $link_after"
# Linux may preserve a linkdown route, so the link must be DOWN
# (not merely missing a route). Check for any alternate live route too.
if ! grep -qE 'state DOWN|does not exist|Device not found' <<< "$link_after"; then
  echo "FAIL: actual interface $IFACE was NOT switched down" >&2; exit 1
fi
if [[ "$MODE" == physical-wifi ]]; then
  wifi_status=$("${ADB[@]}" shell cmd wifi status 2>&1 | tr -d '\r')
  echo "WIFI_AFTER_CUT: $wifi_status"
  grep -qi 'disabled' <<< "$wifi_status" || {
    echo "FAIL: Wi-Fi still enabled on physical phone" >&2; exit 1;
  }
fi
if grep -Eq 'dev (wlan|rmnet|ccmni|eth)[0-9]+' <<< "$route_after" &&
   ! grep -q "dev $IFACE" <<< "$route_after"; then
  echo "FAIL: alternative network route remains (cellular or Ethernet)" >&2; exit 1
fi
echo "PASS: Android actual uplink $IFACE is down while HTTP POST is held"

# Release the REAL upstream bytes after link loss. Because the client is
# offline, it must receive IOException rather than a successful order ACK.
python3 - <<'PY'
from urllib.request import Request,urlopen
req=Request("http://127.0.0.1:8000/__fault/release-after-cut", data=b"", method="POST")
with urlopen(req, timeout=5) as response:
    assert response.status == 200
print("PASS: committed response released only AFTER link cut")
PY
wait "$capture_pid" || { cat "$capture_log"; echo "FAIL: lost-response Android test" >&2; exit 1; }
cat "$capture_log"
grep -q 'OK (1 test)' "$capture_log" || { echo "FAIL: Android did not detect network loss" >&2; exit 1; }
python3 "$ROOT/scripts/verify-android-live-post-drop.py" before --fixture "$FIXTURE" --marker "$MARKER"
echo "PASS: original encrypted CHECKING intent survived lost HTTP response"

force_stop_running
run_stage offline
force_stop_running

# The proxy is disarmed only after the offline and process-death gates.
python3 - <<'PY'
from urllib.request import Request,urlopen
req=Request("http://127.0.0.1:8000/__fault/disarm", data=b"", method="POST")
with urlopen(req, timeout=5) as response:
    assert response.status == 200
PY
cleanup
network_is_down=0
recovered=0
for i in $(seq 1 20); do
  route_up=$("${ADB[@]}" shell ip route get "$HOST_IP" 2>&1 | tr -d '\r' || true)
  if grep -q "dev $IFACE" <<< "$route_up"; then recovered=1; break; fi
  sleep 1
done
test "$recovered" == 1 || { echo "FAIL: Android link did not recover" >&2; exit 1; }
echo "PASS: Android network route recovered ($IFACE)"

run_stage replay
python3 "$ROOT/scripts/verify-android-live-post-drop.py" after \
  --fixture "$FIXTURE" --marker "$MARKER" --receipt "$ROOT/artifacts/android-active-network-cut.json"
"${ADB[@]}" shell am force-stop "$APP_ID"
echo "PASS: actual uplink cut during committed POST, offline process death, same-key replay, exactly one order/charge."
