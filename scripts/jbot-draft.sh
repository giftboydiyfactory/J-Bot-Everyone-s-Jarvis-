#!/bin/bash
# jbot-draft.sh — Create an Outlook draft email via Graph API
# Usage: jbot-draft.sh <subject> <to_email> <html_body> [cc_email]
#
# Creates a draft in the user's Drafts folder (NOT sent automatically).
# Uses the same write-capable token as jbot-send.sh.

set -euo pipefail

SUBJECT="${1:?Usage: jbot-draft.sh <subject> <to_email> <html_body> [cc_email]}"
TO_EMAIL="${2:?Usage: jbot-draft.sh <subject> <to_email> <html_body> [cc_email]}"
HTML_BODY="${3:?Usage: jbot-draft.sh <subject> <to_email> <html_body> [cc_email]}"
CC_EMAIL="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$REPO_DIR/.venv"

if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}" python3 -c "
import sys
from niuma.teams_api import create_draft_sync

cc = [sys.argv[4]] if len(sys.argv) > 4 and sys.argv[4] else None
result = create_draft_sync(
    subject=sys.argv[1],
    to=[sys.argv[2]],
    html_body=sys.argv[3],
    cc=cc,
)
print(f'Draft created: {result.get(\"id\", \"?\")[:30]}')
print(f'Subject: {sys.argv[1]}')
" "$SUBJECT" "$TO_EMAIL" "$HTML_BODY" "$CC_EMAIL"
