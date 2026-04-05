"""Tests for niuma.utils — shared utilities."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from niuma.utils import (
    strip_insight_blocks,
    is_bot_message,
    check_home_disk,
    _auto_clean_disk,
)


# ---------------------------------------------------------------------------
# strip_insight_blocks
# ---------------------------------------------------------------------------

class TestStripInsightBlocks:
    def test_removes_insight_block(self):
        text = "Hello\n`★ Insight ─────────────────────────────────────`\nSome insight\n`─────────────────────────────────────────────────`\nWorld"
        result = strip_insight_blocks(text)
        assert "Insight" not in result
        assert "Hello" in result
        assert "World" in result

    def test_no_insight_block(self):
        text = "Just normal text"
        assert strip_insight_blocks(text) == "Just normal text"


# ---------------------------------------------------------------------------
# is_bot_message
# ---------------------------------------------------------------------------

class TestIsBotMessage:
    def test_detects_jbot_footer(self):
        assert is_bot_message("Sent by J-Bot", "") is True

    def test_detects_ai_pim_utils(self):
        assert is_bot_message("via ai-pim-utils", "") is True

    def test_detects_jbot_header(self):
        assert is_bot_message("", "【🤖J-Bot】Hello") is True

    def test_human_message(self):
        assert is_bot_message("<p>hello world</p>", "hello world") is False


# ---------------------------------------------------------------------------
# check_home_disk
# ---------------------------------------------------------------------------

class TestCheckHomeDisk:
    def test_returns_usage_dict(self):
        result = check_home_disk()
        assert "total_mb" in result
        assert "used_mb" in result
        assert "free_mb" in result
        assert "pct" in result
        assert 0 <= result["pct"] <= 100

    def test_warns_at_90_percent(self):
        fake_usage = MagicMock()
        fake_usage.total = 5 * 1024 * 1024 * 1024  # 5GB
        fake_usage.used = int(4.6 * 1024 * 1024 * 1024)  # 92%
        fake_usage.free = fake_usage.total - fake_usage.used

        with patch("shutil.disk_usage", return_value=fake_usage), \
             patch("niuma.utils._disk_logger") as mock_logger:
            result = check_home_disk()
            mock_logger.warning.assert_called_once()
            assert result["pct"] > 90

    def test_auto_cleans_at_95_percent(self):
        fake_usage = MagicMock()
        fake_usage.total = 5 * 1024 * 1024 * 1024
        fake_usage.used = int(4.85 * 1024 * 1024 * 1024)  # 97%
        fake_usage.free = fake_usage.total - fake_usage.used

        with patch("shutil.disk_usage", return_value=fake_usage), \
             patch("niuma.utils._auto_clean_disk") as mock_clean, \
             patch("niuma.utils._disk_logger"):
            check_home_disk()
            mock_clean.assert_called_once()


# ---------------------------------------------------------------------------
# _auto_clean_disk
# ---------------------------------------------------------------------------

class TestAutoCleanDisk:
    def test_rotates_large_log(self, tmp_path: Path):
        log_dir = tmp_path / ".jbot"
        log_dir.mkdir()
        log_file = log_dir / "jbot.log"
        # Write >1MB of log
        log_file.write_text("line\n" * 200_001)
        assert log_file.stat().st_size > 1_000_000

        with patch("niuma.utils._disk_logger"):
            _auto_clean_disk(tmp_path)

        # Log should be trimmed to ~500 lines
        lines = log_file.read_text().splitlines()
        assert len(lines) <= 501

    def test_removes_old_jsonl(self, tmp_path: Path):
        claude_dir = tmp_path / ".claude" / "projects" / "test"
        claude_dir.mkdir(parents=True)

        # Create an old JSONL (3 days old)
        old_jsonl = claude_dir / "old-session.jsonl"
        old_jsonl.write_text('{"type": "test"}\n')
        import os
        old_time = time.time() - (3 * 86400)
        os.utime(old_jsonl, (old_time, old_time))

        # Create a recent JSONL (should NOT be deleted)
        new_jsonl = claude_dir / "new-session.jsonl"
        new_jsonl.write_text('{"type": "test"}\n')

        with patch("niuma.utils._disk_logger"):
            _auto_clean_disk(tmp_path)

        assert not old_jsonl.exists(), "Old JSONL should be removed"
        assert new_jsonl.exists(), "Recent JSONL should be kept"

    def test_truncates_audit_log(self, tmp_path: Path):
        audit_dir = tmp_path / ".ai-pim-utils"
        audit_dir.mkdir()
        audit_log = audit_dir / "audit.log"
        audit_log.write_text("x" * 1_000_000)

        with patch("niuma.utils._disk_logger"):
            _auto_clean_disk(tmp_path)

        assert audit_log.stat().st_size == 0

    def test_skips_small_files(self, tmp_path: Path):
        """Should not rotate small logs or truncate small audit logs."""
        log_dir = tmp_path / ".jbot"
        log_dir.mkdir()
        log_file = log_dir / "jbot.log"
        log_file.write_text("small log\n")

        audit_dir = tmp_path / ".ai-pim-utils"
        audit_dir.mkdir()
        audit_log = audit_dir / "audit.log"
        audit_log.write_text("small audit\n")

        with patch("niuma.utils._disk_logger"):
            _auto_clean_disk(tmp_path)

        assert log_file.read_text() == "small log\n"
        assert audit_log.read_text() == "small audit\n"
