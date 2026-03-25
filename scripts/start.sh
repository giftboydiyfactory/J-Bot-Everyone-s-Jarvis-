#!/bin/bash
# J-Bot start: kill old processes, start with watchdog (auto-restart on crash)
# Survives SSH disconnect via nohup. Logs to ~/.jbot/jbot.log
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO_DIR/.venv"
PIDFILE="$HOME/.jbot/watchdog.pid"

# 1. Kill old processes
echo "🤖 J-Bot: starting..."
echo "  [1/3] Killing old processes..."
# Kill old watchdog
if [ -f "$PIDFILE" ]; then
    kill $(cat "$PIDFILE") 2>/dev/null || true
    rm -f "$PIDFILE"
fi
pkill -9 -f "niuma" 2>/dev/null || true
sleep 1

# 2. Ensure venv
if [ ! -d "$VENV" ]; then
    echo "  [2/3] Creating venv..."
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    pip install -e "$REPO_DIR[dev]" --quiet
else
    echo "  [2/3] Venv exists, activating..."
    source "$VENV/bin/activate"
fi

# Auto-migrate from ~/.niuma/ if needed
bash "$REPO_DIR/scripts/migrate.sh" 2>/dev/null || true

mkdir -p "$HOME/.jbot"

# 3. Start watchdog loop (nohup + background = survives SSH disconnect)
echo "  [3/3] Starting watchdog..."
nohup bash -c '
VENV="'"$VENV"'"
PIDFILE="'"$PIDFILE"'"
echo $$ > "$PIDFILE"

source "$VENV/bin/activate"

while true; do
    echo "$(date "+%Y-%m-%d %H:%M:%S") [watchdog] Starting J-Bot..." >> ~/.jbot/jbot.log
    jbot 2>&1 | tee -a ~/.jbot/jbot.log || true
    echo "$(date "+%Y-%m-%d %H:%M:%S") [watchdog] J-Bot exited. Restarting in 10s..." >> ~/.jbot/jbot.log
    sleep 10
done
' > /dev/null 2>&1 &

# Wait for watchdog to write its PID
for i in 1 2 3 4 5; do
    [ -f "$PIDFILE" ] && break
    sleep 1
done

echo ""
echo "✅ J-Bot started with watchdog (PID: $(cat "$PIDFILE" 2>/dev/null || echo 'starting...'))"
echo "   Auto-restarts on crash. Survives SSH disconnect."
echo "   Logs:    tail -f ~/.jbot/jbot.log"
echo "   Stop:    bash scripts/stop.sh"
