#!/usr/bin/env bash
set -euo pipefail

# Android Studio terminal helper:
# 1) Gradle sync equivalent
# 2) Clean project
# 3) Assemble project
# 4) Run app (install + launch)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANDROID_DIR="$ROOT_DIR/android-client"

APP_ID="${APP_ID:-ru.monitoring.mobile}"
MAIN_ACTIVITY="${MAIN_ACTIVITY:-.MainActivity}"
GRADLEW="$ANDROID_DIR/gradlew"

if [[ ! -x "$GRADLEW" ]]; then
  chmod +x "$GRADLEW"
fi

run_gradle() {
  local description="$1"
  shift
  echo "==> $description"
  "$GRADLEW" -p "$ANDROID_DIR" "$@"
}

run_gradle "Sync project with Gradle files (CLI equivalent)" help
run_gradle "Clean project" clean
run_gradle "Assemble project" assembleDebug
run_gradle "Install app on connected device/emulator" :app:installDebug

if ! command -v adb >/dev/null 2>&1; then
  echo "[WARN] adb not found in PATH. APK installed, but app launch skipped."
  echo "       Add Android SDK platform-tools to PATH and run again."
  exit 0
fi

if ! adb get-state >/dev/null 2>&1; then
  echo "[WARN] No active adb device/emulator. APK installed, but app launch skipped."
  echo "       Start an emulator or connect a device, then rerun this script."
  exit 0
fi

echo "==> Launch app"
adb shell am start -n "${APP_ID}/${MAIN_ACTIVITY}"

echo "✅ Done: sync + clean + assemble + install + run"
