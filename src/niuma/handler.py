# src/niuma/handler.py
"""Message handling and dispatch routing for J-Bot.

Extracted from main.py for better separation of concerns.
NiumaBot delegates all inbound-message logic here.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from niuma.main import NiumaBot
    from niuma.manager import ManagerDecision

logger = logging.getLogger("niuma.handler")

_MEMBER_PERMISSION_HINT = (
    "This user is a MEMBER (not admin). "
    "You MUST only use action 'reply'. "
    "Do NOT use 'new' or 'resume'."
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
        "admin"   — user is bot runner or in admin_users (full access)
        "member"  — user is in allowed_users only (chat/reply only)
        "unknown" — user is in neither list (messages should be ignored)
    """
    # Bot runner is always admin — match by email first, then by display name
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

    The Manager remembers all context and decides: new, resume, reply, or report.
    Admin users get full access; members are restricted to reply-only actions.
    """
    reply_only = bot._is_reply_only(chat_id)
    rt = message_id

    role = get_user_role(
        user_email,
        admin_users=bot._config.security.admin_users,
        allowed_users=bot._config.security.allowed_users,
        owner_email=getattr(bot, "_owner_email", ""),
        owner_display_name=getattr(bot, "_owner_display_name", ""),
    )
    is_admin = role == "admin"

    # For members, append a hint to the prompt so the Manager self-restricts.
    effective_prompt = prompt
    if not is_admin:
        effective_prompt = f"{prompt}\n\n[SYSTEM HINT] {_MEMBER_PERMISSION_HINT}"

    # Immediate acknowledgment so user knows we received the message
    await bot._responder.send_text(
        chat_id, "Received — thinking...", reply_to=rt,
    )

    decision = None
    last_error = None
    for attempt in range(2):
        try:
            decision = await bot._manager.decide(
                user_message=effective_prompt,
                user_email=user_email,
            )
            break
        except Exception as exc:
            last_error = exc
            logger.warning("Manager attempt %d failed for %s: %s", attempt + 1, user_email, exc)
            if attempt == 0:
                await asyncio.sleep(3)  # Brief pause before retry

    if decision is None:
        logger.exception("Manager failed after retries for %s", user_email, exc_info=last_error)
        await bot._responder.send_text(
            chat_id,
            f"⚠️ Hit a transient error — retried but still failed. "
            f"Please send your message again in a moment.",
            reply_to=rt,
        )
        return

    logger.info(
        "Manager: action=%s for user=%s (role=%s)", decision.action, user_email, role
    )

    # Hard enforcement: members must not trigger worker actions regardless of
    # what the Manager decided (safety net in case the hint was ignored).
    if not is_admin and decision.action in ("new", "resume", "stop"):
        logger.warning(
            "Blocking action=%s for member user=%s — overriding to permission-denied reply",
            decision.action,
            user_email,
        )
        await bot._responder.send_text(chat_id, _MEMBER_PERMISSION_DENIED, reply_to=rt)
        return

    # Enforce reply-only mode
    if reply_only and decision.action not in ("reply", "report"):
        await bot._responder.send_text(
            chat_id,
            decision.reply_text or "This chat is in reply-only mode.",
            reply_to=rt,
        )
        return

    if decision.action == "new":
        await handle_new(bot, chat_id, user_email, decision, rt)
    elif decision.action == "resume":
        await handle_resume(bot, chat_id, decision, rt, user_email=user_email)
    elif decision.action in ("reply", "report"):
        reply_text = decision.reply_text or ""
        if reply_text.strip():
            await bot._responder.send_text(chat_id, reply_text, reply_to=rt)
    elif decision.action == "stop":
        await handle_stop(bot, chat_id, decision, rt)


async def handle_new(
    bot: "NiumaBot",
    chat_id: str,
    user_email: str,
    decision: "ManagerDecision",
    reply_to: str = "",
) -> None:
    """Handle action='new': start a fresh worker session."""
    from niuma.teams_api import create_session_chat_async as create_session_chat

    try:
        session = await bot._session_mgr.start_session(
            chat_id=chat_id,
            created_by=user_email,
            prompt=decision.prompt or "",
            cwd=decision.cwd,
            model=decision.model,
            trigger_message_id=reply_to,
        )
        sid = session["id"]
        session_chat_id = None

        # Only create dedicated chat for complex tasks
        if decision.dedicated_chat:
            try:
                prompt_preview = (decision.prompt or "")[:50]
                bot_cfg = bot._config.bot
                chat_info = await create_session_chat(
                    session_id=sid,
                    topic=f"{bot_cfg.emoji} {bot_cfg.name} [{sid}] {prompt_preview}",
                    user_email=user_email,
                )
                session_chat_id = chat_info["chat_id"]
                await bot._db.update_session(sid, session_chat_id=session_chat_id)

                web_url = chat_info["web_url"]
                await bot._responder.send_text(
                    chat_id,
                    f"🚀 session [{sid}] started → [open session chat]({web_url})",
                    reply_to=reply_to,
                )
                await bot._responder.send_processing(session_chat_id, sid)
            except Exception as e:
                logger.warning("Failed to create session chat: %s. Using main chat.", e)
                session_chat_id = None

        if not session_chat_id:
            await bot._responder.send_processing(chat_id, sid, reply_to=reply_to)

        # Watch session — send results to session chat if available, else main chat
        output_chat = session_chat_id or chat_id
        bot._fire_and_track(
            bot._watch_session(output_chat, sid, reply_to="" if session_chat_id else reply_to)
        )
    except Exception as e:
        logger.exception("Failed to start session")
        await bot._responder.send_text(chat_id, f"Failed to start session: {e}", reply_to=reply_to)


async def handle_resume(
    bot: "NiumaBot",
    chat_id: str,
    decision: "ManagerDecision",
    reply_to: str = "",
    user_email: str = "",
) -> None:
    """Handle action='resume': resume an existing worker session."""
    sid = decision.session_id
    if not sid:
        await bot._responder.send_text(chat_id, "No session ID to resume.", reply_to=reply_to)
        return

    session = await bot._db.get_session(sid)

    # Auto-import from Claude history if not in DB
    if not session:
        from niuma.scanner import scan_all_sessions

        all_scanned = scan_all_sessions()
        match = None
        for s in all_scanned:
            if sid in s["claude_session"]:
                match = s
                break
        if match:
            session = await bot._db.import_session(
                claude_session=match["claude_session"],
                chat_id=chat_id,
                created_by=user_email or "unknown",
                prompt=match.get("last_user_msg") or match.get("name") or "imported",
                cwd=match["cwd"],
            )
            logger.info("Auto-imported session %s -> [%s]", sid, session["id"])

    if not session:
        await bot._responder.send_text(
            chat_id, f"Session {sid} not found in DB or Claude history.",
            reply_to=reply_to,
        )
        return

    # Ownership/admin check: only the session owner or admins can resume
    is_owner = session.get("created_by") == user_email
    resume_role = get_user_role(
        user_email,
        admin_users=bot._config.security.admin_users,
        allowed_users=bot._config.security.allowed_users,
        owner_email=getattr(bot, "_owner_email", ""),
        owner_display_name=getattr(bot, "_owner_display_name", ""),
    )
    is_admin = resume_role == "admin"
    if not (is_owner or is_admin):
        await bot._responder.send_text(
            chat_id,
            f"Permission denied: session [{session['id']}] belongs to {session.get('created_by')}.",
            reply_to=reply_to,
        )
        return

    actual_sid = session["id"]
    # Route output to session's dedicated chat if it has one
    session_chat_id = session.get("session_chat_id")

    # Create dedicated chat on resume if requested and not yet created
    if not session_chat_id and decision.dedicated_chat:
        from niuma.teams_api import create_session_chat_async as create_session_chat_resume
        try:
            prompt_preview = (decision.prompt or session.get("prompt") or "")[:50]
            bot_cfg = bot._config.bot
            chat_info = await create_session_chat_resume(
                session_id=actual_sid,
                topic=f"{bot_cfg.emoji} {bot_cfg.name} [{actual_sid}] {prompt_preview}",
                user_email=user_email,
            )
            session_chat_id = chat_info["chat_id"]
            await bot._db.update_session(actual_sid, session_chat_id=session_chat_id)
            web_url = chat_info["web_url"]
            await bot._responder.send_text(
                chat_id,
                f"🔄 session [{actual_sid}] resuming → [open session chat]({web_url})",
                reply_to=reply_to,
            )
        except Exception as e:
            logger.warning("Failed to create session chat on resume: %s", e)

    output_chat = session_chat_id or chat_id
    output_reply_to = "" if session_chat_id else reply_to

    try:
        await bot._session_mgr.resume_session(
            session_id=actual_sid, prompt=decision.prompt or ""
        )
        if session_chat_id:
            await bot._responder.send_text(
                chat_id, f"🔄 session [{actual_sid}] resuming → results in session chat",
                reply_to=reply_to,
            )
        await bot._responder.send_processing(output_chat, actual_sid, reply_to=output_reply_to)
        bot._fire_and_track(bot._watch_session(output_chat, actual_sid, output_reply_to))
    except (ValueError, RuntimeError) as e:
        await bot._responder.send_text(chat_id, str(e), reply_to=reply_to)


async def handle_stop(
    bot: "NiumaBot",
    chat_id: str,
    decision: "ManagerDecision",
    reply_to: str = "",
) -> None:
    """Handle action='stop': kill a running worker session."""
    sid = decision.session_id
    if not sid:
        await bot._responder.send_text(chat_id, "No session ID to stop.", reply_to=reply_to)
        return

    # Find the session - try exact match first, then prefix match
    session = await bot._db.get_session(sid)
    if not session:
        # Try prefix match
        all_sessions = await bot._db.list_sessions(status="running")
        matches = [s for s in all_sessions if sid in s["id"]]
        if len(matches) == 1:
            session = matches[0]
            sid = session["id"]

    if not session:
        await bot._responder.send_text(chat_id, f"Session {sid} not found.", reply_to=reply_to)
        return

    await bot._session_mgr.stop_session(sid)
    await bot._responder.send_text(
        chat_id, f"\U0001f6d1 session [{sid}] stopped.", reply_to=reply_to,
    )
