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
from niuma.manager import Manager
from niuma.poller import Poller
from niuma.teams_api import create_session_chat_async as create_session_chat
from niuma.responder import Responder
from niuma.session import SessionManager

# TODO (multi-manager): Add config option for per-directory managers,
# e.g. config.claude.per_dir_managers: {"/home/user/project": "manager_session_id"}.
# Each dir would get its own persistent Manager session so context is scoped by project.

logger = logging.getLogger("niuma")

_DEFAULT_CONFIG = Path.home() / ".jbot" / "config.yaml"

_BOT_STATE_MANAGER_CHAT = "manager_chat_id"

_GRACEFUL_SHUTDOWN_TIMEOUT = 30  # seconds to wait for running workers on SIGTERM/SIGINT


def _send_alert(title: str, message: str) -> None:
    """Send a system alert via macOS notification + log."""
    logger.critical("ALERT: %s — %s", title, message)
    try:
        import subprocess
        subprocess.Popen([
            "osascript", "-e",
            f'display notification "{message}" with title "🤖 J-Bot Alert" subtitle "{title}" sound name "Basso"'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass  # Non-fatal — alert is also in logs


class NiumaBot:
    def __init__(self, config: NiumaConfig) -> None:
        self._config = config
        self._db: Optional[Database] = None
        self._poller: Optional[Poller] = None
        self._manager: Optional[Manager] = None
        self._session_mgr: Optional[SessionManager] = None
        self._responder: Optional[Responder] = None
        self._running = False
        self._shutting_down = False
        self._config_mtime: float = 0.0
        self._backoff_seconds: dict[str, int] = {}
        self._background_tasks: set[asyncio.Task] = set()
        self._consecutive_failures: int = 0
        self._alert_threshold: int = 5  # Alert after 5 consecutive failures
        self._last_alert_time: float = 0

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
        self._manager = Manager(self._config.claude, db=self._db)
        self._session_mgr = SessionManager(self._config.claude, self._db, bot_name=self._config.bot.name)
        self._responder = Responder(bot_name=self._config.bot.name, bot_emoji=self._config.bot.emoji)
        self._manager_chat_id: Optional[str] = None

        # Auto-detect owner: whoever runs the bot is always admin
        self._owner_email: str = ""
        self._owner_display_name: str = ""
        await self._detect_owner()

        # Optimization 1: Resume Manager session from DB if one was saved
        await self._manager.load_state()

        # Optimization 2: Resume manager chat from DB if one was saved
        saved_chat = await self._db.get_bot_state(_BOT_STATE_MANAGER_CHAT)
        if saved_chat:
            self._manager_chat_id = saved_chat
            logger.info("Resumed Manager chat from DB: %s", saved_chat[:30])

    async def _detect_owner(self) -> None:
        """Detect the authenticated user via Graph API /me (single call).

        Uses Graph API directly — no teams-cli dependency.
        Failures are non-fatal — the bot falls back to config-only admin lists.
        """
        try:
            from niuma.teams_api import _get_me_sync
            me = await asyncio.to_thread(_get_me_sync)
            email = me.get("mail") or me.get("userPrincipalName", "")
            if email:
                self._owner_email = email
                logger.info("Auto-detected owner email from Graph API: %s", email)
            display_name = me.get("displayName", "")
            if display_name:
                self._owner_display_name = display_name
                logger.info("Auto-detected owner displayName from Graph API: %s", display_name)
        except Exception as exc:
            logger.warning("Could not detect owner from Graph API: %s", exc)

    async def _ensure_manager_chat(self) -> str:
        """Create or retrieve the Manager's dedicated chat group.

        Checks DB first (optimization 2) so restarts reuse the same chat.
        """
        if self._manager_chat_id:
            return self._manager_chat_id

        import socket
        hostname = socket.gethostname()
        # Shorten: pdx-container-xterm-081.prd.it.nvidia.com -> pdx-xterm-081
        short_host = hostname.split(".")[0]
        for prefix in ("pdx-container-", "sjc-container-"):
            short_host = short_host.replace(prefix, "pdx-" if "pdx" in prefix else "sjc-")

        bot = self._config.bot
        try:
            chat_info = await create_session_chat(
                session_id="mgr",
                topic=f"{bot.emoji} {bot.name} [mgr] {short_host}",
                user_email=self._config.security.admin_users[0] if self._config.security.admin_users else "unknown",
            )
            self._manager_chat_id = chat_info["chat_id"]
            logger.info("Manager chat created: %s (%s)", chat_info["topic"], self._manager_chat_id[:30])

            # Persist to DB so restarts reuse this chat (optimization 2)
            await self._db.set_bot_state(_BOT_STATE_MANAGER_CHAT, self._manager_chat_id)

            # Send welcome message
            await self._responder.send_text(
                self._manager_chat_id,
                f"**{bot.emoji} {bot.name} Manager** started on `{hostname}`\n\n"
                f"This is the Manager's communication channel. "
                f"All user interactions and worker reports come through here."
            )

            # Add configured users as members of the manager chat
            # Only add entries that look like email addresses (skip displayNames)
            from niuma.teams_api import add_chat_member_async
            for email in self._config.security.admin_users + self._config.security.allowed_users:
                if "@" not in email:
                    continue  # Skip displayNames — not valid for Graph API
                if email == self._owner_email:
                    continue  # Already the creator
                try:
                    await add_chat_member_async(chat_id=self._manager_chat_id, user_email=email)
                    logger.info("Added %s to manager chat", email)
                except Exception as e:
                    logger.warning("Failed to add %s to manager chat: %s", email, e)
        except Exception as e:
            logger.warning("Failed to create manager chat: %s", e)
            return ""

        return self._manager_chat_id

    async def shutdown(self) -> None:
        """Gracefully shut down the bot (optimization 7).

        Waits up to _GRACEFUL_SHUTDOWN_TIMEOUT seconds for running background
        tasks (worker watchers) to finish before forcibly cancelling them.
        """
        if self._shutting_down:
            return
        self._shutting_down = True
        self._running = False
        logger.info("Shutdown requested — waiting up to %ds for %d background tasks",
                    _GRACEFUL_SHUTDOWN_TIMEOUT, len(self._background_tasks))

        # Notify users in manager chat if available
        if self._manager_chat_id and self._responder:
            bot = self._config.bot
            try:
                await self._responder.send_text(
                    self._manager_chat_id,
                    f"**{bot.emoji} {bot.name} Manager** is shutting down. Active workers will finish before exit.",
                )
            except Exception:
                pass

        if self._background_tasks:
            _, pending = await asyncio.wait(
                list(self._background_tasks),
                timeout=_GRACEFUL_SHUTDOWN_TIMEOUT,
            )
            for task in pending:
                logger.warning("Cancelling task that did not finish in time: %s", task.get_name())
                task.cancel()

        if self._db:
            await self._db.close()

    async def run(self) -> None:
        """Main polling loop."""
        self._running = True
        self._poll_interval = 5  # Start fast (5s), ramp up to max if idle
        self._poll_max = self._config.teams.poll_interval or 60
        self._idle_cycles = 0
        logger.info("J-Bot started, adaptive polling 5s→%ds", self._poll_max)

        # Create manager's dedicated chat on startup
        await self._ensure_manager_chat()

        # Auto-cleanup old sessions (older than 7 days)
        try:
            expired = await self._db.cleanup_expired_sessions()
            if expired:
                logger.info("Cleaned up %d expired sessions", expired)
        except Exception:
            logger.warning("Session cleanup failed", exc_info=True)

        # Proactive token refresh: refresh every 45 minutes (tokens last ~60 min)
        self._token_refresh_interval = 45 * 60  # seconds
        self._last_token_refresh = 0

        import time as _time
        while self._running:
            try:
                # Proactive token refresh before expiry
                now = _time.time()
                if now - self._last_token_refresh > self._token_refresh_interval:
                    try:
                        from niuma.teams_api import force_refresh
                        await asyncio.to_thread(force_refresh)
                        self._last_token_refresh = now
                    except Exception:
                        logger.warning("Proactive token refresh failed — will retry next cycle")
                        self._last_token_refresh = now  # Don't retry immediately on failure

                had_activity = await self.poll_once()
                if had_activity:
                    self._poll_interval = 5
                    self._idle_cycles = 0
                    self._consecutive_failures = 0
                else:
                    self._idle_cycles += 1
                    if self._idle_cycles > 3:
                        self._poll_interval = min(
                            self._poll_interval + 5, self._poll_max
                        )
            except ValueError as ve:
                if "no active connection" in str(ve):
                    logger.warning("DB connection lost — reconnecting")
                    try:
                        await self._db.reconnect()
                    except Exception:
                        logger.exception("DB reconnect failed")
                else:
                    logger.exception("Error in poll cycle")
                self._consecutive_failures += 1
                self._check_alert()
            except Exception:
                logger.exception("Error in poll cycle")
                self._consecutive_failures += 1
                self._check_alert()
            await asyncio.sleep(self._poll_interval)

    async def _check_config_reload(self) -> None:
        """Reload config if the file has been modified."""
        import os
        config_path = Path.home() / ".jbot" / "config.yaml"
        try:
            mtime = os.path.getmtime(config_path)
            if self._config_mtime == 0.0:
                self._config_mtime = mtime
                return
            if mtime > self._config_mtime:
                self._config_mtime = mtime
                new_config = load_config(config_path)
                self._config = new_config
                logger.info("Config reloaded from %s", config_path)
        except Exception:
            pass  # Non-fatal

    async def _try_refresh_token(self) -> None:
        """Attempt to refresh the Teams API token programmatically."""
        try:
            from niuma.teams_api import _get_access_token
            token = await asyncio.to_thread(_get_access_token)
            if token:
                logger.info("Token refreshed successfully via refresh token")
        except Exception as exc:
            logger.error("Token refresh failed: %s. Manual login needed: teams-cli auth login", exc)
            _send_alert("Auth expired", "Run: teams-cli auth login")

    def _check_alert(self) -> None:
        """Send alert if consecutive failures exceed threshold."""
        import time
        now = time.time()
        if self._consecutive_failures >= self._alert_threshold:
            # Only alert every 5 minutes to avoid spam
            if now - self._last_alert_time > 300:
                self._last_alert_time = now
                _send_alert(
                    f"{self._consecutive_failures} consecutive poll failures",
                    "Teams API may be down or auth expired. Run: teams-cli auth login"
                )

    def _record_poll_failure(self) -> None:
        """Record a poll failure and check if alert needed."""
        self._consecutive_failures += 1
        self._check_alert()

    def _record_poll_success(self) -> None:
        """Reset failure counter on success."""
        if self._consecutive_failures > 0:
            logger.info("Poll recovered after %d failures", self._consecutive_failures)
        self._consecutive_failures = 0

    async def poll_once(self) -> bool:
        """Single poll cycle. Returns True if any user message was processed."""
        self._had_activity = False
        logger.debug("Poll cycle start")
        await self._check_config_reload()
        # Merge config chat_ids with dynamically watched chats from DB
        watched = await self._db.list_watched_chats()
        watched_ids = {w["chat_id"]: w["mode"] for w in watched}
        # Config chat_ids are always full mode
        all_trigger_chats: dict[str, str] = {cid: "full" for cid in self._config.teams.chat_ids}
        all_trigger_chats.update(watched_ids)

        # reply_only set: from config + DB watched chats with mode='reply_only'
        reply_only_from_config = set(self._config.teams.reply_only_chat_ids)
        reply_only_from_db = {cid for cid, mode in watched_ids.items() if mode == "reply_only"}
        self._dynamic_reply_only = reply_only_from_config | reply_only_from_db

        # Poll configured trigger chats (trigger prefix required)
        for chat_id in all_trigger_chats:
            await self._poll_chat(chat_id)

        # Poll manager chat (no trigger needed, direct conversation)
        if self._manager_chat_id:
            await self._poll_manager_chat(self._manager_chat_id)

        # Poll session-dedicated chats
        if self._config.teams.auto_session_chats:
            session_chat_ids = await self._db.list_session_chat_ids()
            for chat_id in session_chat_ids:
                await self._poll_session_chat(chat_id)

        return self._had_activity

    async def _poll_and_get_new(
        self, chat_id: str, label: str = "chat",
    ) -> tuple[list, str] | None:
        """Common polling logic shared by _poll_chat, _poll_session_chat, _poll_manager_chat.

        Returns (all_messages, new_messages, newest_id) or None on error/first-poll/no-messages.
        Callers apply their own filtering (trigger filter, bot-message filter, etc.).
        """
        from niuma.poller import TeamsCliError

        try:
            raw = await self._poller.poll_chat(chat_id)
        except (TeamsCliError, RuntimeError):
            raise  # Let caller handle backoff / error specifics

        messages = self._poller.parse_messages(raw)
        if not messages:
            return None

        try:
            newest_id = max(messages, key=lambda m: int(m.id)).id
        except ValueError:
            newest_id = messages[0].id

        last_seen = await self._db.get_poll_state(chat_id)

        if last_seen is None:
            await self._db.set_poll_state(chat_id, newest_id)
            logger.info("First poll of %s %s: skipping existing messages", label, chat_id[:20])
            return None

        new_messages = self._poller.filter_new(messages, last_seen)
        await self._db.set_poll_state(chat_id, newest_id)

        if not new_messages:
            return None

        return new_messages, newest_id

    async def _poll_chat(self, chat_id: str) -> None:
        from niuma.poller import TeamsCliError

        try:
            result = await self._poll_and_get_new(chat_id, label="trigger chat")
            self._backoff_seconds[chat_id] = 0
            self._record_poll_success()
        except TeamsCliError as e:
            self._record_poll_failure()
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
                logger.error("Auth expired — attempting token refresh")
                await self._try_refresh_token()
                return
            else:
                logger.error("Poll failed for %s: %s", chat_id, e)
                return
        except RuntimeError as e:
            logger.error("Poll failed for %s: %s", chat_id, e)
            return

        if result is None:
            return

        new_messages, _ = result

        # Apply trigger filter (only triggered messages in trigger chats)
        triggered = self._poller.filter_triggered(new_messages)
        if not triggered:
            return

        for msg in triggered:
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

    async def _poll_session_chat(self, chat_id: str) -> None:
        """Poll a session-dedicated chat. All messages auto-route to the bound session."""
        try:
            result = await self._poll_and_get_new(chat_id, label="session chat")
        except Exception:
            return

        if result is None:
            return

        new_messages, _ = result

        # Find the bound session
        session = await self._db.get_session_by_chat_id(chat_id)
        if not session:
            return

        for msg in new_messages:
            if not self._is_allowed(msg.sender_email):
                continue

            # Skip bot's own messages
            if "Sent by J-Bot" in msg.body_raw or "ai-pim-utils" in msg.body_raw or "Sent by niuma" in msg.body_raw or "【🤖J-Bot】" in msg.body:
                continue

            prompt = msg.body.strip()
            if not prompt:
                continue

            # Auto-resume the bound session
            sid = session["id"]
            logger.info("Session chat %s: routing to session [%s]", chat_id[:20], sid)
            self._had_activity = True

            # Check if session is currently running — queue message for later
            current = await self._session_mgr.get_result(sid)
            if current and current.get("status") == "running":
                await self._db.add_message(sid, "user", prompt)
                await self._responder.send_text(
                    chat_id,
                    f"Worker is busy — your message has been queued. "
                    f"It will be sent as a follow-up when the current task finishes.",
                )
                continue

            try:
                await self._session_mgr.resume_session(
                    session_id=sid, prompt=prompt,
                )
                await self._responder.send_processing(chat_id, sid)
                self._fire_and_track(self._watch_session(chat_id, sid))
            except (ValueError, RuntimeError) as e:
                await self._responder.send_text(chat_id, str(e))

    async def _poll_manager_chat(self, chat_id: str) -> None:
        """Poll the Manager's dedicated chat. Messages here go directly to Manager."""
        try:
            result = await self._poll_and_get_new(chat_id, label="manager chat")
        except Exception:
            return

        if result is None:
            return

        new_messages, _ = result

        for msg in new_messages:
            if not self._is_allowed(msg.sender_email):
                continue
            if "Sent by J-Bot" in msg.body_raw or "ai-pim-utils" in msg.body_raw or "Sent by niuma" in msg.body_raw or "【🤖J-Bot】" in msg.body:
                continue
            prompt = msg.body.strip()
            if not prompt:
                continue

            # Route through Manager, responses go to manager chat
            await self._handle_message(chat_id, msg.sender_email, prompt, msg.id)

    def _is_reply_only(self, chat_id: str) -> bool:
        # Use dynamic set if populated by poll_once, otherwise fall back to config
        dynamic = getattr(self, "_dynamic_reply_only", None)
        if dynamic is not None:
            return chat_id in dynamic
        return chat_id in self._config.teams.reply_only_chat_ids

    async def _handle_message(
        self, chat_id: str, user_email: str, prompt: str,
        message_id: str = "",
    ) -> None:
        """Delegate to handler module for message routing."""
        self._had_activity = True
        from niuma.handler import handle_message
        await handle_message(self, chat_id, user_email, prompt, message_id)

    async def _watch_session(
        self, chat_id: str, session_id: str, reply_to: str = "",
    ) -> None:
        """Delegate to watcher module for session watching."""
        from niuma.watcher import watch_session
        await watch_session(self, chat_id, session_id, reply_to)

    def _is_allowed(self, email: str) -> bool:
        return (
            email in self._config.security.allowed_users
            or email in self._config.security.admin_users
            or (self._owner_email and email == self._owner_email)
            or (self._owner_display_name and email == self._owner_display_name)
        )


def _setup_logging(config: NiumaConfig) -> None:
    log_path = Path(config.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Only use StreamHandler — the watchdog's `tee` already writes stdout to log file.
    # Using both FileHandler + StreamHandler + tee causes duplicate log lines.
    logging.basicConfig(
        level=getattr(logging, config.logging.level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )


def cli_entry() -> None:
    parser = argparse.ArgumentParser(
        description="J-Bot (Everyone's Jarvis): Teams chat bot powered by Claude Code"
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
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.stdin = open(os.devnull, "r")
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
