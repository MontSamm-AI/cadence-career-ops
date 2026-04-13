#!/usr/bin/env bash
# =============================================================================
# Chrome CDP Setup — Enable Chrome DevTools Protocol for Cadence Career Ops
# =============================================================================
# Run on Windows (Git Bash / WSL calling Windows Chrome)
# This script creates a Chrome launcher shortcut with CDP enabled on port 9222
# =============================================================================

CDP_PORT=9222
CHROME_PATHS=(
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
)

echo "=== Chrome CDP Setup ==="
echo ""

# Find Chrome
CHROME_EXE=""
for path in "${CHROME_PATHS[@]}"; do
    if [ -f "$path" ]; then
        CHROME_EXE="$path"
        break
    fi
done

if [ -z "$CHROME_EXE" ]; then
    echo "ERROR: Chrome not found. Install Google Chrome and retry."
    echo "Checked paths:"
    for path in "${CHROME_PATHS[@]}"; do echo "  $path"; done
    exit 1
fi

echo "Found Chrome: $CHROME_EXE"
echo ""

# Create a Chrome profile for automation
PROFILE_DIR="$HOME/.cadence-chrome-profile"
mkdir -p "$PROFILE_DIR"

echo "Profile directory: $PROFILE_DIR"
echo ""

# Build the launch command (Windows path format for .bat file)
WIN_CHROME=$(echo "$CHROME_EXE" | sed 's|/mnt/c|C:|' | sed 's|/|\\|g')
WIN_PROFILE=$(wslpath -w "$PROFILE_DIR")

# Write a Windows .bat launcher
BAT_FILE="$HOME/start-cadence-chrome.bat"
cat > "$BAT_FILE" << EOF
@echo off
rem Cadence Career Ops — Chrome CDP Launcher
rem Run this on Windows to start Chrome with DevTools Protocol enabled

set CHROME="$WIN_CHROME"
set PROFILE="$WIN_PROFILE"
set PORT=$CDP_PORT

echo Starting Chrome with CDP on port %PORT%...
start "" %CHROME% ^
    --remote-debugging-port=%PORT% ^
    --user-data-dir=%PROFILE% ^
    --no-first-run ^
    --no-default-browser-check
echo Chrome started. Test with: curl http://localhost:%PORT%/json/version
EOF

WIN_BAT=$(wslpath -w "$BAT_FILE")
echo "Created Windows launcher: $WIN_BAT"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "To start Chrome with CDP:"
echo "  Windows: Double-click or run: $WIN_BAT"
echo "  Or manually run Chrome with: --remote-debugging-port=$CDP_PORT"
echo ""
echo "To verify CDP is working (from WSL):"
echo "  curl http://localhost:$CDP_PORT/json/version"
echo ""
echo "IMPORTANT:"
echo "  1. Log into LinkedIn manually in this Chrome window first"
echo "  2. Keep this Chrome window open while running automation"
echo "  3. Never use the same Chrome profile for both personal and automation use"
echo ""
echo "Next: Run 'python3 scripts/skills/test_browser.py' to verify connection"
