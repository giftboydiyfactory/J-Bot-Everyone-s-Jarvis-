# tests/test_manager.py
"""Tests for Manager and ManagerDecision."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from niuma.manager import Manager, ManagerDecision
from niuma.db import Database


# ---------------------------------------------------------------------------
# ManagerDecision.from_claude_output parsing
# ---------------------------------------------------------------------------


def _raw(structured_output: dict, session_id: str = "sid-abc") -> str:
    return json.dumps({
        "result": "",
        "structured_output": structured_output,
        "session_id": session_id,
        "total_cost_usd": 0.01,
    })


def test_parse_decision_new() -> None:
    raw = _raw({"action": "new", "prompt": "run tests", "cwd": "/repo", "dedicated_chat": True})
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "new"
    assert decision.prompt == "run tests"
    assert decision.cwd == "/repo"
    assert decision.dedicated_chat is True


def test_parse_decision_resume() -> None:
    raw = _raw({"action": "resume", "session_id": "0320-abcd", "prompt": "continue"})
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "resume"
    assert decision.session_id == "0320-abcd"
    assert decision.prompt == "continue"


def test_parse_decision_reply() -> None:
    raw = _raw({"action": "reply", "reply_text": "The answer is 42."})
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "reply"
    assert decision.reply_text == "The answer is 42."


def test_parse_decision_report() -> None:
    raw = _raw({"action": "report", "reply_text": "Worker finished."})
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "report"
    assert decision.reply_text == "Worker finished."


def test_parse_decision_fallback_plain_text() -> None:
    """If structured_output is absent, fall back to result string."""
    raw = json.dumps({
        "result": "Just a plain text answer.",
        "session_id": "sid-xyz",
    })
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "reply"
    assert "plain text" in decision.reply_text


def test_parse_decision_fallback_result_json() -> None:
    """If structured_output is absent, fall back to JSON in result string."""
    inner = {"action": "new", "prompt": "scan files", "cwd": "/home"}
    raw = json.dumps({
        "result": json.dumps(inner),
        "session_id": "sid-xyz",
    })
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "new"
    assert decision.prompt == "scan files"


def test_parse_decision_defaults() -> None:
    """Missing optional fields default to None/False."""
    raw = _raw({"action": "reply"})
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.session_id is None
    assert decision.prompt is None
    assert decision.cwd is None
    assert decision.reply_text is None
    assert decision.dedicated_chat is False


# ---------------------------------------------------------------------------
# Manager state persistence via DB
# ---------------------------------------------------------------------------


@pytest.fixture
async def db(tmp_dir: Path) -> Database:
    database = Database(str(tmp_dir / "test.db"))
    await database.init()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_manager_persists_session_id(db: Database) -> None:
    """Manager should save session_id to DB after a successful decide() call."""
    from niuma.config import ClaudeConfig

    cfg = ClaudeConfig(
        dispatcher_model="sonnet",
        worker_model="sonnet",
        max_concurrent=5,
        session_timeout=86400,
        permission_mode="auto",
        default_cwd="/tmp",
    )
    manager = Manager(cfg, db=db)

    raw_output = _raw({"action": "reply", "reply_text": "Hello"}, session_id="new-manager-sid")
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(raw_output.encode(), b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        decision = await manager.decide(user_message="hi", user_email="user@test.com")

    assert decision.action == "reply"
    assert manager.session_id == "new-manager-sid"

    saved = await db.get_bot_state("manager_session_id")
    assert saved == "new-manager-sid"


@pytest.mark.asyncio
async def test_manager_loads_state_from_db(db: Database) -> None:
    """Manager.load_state() should restore session_id from DB on restart."""
    from niuma.config import ClaudeConfig

    await db.set_bot_state("manager_session_id", "restored-sid-abc")

    cfg = ClaudeConfig(
        dispatcher_model="sonnet",
        worker_model="sonnet",
        max_concurrent=5,
        session_timeout=86400,
        permission_mode="auto",
        default_cwd="/tmp",
    )
    manager = Manager(cfg, db=db)
    assert manager.session_id is None  # not yet loaded

    await manager.load_state()
    assert manager.session_id == "restored-sid-abc"


@pytest.mark.asyncio
async def test_feed_worker_result_catches_errors() -> None:
    """feed_worker_result should return a no-op ManagerDecision instead of raising."""
    from niuma.config import ClaudeConfig

    cfg = ClaudeConfig(
        dispatcher_model="sonnet",
        worker_model="sonnet",
        max_concurrent=5,
        session_timeout=86400,
        permission_mode="auto",
        default_cwd="/tmp",
    )
    manager = Manager(cfg, db=None)

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=RuntimeError("claude crashed"))
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        decision = await manager.feed_worker_result(
            session_id="0320-dead",
            result="output text",
            status="completed",
        )

    # Should not raise; returns a safe default
    assert decision.action == "reply"
    assert decision.reply_text == ""
