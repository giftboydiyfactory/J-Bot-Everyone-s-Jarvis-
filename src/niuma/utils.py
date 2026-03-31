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
