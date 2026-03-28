#!/bin/bash
# jbot-worker-run.sh — Actually runs the Claude worker (called by jbot-worker.sh in background)
# Usage: jbot-worker-run.sh <repo_dir> <session_id> <session_chat_id> <manager_chat_id> <user_email> <work_dir> <task_file>
#
# This script is NOT meant to be called directly — use jbot-worker.sh instead.

set -euo pipefail

REPO_DIR="$1"
SESSION_ID="$2"
SESSION_CHAT_ID="$3"
MANAGER_CHAT_ID="$4"
USER_EMAIL="$5"
WORK_DIR="$6"
TASK_FILE="$7"

TASK_DESC=$(cat "$TASK_FILE")
rm -f "$TASK_FILE"

# Activate venv
source "$REPO_DIR/.venv/bin/activate"
export PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}"

SEND="bash $REPO_DIR/scripts/jbot-send.sh"

# Helper: send progress to session chat
report() {
    $SEND "$SESSION_CHAT_ID" "<p><b>J-Bot [$SESSION_ID]</b> $1</p><hr/><p><em>Sent by J-Bot</em></p>" 2>/dev/null || true
}

# Helper: update DB status
update_db() {
    local status="$1"
    local output="$2"
    python3 -c "
import sys, sqlite3, time, pathlib
db = sqlite3.connect(str(pathlib.Path.home() / '.jbot' / 'jbot.db'))
db.execute('UPDATE sessions SET status=?, last_output=?, updated_at=? WHERE id=?',
    (sys.argv[1], sys.argv[2], time.time(), sys.argv[3]))
db.commit()
" "$status" "$output" "$SESSION_ID" 2>/dev/null || true
}

echo "[$(date '+%H:%M:%S')] Worker $SESSION_ID starting..."
echo "[$(date '+%H:%M:%S')] Task: $TASK_DESC"
echo "[$(date '+%H:%M:%S')] CWD: $WORK_DIR"

# Build worker system prompt
WORKER_PROMPT="You are a J-Bot worker session [$SESSION_ID].
Execute the task thoroughly.

## MANDATORY: Progress Reporting
You MUST report progress to your dedicated Teams chat using this exact command:
bash $REPO_DIR/scripts/jbot-send.sh \"$SESSION_CHAT_ID\" \"<html body here><hr/><p><em>Sent by J-Bot</em></p>\"

### When to report:
1. IMMEDIATELY when you start working — send what you plan to do
2. After completing each major step — send what you found/did
3. When you encounter issues — send what went wrong
4. ALWAYS at the end — send the final summary/result

### Report format example:
bash $REPO_DIR/scripts/jbot-send.sh \"$SESSION_CHAT_ID\" \"<p><b>J-Bot [$SESSION_ID]</b> Step 1 done: analyzed 15 files, found 3 issues.</p><hr/><p><em>Sent by J-Bot</em></p>\"

NEVER use teams-cli — it is NOT available. Always use jbot-send.sh.
NEVER skip progress reporting — it is MANDATORY for every task."

# Determine claude command
if command -v clp >/dev/null 2>&1; then
    CLAUDE_CMD="clp run -- claude"
else
    CLAUDE_CMD="claude"
fi

echo "[$(date '+%H:%M:%S')] Running claude..."

WORKER_OUTPUT=$($CLAUDE_CMD -p "$TASK_DESC" \
    --model opus \
    --output-format json \
    --permission-mode bypassPermissions \
    --name "jbot-${USER_EMAIL%%@*}-${SESSION_ID}" \
    --append-system-prompt "$WORKER_PROMPT" \
    --add-dir "$WORK_DIR" \
    2>&1) || true

echo "[$(date '+%H:%M:%S')] Claude exited."

# Extract result
WORKER_RESULT=$(echo "$WORKER_OUTPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    r = data.get('result', '') or ''
    print(r[:2000])
except:
    raw = sys.stdin.read() if hasattr(sys.stdin, 'read') else ''
    print(raw[:2000] if raw else 'Worker completed (no structured output)')
" 2>/dev/null || echo "Worker completed")

echo "[$(date '+%H:%M:%S')] Result: ${WORKER_RESULT:0:200}"

# Update DB
update_db "completed" "$WORKER_RESULT"

# Send completion to dedicated session chat
report "✅ Task completed.<br/>${WORKER_RESULT:0:500}"

# Send completion to manager chat
$SEND "$MANAGER_CHAT_ID" \
    "<p><b>J-Bot</b> ✅ Worker <code>$SESSION_ID</code> finished.</p><p>${WORKER_RESULT:0:300}</p><hr/><p><em>Sent by J-Bot</em></p>" \
    2>/dev/null || true

echo "[$(date '+%H:%M:%S')] Worker $SESSION_ID done."
