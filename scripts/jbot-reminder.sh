#!/bin/bash
# jbot-reminder.sh — Set a reminder that sends a Teams message at a future time
# Usage: jbot-reminder.sh <chat_id> <delay_minutes> <reminder_message>
#
# Example: jbot-reminder.sh "19:abc@thread.v2" 30 "Check build status"

set -euo pipefail

CHAT_ID="${1:?Usage: jbot-reminder.sh <chat_id> <delay_minutes> <message>}"
DELAY_MIN="${2:?Usage: jbot-reminder.sh <chat_id> <delay_minutes> <message>}"
MESSAGE="${3:?Usage: jbot-reminder.sh <chat_id> <delay_minutes> <message>}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Reminder set: '$MESSAGE' in ${DELAY_MIN} minutes"
sleep $((DELAY_MIN * 60))

bash "$SCRIPT_DIR/jbot-send.sh" "$CHAT_ID" "<p><b>【🤖J-Bot Reminder】</b> $MESSAGE</p>"
echo "Reminder sent!"
