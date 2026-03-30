#!/bin/bash
# jbot-email.sh — Send an email via Graph API (no outlook-cli needed)
# Usage: jbot-email.sh <subject> <to_email> <html_body> [cc_email]
#
# Sends immediately. Use jbot-draft.sh if you want a draft instead.

set -euo pipefail

SUBJECT="${1:?Usage: jbot-email.sh <subject> <to_email> <html_body> [cc_email]}"
TO_EMAIL="${2:?Usage: jbot-email.sh <subject> <to_email> <html_body> [cc_email]}"
HTML_BODY="${3:?Usage: jbot-email.sh <subject> <to_email> <html_body> [cc_email]}"
CC_EMAIL="${4:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$REPO_DIR/.venv"

if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}" python3 -c "
import sys
from niuma.teams_api import send_email_sync

cc = [sys.argv[4]] if len(sys.argv) > 4 and sys.argv[4] else None
send_email_sync(
    subject=sys.argv[1],
    to=[sys.argv[2]],
    html_body=sys.argv[3],
    cc=cc,
)
print(f'Email sent: {sys.argv[1]} → {sys.argv[2]}')
" "$SUBJECT" "$TO_EMAIL" "$HTML_BODY" "$CC_EMAIL"
