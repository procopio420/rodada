#!/usr/bin/env bash
set -euo pipefail

# Installs only public Android SDK tooling needed by Rodada Atendimento.  The SDK stays
# outside the repository; local.properties is intentionally gitignored.
readonly COMPILE_SDK_PACKAGE="platforms;android-37.0"
readonly BUILD_TOOLS_PACKAGE="build-tools;37.0.0"
readonly COMMAND_LINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip"
readonly REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly APP_DIR="$REPOSITORY_ROOT/apps/attendance-android"

if ! command -v java >/dev/null 2>&1; then
  echo "JDK 17 is required. Install it and set JAVA_HOME before running this script." >&2
  exit 1
fi

java_version="$(java -version 2>&1 | head -n1)"
if [[ ! "$java_version" =~ \"17\. ]]; then
  echo "Rodada Atendimento requires JDK 17; found: $java_version" >&2
  exit 1
fi

sdk_root="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}}"
export ANDROID_HOME="$sdk_root"
export ANDROID_SDK_ROOT="$sdk_root"

sdkmanager="$sdk_root/cmdline-tools/latest/bin/sdkmanager"
if [[ ! -x "$sdkmanager" ]]; then
  if ! command -v curl >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
    echo "curl and unzip are required to bootstrap Android command-line tools." >&2
    exit 1
  fi
  mkdir -p "$sdk_root/cmdline-tools"
  if [[ -e "$sdk_root/cmdline-tools/latest" ]]; then
    echo "Android command-line tools exist but sdkmanager is not executable: $sdkmanager" >&2
    exit 1
  fi
  temp_dir="$(mktemp -d)"
  trap 'rm -rf "$temp_dir"' EXIT
  curl --fail --location --retry 3 --output "$temp_dir/commandlinetools.zip" "$COMMAND_LINE_TOOLS_URL"
  unzip -q "$temp_dir/commandlinetools.zip" -d "$temp_dir"
  mv "$temp_dir/cmdline-tools" "$sdk_root/cmdline-tools/latest"
fi

yes | "$sdkmanager" --sdk_root="$sdk_root" --licenses >/dev/null
"$sdkmanager" --sdk_root="$sdk_root" \
  "platform-tools" \
  "$COMPILE_SDK_PACKAGE" \
  "$BUILD_TOOLS_PACKAGE"

if [[ ! -f "$APP_DIR/local.properties" ]]; then
  printf 'sdk.dir=%s\n' "$sdk_root" > "$APP_DIR/local.properties"
fi

cat <<EOF
Android SDK ready at: $sdk_root
For this shell, export ANDROID_HOME=$sdk_root
Next: $REPOSITORY_ROOT/scripts/android-check.sh
EOF
