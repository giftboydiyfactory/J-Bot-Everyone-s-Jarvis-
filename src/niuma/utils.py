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


# ---- Disk monitoring ----

import logging
import os
import shutil
from pathlib import Path

_disk_logger = logging.getLogger("niuma.disk")


def check_home_disk() -> dict[str, object]:
    """Check home directory disk usage. Returns dict with total, used, free, pct.

    Triggers log rotation and JSONL cleanup when usage exceeds 90%.
    """
    home = Path.home()
    usage = shutil.disk_usage(str(home))
    pct = (usage.used / usage.total) * 100
    free_mb = usage.free / (1024 * 1024)

    result = {
        "total_mb": round(usage.total / (1024 * 1024)),
        "used_mb": round(usage.used / (1024 * 1024)),
        "free_mb": round(free_mb),
        "pct": round(pct, 1),
    }

    if pct >= 95:
        _disk_logger.error("CRITICAL: Home disk at %.1f%% (%.0f MB free) — auto-cleaning", pct, free_mb)
        _auto_clean_disk(home)
    elif pct >= 90:
        _disk_logger.warning("Home disk at %.1f%% (%.0f MB free)", pct, free_mb)

    return result


def _auto_clean_disk(home: Path) -> None:
    """Emergency disk cleanup: rotate log and remove old JSONL files."""
    cleaned = 0

    # 1. Rotate J-Bot log if > 1MB
    jbot_log = home / ".jbot" / "jbot.log"
    if jbot_log.exists():
        size = jbot_log.stat().st_size
        if size > 1_000_000:
            try:
                lines = jbot_log.read_text().splitlines()
                jbot_log.write_text("\n".join(lines[-500:]) + "\n")
                cleaned += size - jbot_log.stat().st_size
                _disk_logger.info("Rotated jbot.log: freed %.1f MB", cleaned / (1024 * 1024))
            except Exception as e:
                _disk_logger.warning("Failed to rotate jbot.log: %s", e)

    # 2. Remove JSONL session files older than 2 days
    claude_dir = home / ".claude" / "projects"
    if claude_dir.exists():
        import time
        cutoff = time.time() - (2 * 86400)
        for jsonl in claude_dir.rglob("*.jsonl"):
            try:
                if jsonl.stat().st_mtime < cutoff:
                    size = jsonl.stat().st_size
                    jsonl.unlink()
                    cleaned += size
                    _disk_logger.info("Removed old JSONL: %s (%.1f MB)", jsonl.name, size / (1024 * 1024))
            except Exception:
                pass

    # 3. Truncate audit log
    audit_log = home / ".ai-pim-utils" / "audit.log"
    if audit_log.exists() and audit_log.stat().st_size > 500_000:
        try:
            size = audit_log.stat().st_size
            audit_log.write_text("")
            cleaned += size
            _disk_logger.info("Truncated audit.log: freed %.1f MB", size / (1024 * 1024))
        except Exception:
            pass

    if cleaned > 0:
        _disk_logger.info("Auto-cleanup freed %.1f MB total", cleaned / (1024 * 1024))
