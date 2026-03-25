#!/bin/bash
# Install J-Bot as a macOS launchd service (auto-restart on crash, survive SSH disconnect)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.jbot.daemon.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.jbot.daemon.plist"

echo "🤖 J-Bot: Installing launchd service..."

# 1. Stop existing daemon processes
echo "  [1/4] Stopping old processes..."
launchctl bootout gui/$(id -u) "$PLIST_DST" 2>/dev/null || true
pkill -9 -f "niuma.main" 2>/dev/null || true
sleep 1

# 2. Ensure dirs exist
echo "  [2/4] Ensuring directories..."
mkdir -p "$HOME/.niuma"
mkdir -p "$HOME/Library/LaunchAgents"

# 3. Copy plist
echo "  [3/4] Installing plist..."
cp "$PLIST_SRC" "$PLIST_DST"

# 4. Load service
echo "  [4/4] Loading service..."
launchctl bootstrap gui/$(id -u) "$PLIST_DST"

echo ""
echo "✅ J-Bot service installed!"
echo "   Status:  launchctl print gui/$(id -u)/com.jbot.daemon"
echo "   Logs:    tail -f ~/.niuma/launchd-stderr.log"
echo "   Stop:    launchctl bootout gui/$(id -u) $PLIST_DST"
echo "   Restart: launchctl kickstart -k gui/$(id -u)/com.jbot.daemon"
echo ""
echo "   J-Bot will auto-restart on crash and survive SSH disconnects."
