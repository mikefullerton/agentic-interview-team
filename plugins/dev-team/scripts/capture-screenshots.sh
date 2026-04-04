#!/bin/bash
# capture-screenshots.sh — Build a macOS app, launch it, capture window screenshots
# Usage: capture-screenshots.sh <project-path> <output-dir> [--no-swiftui]
# Requires: Xcode command line tools, screencapture
# Outputs: PNG screenshots in <output-dir>/

set -euo pipefail

PROJECT_PATH="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

# Step 1: Build the app
echo "Building app at $PROJECT_PATH..." >&2
BUILD_DIR="$PROJECT_PATH/.build/release"

if [[ -f "$PROJECT_PATH/Package.swift" ]]; then
  cd "$PROJECT_PATH"
  swift build -c release 2>&1 | tail -5 >&2
  APP_NAME=$(swift package describe --type json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null || basename "$PROJECT_PATH")
  APP_PATH=$(find "$BUILD_DIR" -name "*.app" -maxdepth 1 2>/dev/null | head -1)
  if [[ -z "$APP_PATH" ]]; then
    APP_PATH="$BUILD_DIR/$APP_NAME"
  fi
elif [[ -f "$PROJECT_PATH/Makefile" ]]; then
  cd "$PROJECT_PATH"
  make release 2>&1 | tail -5 >&2
  APP_PATH=$(find . -name "*.app" -maxdepth 3 2>/dev/null | head -1)
else
  echo "Cannot determine build system for $PROJECT_PATH" >&2
  exit 1
fi

if [[ -z "$APP_PATH" || ! -e "$APP_PATH" ]]; then
  echo "Build succeeded but no app found at expected location" >&2
  exit 1
fi

# Step 2: Launch the app
echo "Launching $APP_PATH..." >&2
if [[ -d "$APP_PATH" ]]; then
  open -a "$APP_PATH" --args --screenshot-mode 2>/dev/null &
else
  "$APP_PATH" &
fi
APP_PID=$!

# Wait for window to appear (up to 10 seconds)
WINDOW_COUNT=0
for i in $(seq 1 20); do
  sleep 0.5
  WINDOW_COUNT=$(osascript -e "tell application \"System Events\" to count windows of (first process whose unix id is $APP_PID)" 2>/dev/null || echo "0")
  if [[ "$WINDOW_COUNT" -gt 0 ]]; then
    break
  fi
done

if [[ "$WINDOW_COUNT" -eq 0 ]]; then
  echo "App launched but no windows appeared after 10 seconds" >&2
  kill "$APP_PID" 2>/dev/null || true
  exit 1
fi

# Step 3: Capture main window
echo "Capturing launch state..." >&2
sleep 1
screencapture -l "$(osascript -e "tell application \"System Events\" to get id of first window of (first process whose unix id is $APP_PID)" 2>/dev/null)" "$OUTPUT_DIR/01-launch-state.png" 2>/dev/null || \
  screencapture -w "$OUTPUT_DIR/01-launch-state.png" 2>/dev/null || \
  echo "Could not capture window screenshot" >&2

# Step 4: Capture menu items (best-effort)
SCREENSHOT_NUM=2
APP_PROCESS_NAME=$(osascript -e "tell application \"System Events\" to get name of (first process whose unix id is $APP_PID)" 2>/dev/null || echo "")

if [[ -n "$APP_PROCESS_NAME" ]]; then
  MENUS=$(osascript -e "
    tell application \"System Events\"
      tell process \"$APP_PROCESS_NAME\"
        get name of every menu bar item of menu bar 1
      end tell
    end tell
  " 2>/dev/null || echo "")

  for menu in $MENUS; do
    [[ "$menu" == "Apple" ]] && continue
    osascript -e "
      tell application \"System Events\"
        tell process \"$APP_PROCESS_NAME\"
          click menu bar item \"$menu\" of menu bar 1
        end tell
      end tell
    " 2>/dev/null || continue
    sleep 0.5
    screencapture "$OUTPUT_DIR/$(printf '%02d' $SCREENSHOT_NUM)-menu-$menu.png" 2>/dev/null || true
    SCREENSHOT_NUM=$((SCREENSHOT_NUM + 1))
    osascript -e 'tell application "System Events" to key code 53' 2>/dev/null || true
    sleep 0.3
  done
fi

# Step 5: Quit the app
echo "Quitting app..." >&2
kill "$APP_PID" 2>/dev/null || true
wait "$APP_PID" 2>/dev/null || true

echo "Captured screenshots in $OUTPUT_DIR" >&2
ls -1 "$OUTPUT_DIR"/*.png 2>/dev/null | wc -l | xargs echo "Total screenshots:" >&2
