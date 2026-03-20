from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from niuma.config import NiumaConfig, load_config, ConfigError
from niuma.db import Database
from niuma.manager import Manager, ManagerDecision
from niuma.poller import Poller
from niuma.teams_api import create_session_chat_async as create_session_chat
from niuma.responder import Responder
from niuma.session import SessionManager

logger = logging.getLogger("niuma")

_DEFAULT_CONFIG = Path.home() / ".niuma" / "config.yaml"


class NiumaBot:
    def __init__(self, config: NiumaConfig) -> None:
        self._config = config
        self._db: Optional[Database] = None
        self._poller: Optional[Poller] = None
        self._manager: Optional[Manager] = None
        self._session_mgr: Optional[SessionManager] = None
        self._responder: Optional[Responder] = None
        self._running = False
        self._backoff_seconds: dict[str, int] = {}
        self._background_tasks: set[asyncio.Task] = set()

    def _fire_and_track(self, coro: "asyncio.Coroutine") -> asyncio.Task:
        """Schedule a coroutine as a background task, keeping a strong reference."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    async def init(self) -> None:
        self._db = Database(self._config.storage.db_path)
        await self._db.init()
        self._poller = Poller(self._config.teams)
        self._manager = Manager(self._config.claude)
        self._session_mgr = SessionManager(self._config.claude, self._db)
        self._responder = Responder()
        self._manager_chat_id: Optional[str] = None

    async def _ensure_manager_chat(self) -> str:
        """Create or retrieve the Manager's dedicated chat group."""
        if self._manager_chat_id:
            return self._manager_chat_id

        import socket
        hostname = socket.gethostname()
        # Shorten: pdx-container-xterm-081.prd.it.nvidia.com -> pdx-xterm-081
        short_host = hostname.split(".")[0]
        for prefix in ("pdx-container-", "sjc-container-"):
            short_host = short_host.replace(prefix, "pdx-" if "pdx" in prefix else "sjc-")

        try:
            chat_info = await create_session_chat(
                session_id="mgr",
                topic=f"{short_host} manager",
                user_email=self._config.security.admin_users[0] if self._config.security.admin_users else "unknown",
            )
            self._manager_chat_id = chat_info["chat_id"]
            logger.info("Manager chat created: %s (%s)", chat_info["topic"], self._manager_chat_id[:30])

            # Send welcome message
            await self._responder.send_text(
                self._manager_chat_id,
                f"**niuma Manager** started on `{hostname}`\n\n"
                f"This is the Manager's communication channel. "
                f"All user interactions and worker reports come through here."
            )
        except Exception as e:
            logger.warning("Failed to create manager chat: %s", e)
            return ""

        return self._manager_chat_id

    async def shutdown(self) -> None:
        self._running = False
        if self._db:
            await self._db.close()

    async def run(self) -> None:
        """Main polling loop."""
        self._running = True
        logger.info(
            "niuma-bot started, polling every %ds",
            self._config.teams.poll_interval,
        )

        # Create manager's dedicated chat on startup
        await self._ensure_manager_chat()

        while self._running:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Error in poll cycle")
            await asyncio.sleep(self._config.teams.poll_interval)

    async def poll_once(self) -> None:
        """Single poll cycle across all configured chats + manager chat + session chats."""
        # Poll configured trigger chats (@niuma required)
        for chat_id in self._config.teams.chat_ids:
            await self._poll_chat(chat_id)

        # Poll manager chat (no @niuma needed, direct conversation)
        if self._manager_chat_id:
            await self._poll_manager_chat(self._manager_chat_id)

        # Poll session-dedicated chats
        if self._config.teams.auto_session_chats:
            session_chat_ids = await self._db.list_session_chat_ids()
            for chat_id in session_chat_ids:
                await self._poll_session_chat(chat_id)

    async def _poll_chat(self, chat_id: str) -> None:
        from niuma.poller import TeamsCliError

        try:
            raw = await self._poller.poll_chat(chat_id)
            self._backoff_seconds[chat_id] = 0  # reset on success
        except TeamsCliError as e:
            if e.exit_code == 5:  # rate limited
                logger.warning("Rate limited on %s, backing off", chat_id)
                await asyncio.sleep(min(self._backoff_seconds.get(chat_id, 0) or 30, 300))
                return
            elif e.exit_code == 7:  # network error
                self._backoff_seconds[chat_id] = min(
                    (self._backoff_seconds.get(chat_id, 0) or 1) * 2, 300
                )
                logger.warning("Network error on %s, backoff %ds", chat_id, self._backoff_seconds[chat_id])
                await asyncio.sleep(self._backoff_seconds[chat_id])
                return
            elif e.exit_code == 2:  # auth expired
                logger.error("Auth expired for teams-cli, skipping cycle")
                return
            else:
                logger.error("Poll failed for %s: %s", chat_id, e)
                return
        except RuntimeError as e:
            logger.error("Poll failed for %s: %s", chat_id, e)
            return

        messages = self._poller.parse_messages(raw)
        if not messages:
            return

        last_seen = await self._db.get_poll_state(chat_id)
        triggered = self._poller.filter_triggered(messages)
        new_messages = self._poller.filter_new(triggered, last_seen)

        # Find the newest message ID (messages may be newest-first from API)
        try:
            newest_id = max(messages, key=lambda m: int(m.id)).id
        except ValueError:
            newest_id = messages[0].id

        if not new_messages:
            await self._db.set_poll_state(chat_id, newest_id)
            return

        for msg in new_messages:
            if not self._is_allowed(msg.sender_email):
                logger.info(
                    "Ignoring message from unauthorized user: %s",
                    msg.sender_email,
                )
                continue

            prompt = self._poller.extract_prompt(msg)
            if not prompt:
                continue

            await self._handle_message(chat_id, msg.sender_email, prompt, msg.id)

        await self._db.set_poll_state(chat_id, newest_id)

    async def _poll_session_chat(self, chat_id: str) -> None:
        """Poll a session-dedicated chat. All messages auto-route to the bound session."""
        from niuma.poller import TeamsCliError

        try:
            raw = await self._poller.poll_chat(chat_id)
        except (TeamsCliError, RuntimeError):
            return

        messages = self._poller.parse_messages(raw)
        if not messages:
            return

        last_seen = await self._db.get_poll_state(chat_id)

        try:
            newest_id = max(messages, key=lambda m: int(m.id)).id
        except ValueError:
            newest_id = messages[0].id

        # Filter new messages (no trigger needed in session chats)
        new_messages = self._poller.filter_new(messages, last_seen)
        if not new_messages:
            await self._db.set_poll_state(chat_id, newest_id)
            return

        # Find the bound session
        session = await self._db.get_session_by_chat_id(chat_id)
        if not session:
            await self._db.set_poll_state(chat_id, newest_id)
            return

        for msg in new_messages:
            if not self._is_allowed(msg.sender_email):
                continue

            # Skip bot's own messages (contain the signature)
            if "Sent via Claude Code" in msg.body:
                continue

            prompt = msg.body.strip()
            if not prompt:
                continue

            # Auto-resume the bound session
            sid = session["id"]
            logger.info("Session chat %s: routing to session [%s]", chat_id[:20], sid)

            try:
                await self._session_mgr.resume_session(
                    session_id=sid, prompt=prompt,
                )
                await self._responder.send_processing(chat_id, sid)
                self._fire_and_track(self._watch_session(chat_id, sid))
            except (ValueError, RuntimeError) as e:
                await self._responder.send_text(chat_id, str(e))

        await self._db.set_poll_state(chat_id, newest_id)

    async def _poll_manager_chat(self, chat_id: str) -> None:
        """Poll the Manager's dedicated chat. Messages here go directly to Manager."""
        from niuma.poller import TeamsCliError

        try:
            raw = await self._poller.poll_chat(chat_id)
        except (TeamsCliError, RuntimeError):
            return

        messages = self._poller.parse_messages(raw)
        if not messages:
            return

        last_seen = await self._db.get_poll_state(chat_id)
        try:
            newest_id = max(messages, key=lambda m: int(m.id)).id
        except ValueError:
            newest_id = messages[0].id

        new_messages = self._poller.filter_new(messages, last_seen)
        if not new_messages:
            await self._db.set_poll_state(chat_id, newest_id)
            return

        for msg in new_messages:
            if not self._is_allowed(msg.sender_email):
                continue
            if "Sent via Claude Code" in msg.body:
                continue
            prompt = msg.body.strip()
            if not prompt:
                continue

            # Route through Manager, responses go to manager chat
            await self._handle_message(chat_id, msg.sender_email, prompt, msg.id)

        await self._db.set_poll_state(chat_id, newest_id)

    def _is_reply_only(self, chat_id: str) -> bool:
        return chat_id in self._config.teams.reply_only_chat_ids

    async def _handle_message(
        self, chat_id: str, user_email: str, prompt: str,
        message_id: str = "",
    ) -> None:
        """Route user message through the stateful Manager session.

        The Manager remembers all context and decides: new, resume, reply, or report.
        """
        reply_only = self._is_reply_only(chat_id)
        rt = message_id

        try:
            decision = await self._manager.decide(
                user_message=prompt,
                user_email=user_email,
            )
        except Exception:
            logger.exception("Manager failed for message from %s", user_email)
            return

        logger.info("Manager: action=%s for user=%s", decision.action, user_email)

        # Enforce reply-only mode
        if reply_only and decision.action not in ("reply", "report"):
            await self._responder.send_text(
                chat_id,
                decision.reply_text or "This chat is in reply-only mode.",
                reply_to=rt,
            )
            return

        if decision.action == "new":
            await self._handle_new(chat_id, user_email, decision, rt)
        elif decision.action == "resume":
            await self._handle_resume(chat_id, decision, rt, user_email=user_email)
        elif decision.action in ("reply", "report"):
            await self._responder.send_text(chat_id, decision.reply_text or "", reply_to=rt)

    async def _handle_new(
        self, chat_id: str, user_email: str, decision: ManagerDecision,
        reply_to: str = "",
    ) -> None:
        try:
            session = await self._session_mgr.start_session(
                chat_id=chat_id,
                created_by=user_email,
                prompt=decision.prompt or "",
                cwd=decision.cwd,
                model=None,
                trigger_message_id=reply_to,
            )
            sid = session["id"]
            session_chat_id = None

            # Only create dedicated chat for complex tasks
            if decision.dedicated_chat:
                try:
                    prompt_preview = (decision.prompt or "")[:50]
                    chat_info = await create_session_chat(
                        session_id=sid,
                        topic=prompt_preview,
                        user_email=user_email,
                    )
                    session_chat_id = chat_info["chat_id"]
                    await self._db.update_session(sid, session_chat_id=session_chat_id)

                    web_url = chat_info["web_url"]
                    await self._responder.send_text(
                        chat_id,
                        f"🚀 session [{sid}] started → [open session chat]({web_url})",
                        reply_to=reply_to,
                    )
                    await self._responder.send_processing(session_chat_id, sid)
                except Exception as e:
                    logger.warning("Failed to create session chat: %s. Using main chat.", e)
                    session_chat_id = None

            if not session_chat_id:
                await self._responder.send_processing(chat_id, sid, reply_to=reply_to)

            # Watch session — send results to session chat if available, else main chat
            output_chat = session_chat_id or chat_id
            self._fire_and_track(
                self._watch_session(output_chat, sid, reply_to="" if session_chat_id else reply_to)
            )
        except RuntimeError as e:
            await self._responder.send_text(chat_id, str(e), reply_to=reply_to)

    async def _handle_resume(
        self, chat_id: str, decision: ManagerDecision,
        reply_to: str = "", user_email: str = "",
    ) -> None:
        sid = decision.session_id
        if not sid:
            await self._responder.send_text(chat_id, "No session ID to resume.", reply_to=reply_to)
            return

        session = await self._db.get_session(sid)
        if not session:
            await self._responder.send_text(
                chat_id, f"Session {sid} not found.",
                reply_to=reply_to,
            )
            return

        # Ownership/admin check: only the session owner or admins can resume
        is_owner = session.get("created_by") == user_email
        is_admin = user_email in self._config.security.admin_users
        if not (is_owner or is_admin):
            await self._responder.send_text(
                chat_id,
                f"Permission denied: session [{session['id']}] belongs to {session.get('created_by')}.",
                reply_to=reply_to,
            )
            return

        actual_sid = session["id"]
        # Route output to session's dedicated chat if it has one
        session_chat_id = session.get("session_chat_id")
        output_chat = session_chat_id or chat_id
        output_reply_to = "" if session_chat_id else reply_to

        try:
            await self._session_mgr.resume_session(
                session_id=actual_sid, prompt=decision.prompt or ""
            )
            if session_chat_id:
                await self._responder.send_text(
                    chat_id, f"🔄 session [{actual_sid}] resuming → results in session chat",
                    reply_to=reply_to,
                )
            await self._responder.send_processing(output_chat, actual_sid, reply_to=output_reply_to)
            self._fire_and_track(self._watch_session(output_chat, actual_sid, output_reply_to))
        except (ValueError, RuntimeError) as e:
            await self._responder.send_text(chat_id, str(e), reply_to=reply_to)

    async def _watch_session(
        self, chat_id: str, session_id: str, reply_to: str = "",
    ) -> None:
        """Poll DB until session completes, then send result as thread reply."""
        max_wait = self._config.claude.session_timeout + 60
        elapsed = 0
        poll_interval = 2
        while elapsed < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            session = await self._session_mgr.get_result(session_id)
            if not session:
                return
            status = session["status"]
            if status in ("completed", "failed", "timeout"):
                result_text = session.get("last_output", "")
                error_text = None
                if status == "timeout":
                    error_text = "Session timed out (24h)"
                elif status == "failed":
                    error_text = result_text or "Unknown error"
                    result_text = None

                # Send result to Teams
                if error_text:
                    await self._responder.send_result(
                        chat_id, session_id, error=error_text, reply_to=reply_to,
                    )
                else:
                    await self._responder.send_result(
                        chat_id, session_id, result=result_text, reply_to=reply_to,
                    )

                # Feed result back to Manager so it remembers
                try:
                    mgr_decision = await self._manager.feed_worker_result(
                        session_id=session_id,
                        result=result_text or error_text or "",
                        status=status,
                    )
                    # If Manager wants to report something, send it
                    if mgr_decision.action == "report" and mgr_decision.reply_text:
                        await self._responder.send_text(
                            chat_id, mgr_decision.reply_text, reply_to=reply_to,
                        )
                except Exception:
                    logger.debug("Failed to feed worker result to Manager", exc_info=True)

                return

    def _is_allowed(self, email: str) -> bool:
        return (
            email in self._config.security.allowed_users
            or email in self._config.security.admin_users
        )


def _setup_logging(config: NiumaConfig) -> None:
    log_path = Path(config.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.logging.level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_path)),
            logging.StreamHandler(),
        ],
    )


def cli_entry() -> None:
    parser = argparse.ArgumentParser(
        description="niuma-bot: Teams chat bot powered by Claude Code"
    )
    parser.add_argument(
        "-c", "--config",
        default=str(_DEFAULT_CONFIG),
        help=f"Config file path (default: {_DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run in background (nohup-style)",
    )
    args = parser.parse_args()

    try:
        config = load_config(Path(args.config))
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    _setup_logging(config)

    if args.daemon:
        _daemonize()

    bot = NiumaBot(config)

    async def _run() -> None:
        await bot.init()
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(bot.shutdown())
            )
        await bot.run()

    asyncio.run(_run())


def _daemonize() -> None:
    """Simple double-fork daemonization."""
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)
    devnull = open(os.devnull, "r+")
    sys.stdin = devnull
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
