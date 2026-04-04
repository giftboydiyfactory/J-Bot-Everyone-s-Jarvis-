# src/niuma/manager.py
"""Stateful Manager session — the 'team lead' that manages all worker sessions.

The Manager is a persistent Claude Code session that gets --resume'd for every
user message. It has full tool access and replies DIRECTLY to Teams using
jbot-send.sh (Graph API), eliminating the JSON-parsing bottleneck.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from niuma.config import ClaudeConfig
from niuma.session import _claude_command, _load_skills

if TYPE_CHECKING:
    from niuma.db import Database

logger = logging.getLogger(__name__)


def _build_manager_system_prompt() -> str:
    """Build the full Manager system prompt with skills injected."""
    import pathlib
    repo_dir = str(pathlib.Path(__file__).parent.parent.parent)
    skills_content = _load_skills()

    prompt = f"""\
You are J-Bot — Everyone's Jarvis. An AI assistant available via Teams chat.
You have FULL tool access: filesystem, shell, sqlite3, jbot-send.sh, claude CLI.

## How to Reply to Users

You reply DIRECTLY to Teams. The chat_id is provided in every message.
Use this command to send messages:

```bash
bash {repo_dir}/scripts/jbot-send.sh "<chat_id>" "<your HTML message>"
```

This uses Graph API with automatic token refresh — no manual auth needed.

IMPORTANT: ALWAYS use jbot-send.sh for sending messages.
NEVER use "teams-cli" — it is NOT installed and will hang/fail.
jbot-send.sh uses Graph API directly with automatic token refresh.

CRITICAL FORMATTING RULES:
1. EVERY message MUST start with: <p><b>【🤖J-Bot】</b>
2. DO NOT append any footer/signature — the system adds it automatically.
3. ALWAYS use --html flag
4. Use proper HTML: <p>, <b>, <ul>/<li>, <code>, <br/>, <table>
5. Be concise — lead with the answer, use bullets for details
6. NEVER include "★ Insight" blocks — those are internal only, never for users.
7. NEVER send internal status like "已通知用户" or "Notified user" — only send substantive content.

Example reply:
```bash
bash {repo_dir}/scripts/jbot-send.sh "19:abc123@thread.v2" "<p><b>【🤖J-Bot】</b> Here is your answer.</p>"
```

## Microsoft 365 Tools (all via Graph API — no CLI auth needed)

### Send Teams message:
```bash
bash {repo_dir}/scripts/jbot-send.sh "<chat_id>" "<html_body>"
```

### Create Outlook draft (saved to Drafts folder, NOT sent):
```bash
bash {repo_dir}/scripts/jbot-draft.sh "<subject>" "<to_email>" "<html_body>" [cc_email]
```

### Send email directly:
```bash
bash {repo_dir}/scripts/jbot-email.sh "<subject>" "<to_email>" "<html_body>" [cc_email]
```

### Create calendar event:
```bash
bash {repo_dir}/scripts/jbot-calendar.sh "<subject>" "<start_datetime>" "<end_datetime>" [attendee_email] [body_html]
```
Start/end format: "2026-03-30T10:00:00" (Asia/Shanghai timezone)

NEVER use outlook-cli, calendar-cli, or teams-cli for write operations.
All jbot-*.sh scripts use Graph API with automatic token refresh.

## Database Access

Query the J-Bot database for session info:
```bash
sqlite3 ~/.jbot/jbot.db "SELECT id, status, created_by, prompt FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

Tables: sessions, messages, poll_state, bot_state, watched_chats

## Worker Session Management

### Resuming vs Creating Sessions

BEFORE starting a new worker, ALWAYS check if there is an existing session for the same project/task:
```bash
sqlite3 ~/.jbot/jbot.db "SELECT id, status, session_chat_id, prompt FROM sessions WHERE status='running' ORDER BY created_at DESC LIMIT 5;"
```

- If a RUNNING session exists for the same project → send a follow-up message to its dedicated chat via jbot-send.sh, do NOT create a new session
- If no matching session exists OR user explicitly says "new session" → create a new one via jbot-worker.sh
- If a session is stuck (running but no worker process) → update its status to 'failed', then create new

### Starting a New Worker

```bash
bash {repo_dir}/scripts/jbot-worker.sh "<manager_chat_id>" "<user_email>" "<task description>" [cwd]
```

This automatically: creates a Teams group chat, registers in DB, launches worker in background, worker reports progress to its chat.

Example:
```bash
bash {repo_dir}/scripts/jbot-worker.sh "19:abc@thread.v2" "jackeyw@nvidia.com" "Analyze auth module" "/home/user/project"
```

The 4th argument (cwd) is optional, defaults to ~.

After starting a worker, tell the user: session ID, that a dedicated chat was created for progress.

## Decision Logic

- Greetings, simple questions, math, session status: reply directly via jbot-send.sh
- EVERYTHING ELSE: dispatch via jbot-worker.sh. This includes:
  - Writing code or scripts
  - Analyzing codebases
  - Creating email drafts or reports
  - Research tasks
  - File operations
  - Any task the user explicitly asks to "dispatch" or "start a worker" for

## STRICT RULES — DO NOT VIOLATE

1. You are a DISPATCHER. You do NOT write code, create files, or run complex commands yourself.
2. Your only tools are: jbot-send.sh (reply), jbot-worker.sh (dispatch), sqlite3 (check DB).
3. If a task needs more than a greeting or DB query, you MUST call jbot-worker.sh.
4. NEVER fake a dispatch. If you say "Worker dispatched", jbot-worker.sh MUST have been called.
5. NEVER use `claude -p` directly. ALWAYS use jbot-worker.sh for task dispatch.

## Guidelines

- You remember all conversations across --resume calls
- Keep responses concise and well-formatted
- For complex requests, break into subtasks and start multiple workers
- You are the SINGLE point of contact — users talk to you, you coordinate everything

## CRITICAL: You MUST send EVERY response to Teams

NEVER just return text. The user CANNOT see your text output.
Your ONLY way to communicate is via jbot-send.sh.
After EVERY action (greeting, status update, worker dispatch, cron setup, etc.),
you MUST call jbot-send.sh to send the result to the chat_id.
If you don't call jbot-send.sh, the user sees NOTHING.
"""

    if skills_content:
        prompt += f"\n\n# Available Skills (reference guides for tools)\n{skills_content}"

    return prompt


# Cache the prompt at module load
_MANAGER_SYSTEM_PROMPT = _build_manager_system_prompt()


@dataclass(frozen=True)
class ManagerDecision:
    """Minimal fallback dataclass — kept for backward compatibility."""
    action: str
    reply_text: Optional[str] = None

    @classmethod
    def from_claude_output(cls, raw_output: str) -> "ManagerDecision":
        """Parse claude output — minimal fallback only."""
        try:
            outer = json.loads(raw_output)
            result_str = outer.get("result", "")
            return cls(action="reply", reply_text=str(result_str or ""))
        except (json.JSONDecodeError, TypeError):
            return cls(action="reply", reply_text="")


_BOT_STATE_MANAGER_SESSION = "manager_session_id"


class Manager:
    """Stateful Manager that persists across interactions via --resume.

    The Manager has full tool access and replies directly to Teams via jbot-send.sh.
    No JSON parsing needed — the Manager handles everything.
    """

    # How long before we consider the Manager session potentially stale (seconds).
    # If this threshold is exceeded without a successful process() call, the
    # next process() will verify the session is still alive before resuming.
    _WATCHDOG_INTERVAL: int = int(
        __import__("os").environ.get("JBOT_MGR_WATCHDOG_INTERVAL", "3600")
    )

    def __init__(self, config: ClaudeConfig, db: Optional["Database"] = None) -> None:
        self._config = config
        self._db = db
        self._session_id: Optional[str] = None
        self._initialized = False
        self._last_success_ts: float = 0.0

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    async def load_state(self) -> None:
        """Load persisted manager session_id from DB on startup."""
        if self._db is None:
            return
        try:
            saved = await self._db.get_bot_state(_BOT_STATE_MANAGER_SESSION)
            if saved:
                self._session_id = saved
                self._initialized = True
                self._last_success_ts = time.time()
                logger.info("Resumed Manager session from DB: %s", saved[:12])
        except Exception:
            logger.warning("Could not load manager session from DB", exc_info=True)

    async def _check_session_health(self) -> bool:
        """Verify the Manager session is still alive (watchdog).

        Returns True if the session is healthy or no session exists yet.
        If the session is expired/dead, clears it so a fresh one is created.
        """
        if not self._session_id:
            return True  # No session to check -- will create fresh

        # Only check if enough time has passed since last success
        elapsed = time.time() - self._last_success_ts if self._last_success_ts else float("inf")
        if elapsed < self._WATCHDOG_INTERVAL:
            return True

        logger.info("Watchdog: checking Manager session %s health", self._session_id[:12])

        claude_cmd = _claude_command()
        try:
            proc = await asyncio.create_subprocess_exec(
                *claude_cmd, "-p", "ping",
                "--resume", self._session_id,
                "--output-format", "json",
                "--permission-mode", self._config.permission_mode,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=30)
            error_msg = stderr_bytes.decode().strip()

            if proc.returncode != 0 and "No conversation found" in error_msg:
                logger.warning(
                    "Watchdog: Manager session %s expired -- creating fresh session",
                    self._session_id[:12],
                )
                self._session_id = None
                self._initialized = False
                if self._db is not None:
                    try:
                        await self._db.set_bot_state(_BOT_STATE_MANAGER_SESSION, "")
                    except Exception:
                        pass
                return True  # Session cleared, process() will create new one

            # Session is alive
            self._last_success_ts = time.time()
            logger.info("Watchdog: Manager session %s is healthy", self._session_id[:12])
            return True
        except asyncio.TimeoutError:
            logger.warning("Watchdog: health check timed out -- assuming session is alive")
            return True
        except Exception:
            logger.warning("Watchdog: health check failed", exc_info=True)
            return True

    async def process(
        self,
        *,
        user_message: str,
        user_email: str,
        chat_id: str,
        context: str = "",
        _is_retry: bool = False,
    ) -> None:
        """Send a message to the Manager — it replies directly via jbot-send.sh.

        The Manager session is resumed each time, maintaining full conversation history.
        The chat_id is injected so Manager always knows where to reply.
        """
        prompt = self._build_prompt(user_message, user_email, chat_id, context)

        # Watchdog: verify session is alive before resuming (Phase 2)
        if self._config.persistent_manager and not _is_retry:
            await self._check_session_health()

        claude_cmd = _claude_command()

        if self._session_id:
            proc = await asyncio.create_subprocess_exec(
                *claude_cmd, "-p", prompt,
                "--resume", self._session_id,
                "--output-format", "json",
                "--permission-mode", self._config.permission_mode,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *claude_cmd, "-p", prompt,
                "--model", self._config.dispatcher_model,
                "--append-system-prompt", _MANAGER_SYSTEM_PROMPT,
                "--output-format", "json",
                "--permission-mode", self._config.permission_mode,
                "-n", "jbot-manager",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        # Timeout: Manager sends replies via jbot-send.sh as it works.
        # After timeout, release the poll loop but let Manager keep running in background.
        _MGR_TIMEOUT = 1800  # 30 minutes
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=_MGR_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Manager still running after %ds — releasing poll loop (process continues in background)", _MGR_TIMEOUT)
            # Don't kill — Manager is working and reporting via jbot-send.sh.
            # Mark as initialized so next call attempts resume, not duplicate creation.
            if not self._initialized:
                self._initialized = True
                logger.info("Manager first-call timeout — marking initialized to prevent duplicate sessions")
            return

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()

            # If resume failed because session was deleted/expired, auto-create new session
            if self._session_id and "No conversation found" in error_msg:
                if _is_retry:
                    raise RuntimeError("Manager session creation failed after retry")
                logger.warning(
                    "Manager session %s expired — creating fresh session", self._session_id[:12]
                )
                self._session_id = None
                if self._db is not None:
                    try:
                        await self._db.set_bot_state(_BOT_STATE_MANAGER_SESSION, "")
                    except Exception:
                        pass
                # Retry with a fresh session
                return await self.process(
                    user_message=user_message,
                    user_email=user_email,
                    chat_id=chat_id,
                    context=context,
                    _is_retry=True,
                )

            raise RuntimeError(
                f"Manager claude call failed (exit {proc.returncode}): "
                f"{error_msg[:200]}"
            )

        raw = stdout.decode()
        try:
            outer = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Manager returned non-JSON output: %s", raw[:200])
            return

        result_text = str(outer.get("result", ""))
        logger.info("MGR result (first 300): %s", result_text[:300])

        # Manager sends directly to Teams via jbot-send.sh during execution.
        # The result_text here is just the Claude output summary — NOT for sending.
        # Only log it for debugging; no fallback send needed.

        # Save session ID for future resume (including across restarts)
        new_sid = outer.get("session_id")
        if new_sid and new_sid != self._session_id:
            self._session_id = new_sid
            self._initialized = True
            if self._db is not None:
                try:
                    await self._db.set_bot_state(_BOT_STATE_MANAGER_SESSION, new_sid)
                except Exception:
                    logger.warning("Failed to persist manager session_id to DB", exc_info=True)

        # Watchdog: record successful interaction timestamp
        self._last_success_ts = time.time()

    async def feed_worker_result(
        self,
        *,
        session_id: str,
        result: str,
        status: str,
        chat_id: str,
        manager_chat_id: str = "",
    ) -> None:
        """Feed a worker's result back to the Manager for context tracking.

        The Manager sends its summary to the MANAGER chat (not the session chat)
        to avoid duplicating what the Worker already sent to the session chat.
        """
        # Use manager chat for Manager's reply — worker already reported to session chat
        reply_chat = manager_chat_id or chat_id
        context = (
            f"[WORKER RESULT] Session [{session_id}] finished with status={status}.\n"
            f"The worker already sent results to the session chat. "
            f"Send your summary to the MANAGER chat only (chat_id below), NOT the session chat.\n"
            f"Output:\n{result[:3000]}"
        )
        try:
            await self.process(
                user_message="",
                user_email="system",
                chat_id=reply_chat,
                context=context,
            )
        except Exception:
            logger.exception(
                "feed_worker_result failed for session %s", session_id
            )

    def _build_prompt(
        self, user_message: str, user_email: str, chat_id: str, context: str
    ) -> str:
        parts = [f"[REPLY TARGET] chat_id={chat_id}"]
        if context:
            parts.append(context)
        if user_message:
            parts.append(f"[USER MESSAGE from {user_email}]: {user_message}")
        return "\n\n".join(parts)
