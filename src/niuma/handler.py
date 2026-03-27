# src/niuma/handler.py
"""Message handling and dispatch routing for J-Bot.

Simplified: the Manager now replies directly to Teams via tools.
The handler just forwards messages and handles errors.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from niuma.main import NiumaBot

logger = logging.getLogger("niuma.handler")

_MEMBER_PERMISSION_HINT = (
    "This user is a MEMBER (not admin). "
    "You MUST only answer questions directly — do NOT start worker sessions. "
    "Reply with helpful information only."
)

_MEMBER_PERMISSION_DENIED = (
    "You don't have permission to execute tasks. Contact an admin."
)


def get_user_role(
    user_email: str,
    admin_users: list[str],
    allowed_users: list[str],
    owner_email: str = "",
    owner_display_name: str = "",
) -> Literal["admin", "member", "unknown"]:
    """Return the role of a user based on config lists and bot runner identity.

    The bot runner (authenticated teams-cli user) is always admin regardless of
    config lists. Email matching is tried first; display name is used as fallback
    for chats (e.g. 48:notes) where the sender email may not be available.

    Returns:
        "admin"   -- user is bot runner or in admin_users (full access)
        "member"  -- user is in allowed_users only (chat/reply only)
        "unknown" -- user is in neither list (messages should be ignored)
    """
    if owner_email and user_email == owner_email:
        return "admin"
    if owner_display_name and user_email == owner_display_name:
        return "admin"
    if user_email in admin_users:
        return "admin"
    if user_email in allowed_users:
        return "member"
    return "unknown"


async def handle_message(
    bot: "NiumaBot",
    chat_id: str,
    user_email: str,
    prompt: str,
    message_id: str = "",
) -> None:
    """Route a user message through the stateful Manager session.

    The Manager has full tool access and replies directly to Teams.
    This handler just forwards the message and catches errors.
    """
    role = get_user_role(
        user_email,
        admin_users=bot._config.security.admin_users,
        allowed_users=bot._config.security.allowed_users,
        owner_email=getattr(bot, "_owner_email", ""),
        owner_display_name=getattr(bot, "_owner_display_name", ""),
    )

    # For members, append a hint so the Manager self-restricts
    effective_prompt = prompt
    if role == "member":
        effective_prompt = f"{prompt}\n\n[SYSTEM HINT] {_MEMBER_PERMISSION_HINT}"

    # Immediate acknowledgment so user knows we received the message
    await bot._responder.send_text(
        chat_id, "Received — thinking...", reply_to=message_id,
    )

    # Call Manager — it replies directly via jbot-send.sh (Graph API)
    last_error = None
    for attempt in range(2):
        try:
            await bot._manager.process(
                user_message=effective_prompt,
                user_email=user_email,
                chat_id=chat_id,
            )
            return  # Manager replied directly, we are done
        except Exception as exc:
            last_error = exc
            logger.warning("Manager attempt %d failed for %s: %s", attempt + 1, user_email, exc)
            if attempt == 0:
                await asyncio.sleep(3)

    # All attempts failed — send error to user
    logger.exception("Manager failed after retries for %s", user_email, exc_info=last_error)
    await bot._responder.send_text(
        chat_id,
        "Hit a transient error — retried but still failed. "
        "Please send your message again in a moment.",
        reply_to=message_id,
    )
