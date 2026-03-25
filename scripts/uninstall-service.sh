#!/bin/bash
# Uninstall J-Bot launchd service
set -euo pipefail

PLIST_DST="$HOME/Library/LaunchAgents/com.jbot.daemon.plist"

echo "🤖 J-Bot: Uninstalling launchd service..."

launchctl bootout gui/$(id -u) "$PLIST_DST" 2>/dev/null || true
rm -f "$PLIST_DST"
pkill -9 -f "niuma.main" 2>/dev/null || true

echo "✅ J-Bot service removed."
echo "   To run manually: bash scripts/start.sh"
