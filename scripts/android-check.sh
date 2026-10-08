#!/usr/bin/env bash
set -euo pipefail

readonly REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly APP_DIR="$REPOSITORY_ROOT/apps/attendance-android"
readonly PLATFORM_DIR="platforms/android-37.0"
readonly BUILD_TOOLS_DIR="build-tools/37.0.0"

if ! command -v java >/dev/null 2>&1; then
  echo "JDK 17 is required. Run scripts/android-setup.sh after installing it." >&2
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
if [[ ! -d "$sdk_root/$PLATFORM_DIR" || ! -d "$sdk_root/$BUILD_TOOLS_DIR" ]]; then
  echo "Android SDK at $sdk_root is missing $PLATFORM_DIR or $BUILD_TOOLS_DIR." >&2
  echo "Run scripts/android-setup.sh with ANDROID_HOME=$sdk_root." >&2
  exit 1
fi

export ANDROID_HOME="$sdk_root"
export ANDROID_SDK_ROOT="$sdk_root"
export PATH="$ANDROID_HOME/platform-tools:$PATH"

(
  cd "$APP_DIR"
  ./gradlew testDebugUnitTest assembleDebug lintDebug --stacktrace
)

if [[ "${ANDROID_SMOKE:-0}" == "1" ]]; then
  serial="$(adb devices | awk '$2 == "device" { print $1; exit }')"
  if [[ -z "$serial" ]]; then
    echo "ANDROID_SMOKE=1 requested but no authorized emulator/device is connected." >&2
    exit 1
  fi
  (
    cd "$APP_DIR"
    ./gradlew installDebug
  )
  adb -s "$serial" shell am start -W -n com.rodada.attendance/.MainActivity
fi
