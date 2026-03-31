#!/bin/bash
# jbot-send.sh — Send a Teams message via Graph API (no teams-cli write auth needed)
# Usage: jbot-send.sh <chat_id> <html_body>
#
# This script uses Python + Graph API with automatic token refresh.
# It replaces "READ_WRITE_MODE=1 teams-cli chat send" everywhere.

set -euo pipefail

CHAT_ID="${1:?Usage: jbot-send.sh <chat_id> <html_body>}"
HTML_BODY="${2:?Usage: jbot-send.sh <chat_id> <html_body>}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$REPO_DIR/.venv"

# Activate venv if available
if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

# Use Graph API directly — auto-append footer, strip insight blocks
PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}" python3 -c "
import sys, re
from niuma.teams_api import send_chat_message_sync

body = sys.argv[2]

# Strip insight blocks (internal annotations, not for users)
body = re.sub(r'\x60?★ Insight[^\x60]*\x60?\s*\n.*?\x60?─+\x60?\s*\n?', '', body, flags=re.DOTALL).strip()

# Auto-append footer if not already present
if 'Sent by J-Bot' not in body:
    body += '<hr/><p><em>🤖 Sent by J-Bot</em></p>'

result = send_chat_message_sync(
    chat_id=sys.argv[1],
    html_body=body,
)
print(f'Sent: {result.get(\"id\", \"?\")[:20]}')
" "$CHAT_ID" "$HTML_BODY"
