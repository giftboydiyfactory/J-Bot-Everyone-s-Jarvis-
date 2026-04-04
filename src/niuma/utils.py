# src/niuma/utils.py
"""Shared utilities for J-Bot."""
from __future__ import annotations

import re

# Regex to strip ★ Insight blocks — internal annotations, not for end users.
# Single source of truth — imported by manager, responder, watcher.
INSIGHT_PATTERN = re.compile(
    r'`?★ Insight[^`]*`?\s*\n.*?`?─+`?\s*\n?',
    re.DOTALL,
)


def strip_insight_blocks(text: str) -> str:
    """Remove ★ Insight blocks from text — these are internal, not user-facing."""
    return INSIGHT_PATTERN.sub('', text).strip()


# ---- Phase 4: Unified bot-message detection ----

# Markers that indicate a message was sent by J-Bot itself (not a human user).
# Checked against both the raw HTML body and the cleaned text body.
_BOT_RAW_MARKERS = ("Sent by J-Bot", "ai-pim-utils", "Sent by niuma")
_BOT_BODY_MARKERS = ("\u3010\U0001f916J-Bot\u3011",)  # 【🤖J-Bot】


def is_bot_message(body_raw: str, body: str) -> bool:
    """Return True if the message was sent by J-Bot (should be skipped).

    This is the single source of truth for bot-message detection.
    All poll loops (session chat, manager chat, etc.) should use this
    instead of duplicating marker checks inline.

    Args:
        body_raw: The raw HTML body of the Teams message.
        body: The cleaned/text body of the Teams message.
    """
    for marker in _BOT_RAW_MARKERS:
        if marker in body_raw:
            return True
    for marker in _BOT_BODY_MARKERS:
        if marker in body:
            return True
    return False
