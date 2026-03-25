# tests/test_handler.py
"""Tests for handler.py role-based permissions and message forwarding."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from niuma.handler import get_user_role, handle_message, _MEMBER_PERMISSION_DENIED, _MEMBER_PERMISSION_HINT


# ---------------------------------------------------------------------------
# get_user_role unit tests
# ---------------------------------------------------------------------------

def test_get_user_role_admin() -> None:
    role = get_user_role(
        "admin@example.com",
        admin_users=["admin@example.com"],
        allowed_users=["member@example.com"],
    )
    assert role == "admin"


def test_get_user_role_member() -> None:
    role = get_user_role(
        "member@example.com",
        admin_users=["admin@example.com"],
        allowed_users=["member@example.com"],
    )
    assert role == "member"


def test_get_user_role_unknown() -> None:
    role = get_user_role(
        "stranger@example.com",
        admin_users=["admin@example.com"],
        allowed_users=["member@example.com"],
    )
    assert role == "unknown"


def test_get_user_role_admin_takes_precedence_over_allowed() -> None:
    """If a user is in both lists, admin wins."""
    role = get_user_role(
        "both@example.com",
        admin_users=["both@example.com"],
        allowed_users=["both@example.com"],
    )
    assert role == "admin"


def test_get_user_role_empty_lists() -> None:
    role = get_user_role(
        "anyone@example.com",
        admin_users=[],
        allowed_users=[],
    )
    assert role == "unknown"


# ---------------------------------------------------------------------------
# handle_message integration tests (mocked bot)
# ---------------------------------------------------------------------------


def _make_bot(
    admin_users: list[str],
    allowed_users: list[str],
) -> MagicMock:
    """Create a minimal mock NiumaBot for handle_message tests."""
    bot = MagicMock()

    # Config
    bot._config.security.admin_users = admin_users
    bot._config.security.allowed_users = allowed_users

    # Manager
    bot._manager.process = AsyncMock()

    # Responder
    bot._responder.send_text = AsyncMock()

    return bot


@pytest.mark.asyncio
async def test_admin_calls_manager_process() -> None:
    """Admin users should have their message forwarded to manager.process()."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=[],
    )

    await handle_message(bot, "chat-1", "admin@example.com", "run tests", "msg-1")

    # Manager.process should have been called
    bot._manager.process.assert_called_once()
    call_kwargs = bot._manager.process.call_args.kwargs
    assert call_kwargs["user_email"] == "admin@example.com"
    assert call_kwargs["chat_id"] == "chat-1"
    # Admin prompt should NOT contain the member hint
    assert _MEMBER_PERMISSION_HINT not in call_kwargs["user_message"]


@pytest.mark.asyncio
async def test_member_hint_appended_to_prompt() -> None:
    """For members, the system hint must be appended to the prompt sent to Manager."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=["member@example.com"],
    )

    await handle_message(bot, "chat-1", "member@example.com", "can you help?", "msg-5")

    call_kwargs = bot._manager.process.call_args.kwargs
    assert "can you help?" in call_kwargs["user_message"]
    assert _MEMBER_PERMISSION_HINT in call_kwargs["user_message"]


@pytest.mark.asyncio
async def test_admin_hint_not_appended_to_prompt() -> None:
    """For admins, the system hint must NOT be added to the prompt."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=[],
    )

    await handle_message(bot, "chat-1", "admin@example.com", "do something", "msg-6")

    call_kwargs = bot._manager.process.call_args.kwargs
    assert _MEMBER_PERMISSION_HINT not in call_kwargs["user_message"]


@pytest.mark.asyncio
async def test_acknowledgment_sent_before_process() -> None:
    """Handler should send an acknowledgment message before calling manager.process()."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=[],
    )

    await handle_message(bot, "chat-1", "admin@example.com", "hello", "msg-7")

    # First call to send_text should be the acknowledgment
    first_call = bot._responder.send_text.call_args_list[0]
    assert first_call.args[0] == "chat-1"
    assert "thinking" in first_call.args[1].lower() or "received" in first_call.args[1].lower()


@pytest.mark.asyncio
async def test_manager_failure_sends_error_message() -> None:
    """If Manager.process raises, handle_message should send an error to the user."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=[],
    )
    bot._manager.process = AsyncMock(side_effect=RuntimeError("claude crashed"))

    await handle_message(bot, "chat-1", "admin@example.com", "hello", "msg-8")

    # Should have sent acknowledgment + error message
    assert bot._responder.send_text.call_count >= 2
    last_call = bot._responder.send_text.call_args_list[-1]
    assert "error" in last_call.args[1].lower() or "failed" in last_call.args[1].lower()


@pytest.mark.asyncio
async def test_member_message_forwarded_to_manager() -> None:
    """Members should also have their message forwarded to manager.process()."""
    bot = _make_bot(
        admin_users=["admin@example.com"],
        allowed_users=["member@example.com"],
    )

    await handle_message(bot, "chat-1", "member@example.com", "hello", "msg-9")

    bot._manager.process.assert_called_once()
    call_kwargs = bot._manager.process.call_args.kwargs
    assert call_kwargs["user_email"] == "member@example.com"
