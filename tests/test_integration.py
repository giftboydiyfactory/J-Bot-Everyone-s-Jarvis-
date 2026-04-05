from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from niuma.config import load_config
from niuma.main import NiumaBot


@pytest.fixture
async def bot(config_file: Path) -> NiumaBot:
    config = load_config(config_file)
    # Mock Graph API calls during init (_detect_owner, manager.load_state)
    with patch("niuma.main.asyncio.to_thread", return_value={"mail": "testbot@nvidia.com", "displayName": "TestBot"}):
        bot = NiumaBot(config)
        await bot.init()
    yield bot
    await bot.shutdown()


@pytest.mark.asyncio
async def test_full_flow_new_session(bot: NiumaBot) -> None:
    """User sends @jbot message -> Manager.process() is called with correct args."""
    graph_messages = [
        {
            "id": "1742385601000",
            "from": {"user": {"displayName": "Jack", "email": "testuser@nvidia.com"}},
            "body": {"content": "@jbot analyze this repo"},
            "createdDateTime": "2026-03-19T10:00:00Z",
        }
    ]

    # Pre-seed the poll state so the bot treats the message as new.
    chat_id = bot._config.teams.chat_ids[0]
    await bot._db.set_poll_state(chat_id, "1742385600000")

    # Mock Graph API polling, Manager.process(), and Responder.send()
    with patch(
        "niuma.poller._graph_get_messages_sync", return_value=graph_messages
    ) as poll_mock, patch.object(
        bot._manager, "process", new_callable=AsyncMock
    ) as manager_mock, patch.object(
        bot._responder, "send", new_callable=AsyncMock
    ) as send_mock:
        await bot.poll_once()
        # Allow fire-and-forget tasks to complete
        await asyncio.sleep(0.3)

    # Verify Graph API was polled
    poll_mock.assert_called()

    # Verify acknowledgment was sent
    assert send_mock.call_count >= 1

    # Verify Manager.process() was called with the user's message
    assert manager_mock.call_count >= 1
    call_kwargs = manager_mock.call_args
    assert "analyze this repo" in call_kwargs.kwargs.get("user_message", "")
    assert call_kwargs.kwargs.get("user_email") == "testuser@nvidia.com"
    assert call_kwargs.kwargs.get("chat_id") == chat_id
