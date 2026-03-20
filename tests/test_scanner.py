# tests/test_scanner.py
"""Tests for scanner.py utilities."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from niuma.scanner import _decode_project_path, _read_session_meta, scan_all_sessions


# ---------------------------------------------------------------------------
# _decode_project_path
# ---------------------------------------------------------------------------


def test_decode_project_path_root() -> None:
    # "-" prefix stripped; single part -> "/"
    result = _decode_project_path("-")
    assert result == "/"


def test_decode_project_path_simple(tmp_path: Path) -> None:
    # Create a real directory so the path-existence check succeeds
    sub = tmp_path / "myproject"
    sub.mkdir()
    # Encode: /tmp/... -> -tmp-...
    # We pass the encoded dir name that corresponds to sub
    encoded = str(sub).lstrip("/").replace("/", "-")
    result = _decode_project_path("-" + encoded)
    # Should resolve back to the real path (or a close approximation)
    assert "myproject" in result


def test_decode_project_path_nonexistent() -> None:
    # Non-existent path: falls back gracefully, does not raise
    encoded = "-nonexistent-path-xyz-abc123"
    result = _decode_project_path(encoded)
    assert isinstance(result, str)
    assert len(result) > 0


def test_decode_project_path_empty_string() -> None:
    result = _decode_project_path("")
    assert result == "/"


# ---------------------------------------------------------------------------
# _read_session_meta
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def test_read_session_meta_empty_file(tmp_path: Path) -> None:
    jsonl = tmp_path / "abc123.jsonl"
    jsonl.write_text("")
    result = _read_session_meta(jsonl)
    assert result is None


def test_read_session_meta_no_user_messages(tmp_path: Path) -> None:
    jsonl = tmp_path / "abc123.jsonl"
    _write_jsonl(jsonl, [
        {"type": "custom-title", "customTitle": "My Session", "timestamp": "2026-03-20T10:00:00Z"},
    ])
    result = _read_session_meta(jsonl)
    assert result is None  # num_user_turns == 0


def test_read_session_meta_basic(tmp_path: Path) -> None:
    jsonl = tmp_path / "testsession.jsonl"
    _write_jsonl(jsonl, [
        {"type": "custom-title", "customTitle": "Test Session", "timestamp": "2026-03-20T10:00:00Z", "cwd": "/home/user"},
        {"type": "user", "message": {"content": "Hello there"}, "timestamp": "2026-03-20T10:00:01Z"},
        {"type": "assistant", "message": {"content": "Hi!"}, "timestamp": "2026-03-20T10:00:02Z"},
        {"type": "user", "message": {"content": "Second message"}, "timestamp": "2026-03-20T10:00:03Z"},
    ])
    result = _read_session_meta(jsonl)
    assert result is not None
    assert result["claude_session"] == "testsession"
    assert result["name"] == "Test Session"
    assert result["first_user_msg"] == "Hello there"
    assert result["last_user_msg"] == "Second message"
    assert result["num_turns"] == 2
    assert result["session_cwd"] == "/home/user"


def test_read_session_meta_list_content(tmp_path: Path) -> None:
    """User messages with list-type content (multi-part) should be concatenated."""
    jsonl = tmp_path / "listsession.jsonl"
    _write_jsonl(jsonl, [
        {"type": "user", "message": {"content": [
            {"type": "text", "text": "Part one"},
            {"type": "text", "text": "Part two"},
        ]}, "timestamp": "2026-03-20T10:00:00Z"},
    ])
    result = _read_session_meta(jsonl)
    assert result is not None
    assert "Part one" in result["first_user_msg"]
    assert "Part two" in result["first_user_msg"]


def test_read_session_meta_handles_bad_lines(tmp_path: Path) -> None:
    """Malformed JSON lines should be silently skipped."""
    jsonl = tmp_path / "badsession.jsonl"
    with open(jsonl, "w") as f:
        f.write("not valid json\n")
        f.write(json.dumps({"type": "user", "message": {"content": "OK"}, "timestamp": "t"}) + "\n")
    result = _read_session_meta(jsonl)
    assert result is not None
    assert result["num_turns"] == 1


# ---------------------------------------------------------------------------
# scan_all_sessions
# ---------------------------------------------------------------------------


def test_scan_all_sessions_no_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("niuma.scanner._CLAUDE_PROJECTS_DIR", Path("/nonexistent/path/xyz"))
    result = scan_all_sessions()
    assert result == []


def test_scan_all_sessions_with_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("niuma.scanner._CLAUDE_PROJECTS_DIR", tmp_path)

    # Create a fake project dir with one session
    proj_dir = tmp_path / "-home-user-myproject"
    proj_dir.mkdir()
    jsonl = proj_dir / "session1.jsonl"
    _write_jsonl(jsonl, [
        {"type": "user", "message": {"content": "Do the thing"}, "timestamp": "2026-03-20T10:00:00Z"},
    ])

    results = scan_all_sessions()
    assert len(results) == 1
    assert results[0]["first_user_msg"] == "Do the thing"
