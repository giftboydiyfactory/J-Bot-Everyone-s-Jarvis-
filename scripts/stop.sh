#!/bin/bash
# Stop J-Bot and its watchdog
PIDFILE="$HOME/.jbot/watchdog.pid"

echo "🤖 J-Bot: stopping..."
if [ -f "$PIDFILE" ]; then
    kill $(cat "$PIDFILE") 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "  Watchdog stopped."
fi
pkill -9 -f "niuma" 2>/dev/null || true
echo "✅ J-Bot stopped."
