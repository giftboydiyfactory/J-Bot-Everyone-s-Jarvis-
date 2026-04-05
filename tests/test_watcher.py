"""Tests for niuma.watcher — session JSONL parsing helpers."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from niuma.watcher import _parse_latest_activity, _get_session_progress, _find_progress_by_name


# ---------------------------------------------------------------------------
# _parse_latest_activity
# ---------------------------------------------------------------------------

class TestParseLatestActivity:
    def test_extracts_tool_and_text(self, tmp_path: Path):
        jsonl = tmp_path / "session.jsonl"
        lines = [
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Looking at the code..."},
                {"type": "tool_use", "name": "Read"},
            ]}}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Found the issue in main.py"},
                {"type": "tool_use", "name": "Edit"},
            ]}}),
        ]
        jsonl.write_text("\n".join(lines))

        result = _parse_latest_activity(jsonl)
        assert result is not None
        assert "Edit" in result
        assert "main.py" in result

    def test_handles_empty_file(self, tmp_path: Path):
        jsonl = tmp_path / "empty.jsonl"
        jsonl.write_text("")
        result = _parse_latest_activity(jsonl)
        assert result is None

    def test_handles_invalid_json(self, tmp_path: Path):
        jsonl = tmp_path / "bad.jsonl"
        jsonl.write_text("not json\nalso not json\n")
        result = _parse_latest_activity(jsonl)
        assert result is None

    def test_strips_insight_blocks(self, tmp_path: Path):
        jsonl = tmp_path / "insight.jsonl"
        text = (
            "`★ Insight ─────────────────────────────────────`\n"
            "Some insight content\n"
            "`─────────────────────────────────────────────────`\n"
            "Actual useful text here"
        )
        lines = [
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": text},
            ]}}),
        ]
        jsonl.write_text("\n".join(lines))

        result = _parse_latest_activity(jsonl)
        assert result is not None
        assert "Insight" not in result
        assert "useful text" in result

    def test_extracts_from_last_20_entries(self, tmp_path: Path):
        jsonl = tmp_path / "long.jsonl"
        lines = []
        for i in range(30):
            lines.append(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": f"Message {i}"},
            ]}}))
        jsonl.write_text("\n".join(lines))

        result = _parse_latest_activity(jsonl)
        assert "Message 29" in result


# ---------------------------------------------------------------------------
# _get_session_progress
# ---------------------------------------------------------------------------

class TestGetSessionProgress:
    def test_returns_none_for_empty_session_id(self):
        assert _get_session_progress("") is None

    def test_returns_none_when_projects_dir_missing(self):
        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", Path("/nonexistent/path")):
            assert _get_session_progress("abc123") is None

    def test_finds_session_in_project_dir(self, tmp_path: Path):
        projects = tmp_path / "projects"
        project = projects / "test-project"
        project.mkdir(parents=True)
        jsonl = project / "session-abc.jsonl"
        jsonl.write_text(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Working on tests"},
            {"type": "tool_use", "name": "Bash"},
        ]}}) + "\n")

        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", projects):
            result = _get_session_progress("session-abc")
        assert result is not None
        assert "Bash" in result

    def test_returns_none_when_session_not_found(self, tmp_path: Path):
        projects = tmp_path / "projects"
        project = projects / "test-project"
        project.mkdir(parents=True)

        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", projects):
            assert _get_session_progress("nonexistent") is None


# ---------------------------------------------------------------------------
# _find_progress_by_name
# ---------------------------------------------------------------------------

class TestFindProgressByName:
    def test_returns_none_when_no_projects_dir(self):
        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", Path("/nonexistent")):
            assert _find_progress_by_name("sess-1") is None

    def test_finds_session_by_name_in_jsonl(self, tmp_path: Path):
        projects = tmp_path / "projects"
        project = projects / "test"
        project.mkdir(parents=True)
        jsonl = project / "some-uuid.jsonl"

        lines = [
            json.dumps({"type": "system", "custom-title": "jbot-user-sess-123"}),
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Analyzing the build log"},
                {"type": "tool_use", "name": "Grep"},
            ]}}),
        ]
        jsonl.write_text("\n".join(lines))

        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", projects):
            result = _find_progress_by_name("sess-123")
        assert result is not None
        assert "Grep" in result

    def test_skips_old_files(self, tmp_path: Path):
        projects = tmp_path / "projects"
        project = projects / "test"
        project.mkdir(parents=True)
        jsonl = project / "old.jsonl"
        jsonl.write_text(json.dumps({"type": "system", "custom-title": "jbot-user-sess-old"}) + "\n")
        # Make it old (2 hours ago > 1800s threshold)
        import os
        old_time = time.time() - 7200
        os.utime(jsonl, (old_time, old_time))

        with patch("niuma.watcher._CLAUDE_PROJECTS_DIR", projects):
            assert _find_progress_by_name("sess-old") is None
