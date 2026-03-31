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

# Helper: send progress to session chat (footer auto-appended by jbot-send.sh)
report() {
    $SEND "$SESSION_CHAT_ID" "<p><b>J-Bot [$SESSION_ID]</b> $1</p>" 2>/dev/null || true
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
WORKER_PROMPT="You are J-Bot, working on task [$SESSION_ID].
Execute the task thoroughly.

## MANDATORY: Progress Reporting
You MUST report progress to your dedicated Teams chat using this exact command:
bash $REPO_DIR/scripts/jbot-send.sh \"$SESSION_CHAT_ID\" \"<html body here>\"

FORMATTING RULES:
- DO NOT append any footer/signature — jbot-send.sh adds it automatically.
- NEVER include '★ Insight' blocks in messages — those are internal only.
- NEVER send internal status like '已通知用户' or 'Notified user'.

### When to report:
1. IMMEDIATELY when you start working — send what you plan to do
2. After completing each major step — send what you found/did
3. When you encounter issues — send what went wrong
4. ALWAYS at the end — send the final summary/result

### Report format example:
bash $REPO_DIR/scripts/jbot-send.sh \"$SESSION_CHAT_ID\" \"<p><b>J-Bot [$SESSION_ID]</b> Step 1 done: analyzed 15 files, found 3 issues.</p>\"

NEVER use outlook-cli, calendar-cli, or teams-cli for write operations.
NEVER skip progress reporting — it is MANDATORY for every task.

## Microsoft 365 Tools (all via Graph API)
- bash $REPO_DIR/scripts/jbot-send.sh <chat_id> <html>  — Send Teams message
- bash $REPO_DIR/scripts/jbot-draft.sh <subject> <to> <html> [cc]  — Create Outlook draft
- bash $REPO_DIR/scripts/jbot-email.sh <subject> <to> <html> [cc]  — Send email directly
- bash $REPO_DIR/scripts/jbot-calendar.sh <subject> <start> <end> [attendee] [body]  — Create calendar event

## CRITICAL: The user CANNOT see your text output
Your ONLY way to communicate with the user is via jbot-send.sh.
If you don't call jbot-send.sh, the user sees NOTHING — no matter what text you return.
You MUST call jbot-send.sh at least TWICE: once at the start, once with the final result."

# Determine claude command
if command -v clp >/dev/null 2>&1; then
    CLAUDE_CMD="clp run -- claude"
else
    CLAUDE_CMD="claude"
fi

echo "[$(date '+%H:%M:%S')] Running claude..."

# Capture stdout (JSON) and stderr separately
WORKER_STDOUT_FILE=$(mktemp /tmp/jbot-worker-XXXXXX.json)
$CLAUDE_CMD -p "$TASK_DESC" \
    --model opus \
    --output-format json \
    --permission-mode bypassPermissions \
    --name "jbot-${USER_EMAIL%%@*}-${SESSION_ID}" \
    --append-system-prompt "$WORKER_PROMPT" \
    --add-dir "$WORK_DIR" \
    > "$WORKER_STDOUT_FILE" 2>/dev/null || true

echo "[$(date '+%H:%M:%S')] Claude exited."

# Extract result and session_id from claude JSON output
eval "$(python3 -c "
import json, sys, shlex

try:
    data = json.load(open(sys.argv[1]))
    result = (data.get('result', '') or '')[:2000]
    sid = data.get('session_id', '') or ''
except Exception:
    result = 'Worker completed'
    sid = ''

# Output shell variable assignments
print(f'WORKER_RESULT={shlex.quote(result)}')
print(f'CLAUDE_SESSION_ID={shlex.quote(sid)}')
" "$WORKER_STDOUT_FILE" 2>/dev/null || echo 'WORKER_RESULT="Worker completed"
CLAUDE_SESSION_ID=""')"

rm -f "$WORKER_STDOUT_FILE"

echo "[$(date '+%H:%M:%S')] Result: ${WORKER_RESULT:0:200}"
echo "[$(date '+%H:%M:%S')] Claude session: ${CLAUDE_SESSION_ID:-none}"

# HTML-escape the result before embedding (prevents XSS from claude output)
SAFE_RESULT=$(python3 -c "import html,sys; print(html.escape(sys.stdin.read()[:500]))" <<< "$WORKER_RESULT" 2>/dev/null || echo "$WORKER_RESULT")

# Update DB with result + claude session ID (enables --resume for follow-up)
python3 -c "
import sys, sqlite3, time, pathlib
db = sqlite3.connect(str(pathlib.Path.home() / '.jbot' / 'jbot.db'))
db.execute('UPDATE sessions SET status=?, last_output=?, claude_session=?, updated_at=? WHERE id=?',
    (sys.argv[1], sys.argv[2], sys.argv[3] or None, time.time(), sys.argv[4]))
db.commit()
" "completed" "$WORKER_RESULT" "$CLAUDE_SESSION_ID" "$SESSION_ID" 2>/dev/null || true

# Send completion to dedicated session chat
report "✅ Task completed.<br/>$SAFE_RESULT"

# Send completion to manager chat (footer auto-appended by jbot-send.sh)
$SEND "$MANAGER_CHAT_ID" \
    "<p><b>J-Bot</b> ✅ Task <code>$SESSION_ID</code> done.</p><p>$SAFE_RESULT</p>" \
    2>/dev/null || true

echo "[$(date '+%H:%M:%S')] Worker $SESSION_ID done."
