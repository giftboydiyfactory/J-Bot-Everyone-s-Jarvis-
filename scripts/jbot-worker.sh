#!/bin/bash
# jbot-worker.sh — Start a worker session with a dedicated Teams group chat
# Usage: jbot-worker.sh <manager_chat_id> <user_email> <task_description> [cwd]
#
# Returns IMMEDIATELY after creating the chat and launching the worker in background.
# The worker reports progress to its own dedicated Teams chat.

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
import sys, json, time, secrets, os

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
    topic=f'J-Bot [{sid}] {task_desc[:40]}',
    user_email=user_email,
)
session_chat_id = chat_info['chat_id']

# Register session in DB
import sqlite3, pathlib
db_path = pathlib.Path.home() / '.jbot' / 'jbot.db'
now = time.time()
conn = sqlite3.connect(str(db_path))
conn.execute('PRAGMA busy_timeout = 10000')
worker_model = os.environ.get('JBOT_WORKER_MODEL', 'opus')
conn.execute(
    '''INSERT INTO sessions (id, chat_id, created_by, status, prompt, cwd, model, session_chat_id, created_at, updated_at)
       VALUES (?, ?, ?, 'running', ?, ?, ?, ?, ?, ?)''',
    (sid, manager_chat_id, user_email, task_desc, work_dir, worker_model, session_chat_id, now, now),
)
conn.commit()
conn.close()

# Send welcome message to the dedicated chat (HTML-escape user input)
import html as _html
safe_desc = _html.escape(task_desc[:200])
safe_cwd = _html.escape(work_dir)
send_chat_message_sync(
    chat_id=session_chat_id,
    html_body=(
        f'<p><b>J-Bot</b> Task <code>{sid}</code> started</p>'
        f'<p><b>Task:</b> {safe_desc}</p>'
        f'<p><b>CWD:</b> <code>{safe_cwd}</code></p>'
        f'<p>Progress updates will appear here.</p>'
        '<hr/><p><em>Sent by J-Bot</em></p>'
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

# Step 2: Write task description to a temp file (avoids quoting hell in nohup)
TASK_FILE=$(mktemp /tmp/jbot-task-XXXXXX.txt)
echo "$TASK_DESC" > "$TASK_FILE"

# Step 3: Launch worker runner in background
# Pass REPORT_CHAT_IDS env var through for multi-chat reporting (Phase 3)
REPORT_CHAT_IDS="${REPORT_CHAT_IDS:-}" \
nohup bash "$SCRIPT_DIR/jbot-worker-run.sh" \
    "$REPO_DIR" "$SESSION_ID" "$SESSION_CHAT_ID" "$MANAGER_CHAT_ID" \
    "$USER_EMAIL" "$WORK_DIR" "$TASK_FILE" \
    >> "$HOME/.jbot/worker-${SESSION_ID}.log" 2>&1 &

# Return immediately with session info
echo "Worker $SESSION_ID launched in background (PID: $!)"
echo "Dedicated chat: $SESSION_CHAT_ID"
echo "Logs: ~/.jbot/worker-${SESSION_ID}.log"
