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


def _raw(result: str = "", session_id: str = "sid-abc") -> str:
    return json.dumps({
        "result": result,
        "session_id": session_id,
        "total_cost_usd": 0.01,
    })


def test_parse_decision_reply() -> None:
    raw = _raw(result="The answer is 42.")
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "reply"
    assert decision.reply_text == "The answer is 42."


def test_parse_decision_empty_result() -> None:
    raw = _raw(result="")
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "reply"
    assert decision.reply_text == ""


def test_parse_decision_fallback_invalid_json() -> None:
    """If input is not valid JSON, return safe default."""
    decision = ManagerDecision.from_claude_output("not json at all")
    assert decision.action == "reply"
    assert decision.reply_text == ""


def test_parse_decision_always_returns_reply_action() -> None:
    """from_claude_output always returns action='reply' regardless of content."""
    raw = _raw(result="some text")
    decision = ManagerDecision.from_claude_output(raw)
    assert decision.action == "reply"


def test_manager_decision_fields() -> None:
    """ManagerDecision only has action and reply_text."""
    decision = ManagerDecision(action="reply", reply_text="Hello")
    assert decision.action == "reply"
    assert decision.reply_text == "Hello"


def test_manager_decision_default_reply_text() -> None:
    """reply_text defaults to None."""
    decision = ManagerDecision(action="reply")
    assert decision.reply_text is None


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
    """Manager should save session_id to DB after a successful process() call."""
    from niuma.config import ClaudeConfig

    cfg = ClaudeConfig(
        dispatcher_model="sonnet",
        worker_model="sonnet",
        max_concurrent=5,
        session_timeout=86400,
        permission_mode="auto",
        default_cwd="/tmp",
        persistent_manager=True,
    )
    manager = Manager(cfg, db=db)

    raw_output = json.dumps({
        "result": "Hello",
        "session_id": "new-manager-sid",
        "total_cost_usd": 0.01,
    })
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(raw_output.encode(), b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        await manager.process(
            user_message="hi",
            user_email="user@test.com",
            chat_id="chat-1",
        )

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
        persistent_manager=True,
    )
    manager = Manager(cfg, db=db)
    assert manager.session_id is None  # not yet loaded

    await manager.load_state()
    assert manager.session_id == "restored-sid-abc"


@pytest.mark.asyncio
async def test_feed_worker_result_catches_errors() -> None:
    """feed_worker_result should not raise even if process() fails."""
    from niuma.config import ClaudeConfig

    cfg = ClaudeConfig(
        dispatcher_model="sonnet",
        worker_model="sonnet",
        max_concurrent=5,
        session_timeout=86400,
        permission_mode="auto",
        default_cwd="/tmp",
        persistent_manager=True,
    )
    manager = Manager(cfg, db=None)

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=RuntimeError("claude crashed"))
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        # Should not raise
        await manager.feed_worker_result(
            session_id="0320-dead",
            result="output text",
            status="completed",
            chat_id="chat-1",
        )
