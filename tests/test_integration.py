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
    bot = NiumaBot(config)
    await bot.init()
    yield bot
    await bot.shutdown()


def _teams_read_output(messages: list[dict]) -> bytes:
    return json.dumps({
        "success": True,
        "data": {"messages": messages},
        "metadata": {},
    }).encode()


def _claude_manager_output(action: str, **kwargs) -> bytes:
    inner = {"action": action, **kwargs}
    return json.dumps({
        "result": "",
        "structured_output": inner,
        "session_id": "manager-uuid",
        "total_cost_usd": 0.01,
    }).encode()


def _claude_worker_output(result: str) -> bytes:
    return json.dumps({
        "result": result,
        "session_id": "worker-uuid-123",
        "total_cost_usd": 0.05,
    }).encode()


@pytest.mark.asyncio
async def test_full_flow_new_session(bot: NiumaBot) -> None:
    """User sends @niuma message -> dispatcher routes new -> worker completes -> reply sent."""
    teams_read_mock = AsyncMock()
    teams_read_mock.communicate = AsyncMock(return_value=(
        _teams_read_output([{
            "id": "msg-1",
            "from": {"user": {"displayName": "Jack", "email": "testuser@nvidia.com"}},
            "body": {"content": "@niuma analyze this repo"},
            "createdDateTime": "2026-03-19T10:00:00Z",
        }]),
        b"",
    ))
    teams_read_mock.returncode = 0

    manager_mock = AsyncMock()
    manager_mock.communicate = AsyncMock(return_value=(
        _claude_manager_output("new", prompt="analyze this repo", cwd="/tmp"),
        b"",
    ))
    manager_mock.returncode = 0

    worker_mock = AsyncMock()
    worker_mock.communicate = AsyncMock(return_value=(
        _claude_worker_output("Found 2 performance issues"),
        b"",
    ))
    worker_mock.returncode = 0
    worker_mock.pid = 12345
    worker_mock.kill = MagicMock()

    teams_send_mock = AsyncMock()
    teams_send_mock.communicate = AsyncMock(return_value=(b'{"success":true}', b""))
    teams_send_mock.returncode = 0

    async def mock_subprocess(*args, **kwargs):
        cmd = args[0] if args else ""
        if cmd == "teams-cli":
            if "read" in args:
                return teams_read_mock
            else:
                return teams_send_mock
        elif cmd == "claude":
            if "--json-schema" in args:
                return manager_mock
            else:
                return worker_mock
        return teams_read_mock

    with patch("asyncio.create_subprocess_exec", side_effect=mock_subprocess):
        await bot.poll_once()
        await asyncio.sleep(0.2)

    assert teams_send_mock.communicate.call_count >= 1
