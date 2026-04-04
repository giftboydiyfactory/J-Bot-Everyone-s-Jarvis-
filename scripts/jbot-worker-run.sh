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
# Uses a temp file to avoid shell expansion of HTML content
report() {
    local tmpfile
    tmpfile=$(mktemp /tmp/jbot-report-XXXXXX)
    printf '%s' "<p><b>J-Bot [$SESSION_ID]</b> $1</p>" > "$tmpfile"
    $SEND "$SESSION_CHAT_ID" "$(cat "$tmpfile")" 2>/dev/null || true
    rm -f "$tmpfile"
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

# Phase 3: Update heartbeat before starting work
python3 -c "
import sqlite3, time, pathlib, sys
db = sqlite3.connect(str(pathlib.Path.home() / '.jbot' / 'jbot.db'))
db.execute('PRAGMA busy_timeout = 10000')
db.execute('UPDATE sessions SET last_heartbeat=?, updated_at=? WHERE id=?',
    (time.time(), time.time(), sys.argv[1]))
db.commit()
" "$SESSION_ID" 2>/dev/null || true

echo "[$(date '+%H:%M:%S')] Running claude..."

# Capture stdout (JSON) and stderr separately
WORKER_STDOUT_FILE=$(mktemp /tmp/jbot-worker-XXXXXX.json)
WORKER_MODEL=${JBOT_WORKER_MODEL:-opus}
WORKER_PERM=${JBOT_PERM_MODE:-bypassPermissions}
$CLAUDE_CMD -p "$TASK_DESC" \
    --model "$WORKER_MODEL" \
    --output-format json \
    --permission-mode "$WORKER_PERM" \
    --name "jbot-${USER_EMAIL%%@*}-${SESSION_ID}" \
    --append-system-prompt "$WORKER_PROMPT" \
    --add-dir "$WORK_DIR" \
    > "$WORKER_STDOUT_FILE" 2>/dev/null
CLAUDE_EXIT_CODE=$?

echo "[$(date '+%H:%M:%S')] Claude exited with code $CLAUDE_EXIT_CODE."

# Extract result and session_id from claude JSON output (no eval — safe extraction)
TMPDIR_PARSE=$(mktemp -d /tmp/jbot-parse-XXXXXX)
python3 -c "
import json, sys, pathlib
tmpdir = sys.argv[2]
try:
    data = json.load(open(sys.argv[1]))
    pathlib.Path(tmpdir, 'result').write_text((data.get('result', '') or '')[:2000])
    pathlib.Path(tmpdir, 'session_id').write_text(data.get('session_id', '') or '')
except Exception:
    pathlib.Path(tmpdir, 'result').write_text('Worker completed')
    pathlib.Path(tmpdir, 'session_id').write_text('')
" "$WORKER_STDOUT_FILE" "$TMPDIR_PARSE" 2>/dev/null || true

WORKER_RESULT=$(cat "$TMPDIR_PARSE/result" 2>/dev/null || echo "Worker completed")
CLAUDE_SESSION_ID=$(cat "$TMPDIR_PARSE/session_id" 2>/dev/null || echo "")
rm -rf "$TMPDIR_PARSE" "$WORKER_STDOUT_FILE"

echo "[$(date '+%H:%M:%S')] Result: ${WORKER_RESULT:0:200}"
echo "[$(date '+%H:%M:%S')] Claude session: ${CLAUDE_SESSION_ID:-none}"

# HTML-escape the result before embedding (prevents XSS from claude output)
SAFE_RESULT=$(python3 -c "import html,sys; print(html.escape(sys.stdin.read()[:500]))" <<< "$WORKER_RESULT" 2>/dev/null || echo "$WORKER_RESULT")

# Determine final status based on Claude exit code
if [ "$CLAUDE_EXIT_CODE" -eq 0 ]; then
    FINAL_STATUS="completed"
else
    FINAL_STATUS="failed"
    WORKER_RESULT="[EXIT CODE $CLAUDE_EXIT_CODE] ${WORKER_RESULT}"
fi

# Update DB with result + claude session ID (enables --resume for follow-up)
python3 -c "
import sys, sqlite3, time, pathlib
db = sqlite3.connect(str(pathlib.Path.home() / '.jbot' / 'jbot.db'))
db.execute('PRAGMA busy_timeout = 10000')
db.execute('UPDATE sessions SET status=?, last_output=?, claude_session=?, updated_at=? WHERE id=?',
    (sys.argv[1], sys.argv[2], sys.argv[3] or None, time.time(), sys.argv[4]))
db.commit()
" "$FINAL_STATUS" "$WORKER_RESULT" "$CLAUDE_SESSION_ID" "$SESSION_ID" 2>/dev/null || true

# Send completion to dedicated session chat (via temp file for safety)
COMPLETION_HTML=$(printf '<p><b>J-Bot [%s]</b> Task completed.</p><p>%s</p>' "$SESSION_ID" "$SAFE_RESULT")
$SEND "$SESSION_CHAT_ID" "$COMPLETION_HTML" 2>/dev/null || true

# Send completion to manager chat (via temp file for safety)
MGR_HTML=$(printf '<p><b>J-Bot</b> Task <code>%s</code> done.</p><p>%s</p>' "$SESSION_ID" "$SAFE_RESULT")
$SEND "$MANAGER_CHAT_ID" "$MGR_HTML" 2>/dev/null || true

# Phase 3: Report to additional chats if REPORT_CHAT_IDS is set (JSON array or comma-separated)
if [ -n "${REPORT_CHAT_IDS:-}" ]; then
    echo "[$(date '+%H:%M:%S')] Reporting to additional chats: $REPORT_CHAT_IDS"
    # Parse JSON array or comma-separated list
    EXTRA_CHATS=$(python3 -c "
import sys, json
raw = sys.argv[1]
try:
    ids = json.loads(raw)
except (json.JSONDecodeError, TypeError):
    ids = [s.strip() for s in raw.split(',') if s.strip()]
for cid in ids:
    print(cid)
" "$REPORT_CHAT_IDS" 2>/dev/null || true)
    while IFS= read -r EXTRA_CHAT_ID; do
        if [ -n "$EXTRA_CHAT_ID" ] && [ "$EXTRA_CHAT_ID" != "$SESSION_CHAT_ID" ] && [ "$EXTRA_CHAT_ID" != "$MANAGER_CHAT_ID" ]; then
            EXTRA_HTML=$(printf '<p><b>J-Bot</b> Task <code>%s</code> done.</p><p>%s</p>' "$SESSION_ID" "$SAFE_RESULT")
            $SEND "$EXTRA_CHAT_ID" "$EXTRA_HTML" 2>/dev/null || true
            echo "[$(date '+%H:%M:%S')] Reported to extra chat: ${EXTRA_CHAT_ID:0:20}..."
        fi
    done <<< "$EXTRA_CHATS"
fi

echo "[$(date '+%H:%M:%S')] Worker $SESSION_ID done."
