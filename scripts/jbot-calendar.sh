#!/bin/bash
# jbot-calendar.sh — Create a calendar event via Graph API (no calendar-cli needed)
# Usage: jbot-calendar.sh <subject> <start_datetime> <end_datetime> [attendee_email] [body_html]
#
# start/end format: "2026-03-30T10:00:00" (Asia/Shanghai timezone)

set -euo pipefail

SUBJECT="${1:?Usage: jbot-calendar.sh <subject> <start> <end> [attendee] [body_html]}"
START="${2:?Usage: jbot-calendar.sh <subject> <start> <end> [attendee] [body_html]}"
END="${3:?Usage: jbot-calendar.sh <subject> <start> <end> [attendee] [body_html]}"
ATTENDEE="${4:-}"
BODY_HTML="${5:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$REPO_DIR/.venv"

if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}" python3 -c "
import sys
from niuma.teams_api import create_calendar_event_sync

attendees = [sys.argv[4]] if len(sys.argv) > 4 and sys.argv[4] else None
body = sys.argv[5] if len(sys.argv) > 5 else ''
result = create_calendar_event_sync(
    subject=sys.argv[1],
    start=sys.argv[2],
    end=sys.argv[3],
    attendees=attendees,
    body_html=body,
)
print(f'Event created: {sys.argv[1]}')
print(f'  Start: {sys.argv[2]}')
print(f'  End:   {sys.argv[3]}')
web_link = result.get('webLink', '')
if web_link:
    print(f'  Link:  {web_link[:80]}')
" "$SUBJECT" "$START" "$END" "$ATTENDEE" "$BODY_HTML"
