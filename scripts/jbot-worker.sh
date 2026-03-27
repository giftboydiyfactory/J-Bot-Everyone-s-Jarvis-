#!/bin/bash
# jbot-worker.sh — Start a worker session with a dedicated Teams group chat
# Usage: jbot-worker.sh <manager_chat_id> <user_email> <task_description> [cwd]
#
# Returns IMMEDIATELY after creating the chat and launching the worker in background.
# The worker reports progress to its own dedicated Teams chat.
# On completion, updates the DB and sends a summary to both dedicated chat and manager chat.

set -euo pipefail

MANAGER_CHAT_ID="${1:?Usage: jbot-worker.sh <manager_chat_id> <user_email> <task_description> [cwd]}"
USER_EMAIL="${2:?Usage: jbot-worker.sh <manager_chat_id> <user_email> <task_description> [cwd]}"
TASK_DESC="${3:?Usage: jbot-worker.sh <manager_chat_id> <user_email> <task_description> [cwd]}"
WORK_DIR="${4:-$HOME}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$REPO_DIR/.venv"

# Activate venv
if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

# Step 1: Create session + dedicated group chat (synchronous — fast)
RESULT=$(PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}" python3 -c "
import sys, json, time, secrets

task_desc = sys.argv[1]
user_email = sys.argv[2]
manager_chat_id = sys.argv[3]
work_dir = sys.argv[4]

# Generate session ID
sid = time.strftime('%m%d') + '-' + secrets.token_hex(4).upper()

# Create dedicated Teams group chat
from niuma.teams_api import create_session_chat, send_chat_message_sync

chat_info = create_session_chat(
    session_id=sid,
    topic=f'🤖 jbot [{sid}] {task_desc[:40]}',
    user_email=user_email,
)
session_chat_id = chat_info['chat_id']

# Register session in DB
import sqlite3, pathlib
db_path = pathlib.Path.home() / '.jbot' / 'jbot.db'
now = time.time()
conn = sqlite3.connect(str(db_path))
conn.execute(
    '''INSERT INTO sessions (id, chat_id, created_by, status, prompt, cwd, model, session_chat_id, created_at, updated_at)
       VALUES (?, ?, ?, 'running', ?, ?, 'opus', ?, ?, ?)''',
    (sid, manager_chat_id, user_email, task_desc, work_dir, session_chat_id, now, now),
)
conn.commit()
conn.close()

# Send welcome message to the dedicated chat
send_chat_message_sync(
    chat_id=session_chat_id,
    html_body=(
        f'<p><b>【🤖J-Bot】</b> Worker session <code>{sid}</code> started</p>'
        f'<p><b>Task:</b> {task_desc[:200]}</p>'
        f'<p><b>CWD:</b> <code>{work_dir}</code></p>'
        f'<p>Progress updates will appear here.</p>'
        f'<hr/><p><em>🤖 Sent by J-Bot</em></p>'
    ),
)

print(json.dumps({
    'session_id': sid,
    'session_chat_id': session_chat_id,
    'web_url': chat_info.get('web_url', ''),
}))
" "$TASK_DESC" "$USER_EMAIL" "$MANAGER_CHAT_ID" "$WORK_DIR" 2>/dev/null)

SESSION_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
SESSION_CHAT_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_chat_id'])")

# Step 2: Launch worker in BACKGROUND (returns immediately to Manager)
nohup bash -c '
REPO_DIR="'"$REPO_DIR"'"
VENV="'"$VENV"'"
SESSION_ID="'"$SESSION_ID"'"
SESSION_CHAT_ID="'"$SESSION_CHAT_ID"'"
MANAGER_CHAT_ID="'"$MANAGER_CHAT_ID"'"
TASK_DESC="'"$(echo "$TASK_DESC" | sed "s/'/'\\\\''/g")"'"
USER_EMAIL="'"$USER_EMAIL"'"
WORK_DIR="'"$WORK_DIR"'"

source "$VENV/bin/activate"
export PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}"

WORKER_PROMPT="You are a J-Bot worker session [$SESSION_ID].
Execute the task thoroughly. Report progress to your dedicated Teams chat.

## Progress Reporting
Send progress updates to your Teams chat:
bash $REPO_DIR/scripts/jbot-send.sh \"$SESSION_CHAT_ID\" \"<p><b>【🤖J-Bot】</b> your update</p><hr/><p><em>🤖 Sent by J-Bot</em></p>\"

- Send an update when starting major steps
- Send intermediate findings
- Send the FINAL result when done
NEVER use teams-cli — it is NOT available. Always use jbot-send.sh."

if command -v clp >/dev/null 2>&1; then
    CLAUDE_CMD="clp run -- claude"
else
    CLAUDE_CMD="claude"
fi

WORKER_OUTPUT=$($CLAUDE_CMD -p "$TASK_DESC" \
    --model opus \
    --output-format json \
    --permission-mode bypassPermissions \
    --name "jbot-${USER_EMAIL%%@*}-${SESSION_ID}" \
    --append-system-prompt "$WORKER_PROMPT" \
    --add-dir "$WORK_DIR" \
    2>/dev/null) || true

# Extract result
WORKER_RESULT=$(echo "$WORKER_OUTPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get(\"result\", \"\")[:2000])
except:
    print(\"Worker completed\")
" 2>/dev/null || echo "Worker completed")

# Update DB
python3 -c "
import sys, sqlite3, time, pathlib
sid, result = sys.argv[1], sys.argv[2]
db = sqlite3.connect(str(pathlib.Path.home() / \".jbot\" / \"jbot.db\"))
db.execute(\"UPDATE sessions SET status=?, last_output=?, updated_at=? WHERE id=?\",
    (\"completed\", result, time.time(), sid))
db.commit()
" "$SESSION_ID" "$WORKER_RESULT" 2>/dev/null

# Send completion to dedicated chat
bash "$REPO_DIR/scripts/jbot-send.sh" "$SESSION_CHAT_ID" \
    "<p><b>【🤖J-Bot】</b> ✅ Session <code>$SESSION_ID</code> completed</p><hr/><p><em>🤖 Sent by J-Bot</em></p>" \
    2>/dev/null || true

# Send completion to manager chat
bash "$REPO_DIR/scripts/jbot-send.sh" "$MANAGER_CHAT_ID" \
    "<p><b>【🤖J-Bot】</b> ✅ Worker <code>$SESSION_ID</code> finished.<br/>Result: ${WORKER_RESULT:0:300}</p><hr/><p><em>🤖 Sent by J-Bot</em></p>" \
    2>/dev/null || true

' >> ~/.jbot/worker-${SESSION_ID}.log 2>&1 &

# Return immediately with session info
echo "Worker $SESSION_ID launched in background"
echo "Dedicated chat: $SESSION_CHAT_ID"
echo "Logs: ~/.jbot/worker-${SESSION_ID}.log"
