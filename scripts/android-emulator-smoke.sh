#!/usr/bin/env bash
set -euo pipefail

# Boots the known-good headless development AVD, verifies host API reachability
# through 10.0.2.2, then installs and opens Rodada Atendimento.  It deliberately
# leaves the emulator running so the operator can complete the real API smoke.
readonly REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly APP_DIR="$REPOSITORY_ROOT/apps/attendance-android"
readonly AVD_NAME="${RODADA_AVD_NAME:-rodada-api-36}"
readonly EMULATOR_PORT="${RODADA_EMULATOR_PORT:-5556}"
readonly SERIAL="emulator-$EMULATOR_PORT"
readonly SYSTEM_IMAGE_PACKAGE="system-images;android-36;google_apis;x86_64"
readonly SYSTEM_IMAGE_DIR="system-images/android-36/google_apis/x86_64"
readonly API_HOST="${RODADA_API_HOST:-10.0.2.2}"
readonly API_PORT="${RODADA_API_PORT:-8000}"
readonly API_HEALTH_URL="${RODADA_API_HEALTH_URL:-http://127.0.0.1:${API_PORT}/health/}"

usage() {
  cat <<EOF
Usage: scripts/android-emulator-smoke.sh [--provision]

Starts $AVD_NAME on $SERIAL using API 36 Google APIs with SwiftShader software
graphics, verifies $API_HOST:$API_PORT from Android, installs the debug APK and
opens Rodada Atendimento.

Options:
  --provision  install the emulator and API 36 system image, and create the AVD

Environment:
  ANDROID_HOME or ANDROID_SDK_ROOT   Android SDK location
  RODADA_AVD_NAME                   AVD name (default: rodada-api-36)
  RODADA_EMULATOR_PORT              emulator port (default: 5556)
  RODADA_API_HOST / RODADA_API_PORT Android-visible local API (10.0.2.2:8000)
  RODADA_API_HEALTH_URL             host health endpoint to preflight
  RODADA_EMULATOR_MEMORY_MB         emulator memory (default: 2048)
  RODADA_SMOKE_SKIP_BUILD=1         install an existing debug APK without assemble
  RODADA_SMOKE_LOGCAT=1             save current logcat after launch
EOF
}

provision=0
case "${1:-}" in
  "") ;;
  --provision) provision=1 ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

if ! command -v java >/dev/null 2>&1; then
  echo "JDK 17 is required. Set JAVA_HOME before running this script." >&2
  exit 1
fi
java_version="$(java -version 2>&1 | head -n1)"
if [[ ! "$java_version" =~ \"17\. ]]; then
  echo "Rodada Atendimento requires JDK 17; found: $java_version" >&2
  exit 1
fi

sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [[ -z "$sdk_root" && -f "$APP_DIR/local.properties" ]]; then
  sdk_root="$(sed -n 's#^sdk.dir=##p' "$APP_DIR/local.properties" | head -n1)"
fi
if [[ -z "$sdk_root" ]]; then
  echo "Android SDK was not located. Set ANDROID_HOME or run scripts/android-setup.sh." >&2
  exit 1
fi

export ANDROID_HOME="$sdk_root"
export ANDROID_SDK_ROOT="$sdk_root"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

sdkmanager="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
avdmanager="$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager"
emulator="$ANDROID_HOME/emulator/emulator"

if (( provision )); then
  if [[ ! -x "$sdkmanager" || ! -x "$avdmanager" ]]; then
    echo "Android command-line tools are missing. Run scripts/android-setup.sh first." >&2
    exit 1
  fi
  "$sdkmanager" --sdk_root="$ANDROID_HOME" "emulator" "$SYSTEM_IMAGE_PACKAGE"
fi

if [[ ! -x "$emulator" || ! -d "$ANDROID_HOME/$SYSTEM_IMAGE_DIR" ]]; then
  echo "Missing emulator or $SYSTEM_IMAGE_PACKAGE." >&2
  echo "Run: ANDROID_HOME=$ANDROID_HOME $0 --provision" >&2
  exit 1
fi

if [[ ! -x "$avdmanager" ]]; then
  echo "Android avdmanager is missing. Run scripts/android-setup.sh first." >&2
  exit 1
fi

if ! command -v adb >/dev/null 2>&1; then
  echo "adb is missing from $ANDROID_HOME/platform-tools." >&2
  exit 1
fi

if ! "$avdmanager" list avd | grep -Fqx "    Name: $AVD_NAME"; then
  if (( ! provision )); then
    echo "AVD $AVD_NAME does not exist." >&2
    echo "Run: ANDROID_HOME=$ANDROID_HOME $0 --provision" >&2
    exit 1
  fi
  printf 'no\n' | "$avdmanager" create avd --force --name "$AVD_NAME" --package "$SYSTEM_IMAGE_PACKAGE" --device "pixel_2"
fi

if ! curl --fail --silent --show-error --max-time 5 "$API_HEALTH_URL" >/dev/null; then
  cat >&2 <<EOF
The local API did not answer at $API_HEALTH_URL.
Start it on all host interfaces before the smoke, for example:
  cd apps/api && python manage.py runserver 0.0.0.0:$API_PORT
EOF
  exit 1
fi

adb start-server >/dev/null
if ! adb -s "$SERIAL" get-state 2>/dev/null | grep -qx "device"; then
  log_file="${RODADA_EMULATOR_LOG:-$(mktemp -t rodada-emulator.XXXXXX.log)}"
  "$emulator" \
    -avd "$AVD_NAME" \
    -port "$EMULATOR_PORT" \
    -no-snapshot \
    -no-boot-anim \
    -no-audio \
    -gpu swiftshader_indirect \
    -no-window \
    -memory "${RODADA_EMULATOR_MEMORY_MB:-2048}" \
    -netdelay none \
    -netspeed full \
    >"$log_file" 2>&1 &
  echo "Booting $SERIAL (emulator log: $log_file)"
fi

adb -s "$SERIAL" wait-for-device
for _ in {1..90}; do
  if [[ "$(adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; then
    break
  fi
  sleep 1
done
if [[ "$(adb -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]]; then
  echo "$SERIAL did not complete boot within 90 seconds." >&2
  exit 1
fi

reachable=0
for _ in {1..20}; do
  if adb -s "$SERIAL" shell toybox nc -z -w 3 "$API_HOST" "$API_PORT" >/dev/null 2>&1; then
    reachable=1
    break
  fi
  sleep 2
done
if (( ! reachable )); then
  cat >&2 <<EOF
Android cannot reach $API_HOST:$API_PORT. The debug app uses 10.0.2.2 for the
host machine; confirm the API is bound to 0.0.0.0 and the emulator is healthy.
EOF
  exit 1
fi

if [[ "${RODADA_SMOKE_SKIP_BUILD:-0}" != "1" ]]; then
  (
    cd "$APP_DIR"
    ./gradlew assembleDebug
  )
fi
(
  cd "$APP_DIR"
  ./gradlew installDebug
)
adb -s "$SERIAL" shell am start -W -n com.rodada.attendance/.MainActivity >/dev/null

if [[ "${RODADA_SMOKE_LOGCAT:-0}" == "1" ]]; then
  logcat_file="${RODADA_SMOKE_LOGCAT_FILE:-$(mktemp -t rodada-logcat.XXXXXX.log)}"
  adb -s "$SERIAL" logcat -d -v threadtime >"$logcat_file"
  echo "Saved logcat: $logcat_file"
fi

cat <<EOF
Rodada Atendimento is running on $SERIAL and reached the local API.

Complete the manual canonical API smoke in the app:
  1. Login: venue bar-do-aderlan, operator bia, PIN 1234.
  2. Confirm the restored/session screen loads Tabs and catalog from the API.
  3. Open a Tab, add a catalog item, and refresh to observe canonical state.

For a manager-only path, use ana / 0420. These credentials exist only after
running apps/api/manage.py seed_demo in local development.
EOF
