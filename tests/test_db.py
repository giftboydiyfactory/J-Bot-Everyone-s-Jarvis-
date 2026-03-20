from __future__ import annotations

import pytest
from pathlib import Path

from niuma.db import Database


@pytest.fixture
async def db(tmp_dir: Path) -> Database:
    database = Database(str(tmp_dir / "test.db"))
    await database.init()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_init_creates_tables(db: Database) -> None:
    tables = await db.list_tables()
    assert "sessions" in tables
    assert "messages" in tables
    assert "poll_state" in tables


@pytest.mark.asyncio
async def test_create_and_get_session(db: Database) -> None:
    session = await db.create_session(
        chat_id="chat-1",
        created_by="user@nvidia.com",
        prompt="test prompt",
        cwd="/tmp",
        model="sonnet",
    )
    assert len(session["id"]) == 9  # format: MMDD-XXXX (e.g. "0320-a7f3")
    assert session["status"] == "pending"

    fetched = await db.get_session(session["id"])
    assert fetched is not None
    assert fetched["prompt"] == "test prompt"


@pytest.mark.asyncio
async def test_update_session_status(db: Database) -> None:
    session = await db.create_session(
        chat_id="chat-1",
        created_by="user@nvidia.com",
        prompt="test",
        cwd="/tmp",
        model="sonnet",
    )
    await db.update_session(session["id"], status="running", claude_session="uuid-123")
    updated = await db.get_session(session["id"])
    assert updated["status"] == "running"
    assert updated["claude_session"] == "uuid-123"


@pytest.mark.asyncio
async def test_list_sessions_by_status(db: Database) -> None:
    await db.create_session(chat_id="c", created_by="u", prompt="p1", cwd="/", model="s")
    s2 = await db.create_session(chat_id="c", created_by="u", prompt="p2", cwd="/", model="s")
    await db.update_session(s2["id"], status="running")

    running = await db.list_sessions(status="running")
    assert len(running) == 1
    assert running[0]["prompt"] == "p2"


@pytest.mark.asyncio
async def test_poll_state(db: Database) -> None:
    await db.set_poll_state("chat-1", "msg-100")
    state = await db.get_poll_state("chat-1")
    assert state == "msg-100"

    await db.set_poll_state("chat-1", "msg-200")
    state = await db.get_poll_state("chat-1")
    assert state == "msg-200"


@pytest.mark.asyncio
async def test_add_and_get_messages(db: Database) -> None:
    session = await db.create_session(
        chat_id="c", created_by="u", prompt="p", cwd="/", model="s"
    )
    await db.add_message(session["id"], "user", "hello")
    await db.add_message(session["id"], "assistant", "hi there")

    msgs = await db.get_messages(session["id"])
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_bot_state(db: Database) -> None:
    # Initially absent
    val = await db.get_bot_state("manager_session_id")
    assert val is None

    # Set and retrieve
    await db.set_bot_state("manager_session_id", "sid-abc123")
    val = await db.get_bot_state("manager_session_id")
    assert val == "sid-abc123"

    # Overwrite
    await db.set_bot_state("manager_session_id", "sid-newvalue")
    val = await db.get_bot_state("manager_session_id")
    assert val == "sid-newvalue"


@pytest.mark.asyncio
async def test_get_total_cost_usd(db: Database) -> None:
    # No sessions: total is 0
    total = await db.get_total_cost_usd()
    assert total == 0.0

    # Add sessions with cost
    s1 = await db.create_session(chat_id="c", created_by="u", prompt="p1", cwd="/", model="s")
    s2 = await db.create_session(chat_id="c", created_by="u", prompt="p2", cwd="/", model="s")
    await db.update_session(s1["id"], cost_usd=0.10)
    await db.update_session(s2["id"], cost_usd=0.05)

    total = await db.get_total_cost_usd()
    assert abs(total - 0.15) < 1e-9


@pytest.mark.asyncio
async def test_init_creates_bot_state_table(db: Database) -> None:
    tables = await db.list_tables()
    assert "bot_state" in tables


@pytest.mark.asyncio
async def test_init_creates_watched_chats_table(db: Database) -> None:
    tables = await db.list_tables()
    assert "watched_chats" in tables


@pytest.mark.asyncio
async def test_add_and_list_watched_chats(db: Database) -> None:
    chats = await db.list_watched_chats()
    assert chats == []

    await db.add_watched_chat("chat-1", added_by="admin@nvidia.com", mode="full")
    await db.add_watched_chat("chat-2", added_by="admin@nvidia.com", mode="reply_only")

    chats = await db.list_watched_chats()
    assert len(chats) == 2
    chat_ids = {c["chat_id"] for c in chats}
    assert "chat-1" in chat_ids
    assert "chat-2" in chat_ids

    modes = {c["chat_id"]: c["mode"] for c in chats}
    assert modes["chat-1"] == "full"
    assert modes["chat-2"] == "reply_only"


@pytest.mark.asyncio
async def test_remove_watched_chat(db: Database) -> None:
    await db.add_watched_chat("chat-1", added_by="admin@nvidia.com")
    await db.add_watched_chat("chat-2", added_by="admin@nvidia.com")

    await db.remove_watched_chat("chat-1")
    chats = await db.list_watched_chats()
    assert len(chats) == 1
    assert chats[0]["chat_id"] == "chat-2"


@pytest.mark.asyncio
async def test_add_watched_chat_updates_mode(db: Database) -> None:
    """Re-adding an existing chat updates its mode."""
    await db.add_watched_chat("chat-1", added_by="admin@nvidia.com", mode="full")
    await db.add_watched_chat("chat-1", added_by="admin2@nvidia.com", mode="reply_only")

    chats = await db.list_watched_chats()
    assert len(chats) == 1
    assert chats[0]["mode"] == "reply_only"
    assert chats[0]["added_by"] == "admin2@nvidia.com"
