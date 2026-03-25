# src/niuma/manager.py
"""Stateful Manager session — the 'team lead' that manages all worker sessions.

Unlike the old stateless Dispatcher, the Manager is a single persistent Claude Code
session that gets --resume'd for every user message. It remembers all context:
who asked what, which workers are running, what results came back.

The Manager returns structured JSON instructions that the bot executes.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from niuma.config import ClaudeConfig
from niuma.session import _claude_command

if TYPE_CHECKING:
    from niuma.db import Database

logger = logging.getLogger(__name__)

_MANAGER_SYSTEM_PROMPT = """\
You are J-Bot — an AI coordinator managing task sessions via Teams chat.

## Decision Logic

Use "reply" when you CAN answer from your own memory/knowledge:
- Greetings, math, simple factual questions
- Session status you already know (you received worker results)
- Listing sessions you remember — just summarize from memory
- Cost summaries from data you've already seen

Use "new" ONLY when the task requires tools, file access, or fresh data:
- Code analysis, bug fixing, test generation, documentation
- Tasks that need shell commands or file system access
- Queries that need LIVE data you don't have in memory

Key: If you already have the answer in your conversation history, use "reply". \
Do NOT spawn a new session just to look up information you already know.

## Actions (return ONE as JSON)

1. {"action": "reply", "reply_text": "your answer"}
   Answer directly from memory/knowledge.

2. {"action": "new", "prompt": "task description", "dedicated_chat": true/false}
   Start a new task session. Set dedicated_chat=true for complex/verbose tasks.
   Do NOT include "cwd" unless user provides an exact path.

3. {"action": "resume", "session_id": "XXXX", "prompt": "follow-up"}
   Continue an existing session.

4. {"action": "report", "reply_text": "status update"}
   Proactive status report.

5. {"action": "stop", "session_id": "XXXX"}
   Kill a running session.

6. {"action": "new", "prompt": "...", "model": "opus"}
   Override model. Options: "haiku" (fast), "sonnet" (balanced), "opus" (deep reasoning).

## Context Management
- You have a 1M token context window but should use it wisely.
- After receiving worker results, mentally compress: keep the KEY FINDINGS and \
DECISIONS, discard verbose raw output. When reporting to users, be concise.
- If you notice your context getting long, summarize older session results \
into brief notes so you retain the important facts without the bulk.

## Guidelines
- You remember all conversations, session assignments, and results across restarts.
- When a worker finishes, summarize key findings and report to the user.
- For complex requests, break into subtasks and assign multiple sessions.
- You are the SINGLE point of contact — users don't talk to sessions directly.

## IMPORTANT: You can use tools!
You have full access to the filesystem, shell, and tools. You CAN:
- Query ~/.jbot/jbot.db directly to check sessions, costs, status
- Read files, run commands, check system state
- Then make an informed decision

## CRITICAL OUTPUT FORMAT
Your FINAL text response MUST be ONLY a valid JSON object. Examples:
{"action": "reply", "reply_text": "Hello! Here are your sessions..."}
{"action": "new", "prompt": "analyze the auth module", "dedicated_chat": true}
{"action": "resume", "session_id": "0325-a7f3", "prompt": "continue"}
{"action": "stop", "session_id": "0325-a7f3"}

Do NOT wrap in markdown. Do NOT add explanation. ONLY the JSON object.\
"""

_MANAGER_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "action": {"enum": ["new", "resume", "reply", "report", "stop"]},
        "session_id": {"type": "string"},
        "prompt": {"type": "string"},
        "cwd": {"type": "string"},
        "reply_text": {"type": "string"},
        "dedicated_chat": {"type": "boolean"},
        "model": {"type": "string"},
    },
    "required": ["action"],
})


@dataclass(frozen=True)
class ManagerDecision:
    action: str
    session_id: Optional[str] = None
    prompt: Optional[str] = None
    cwd: Optional[str] = None
    reply_text: Optional[str] = None
    dedicated_chat: bool = False
    model: Optional[str] = None

    @classmethod
    def from_claude_output(cls, raw_output: str) -> "ManagerDecision":
        """Parse the JSON output from claude -p --output-format json."""
        outer = json.loads(raw_output)

        inner = outer.get("structured_output")
        if not isinstance(inner, dict):
            # Fallback: try parsing result as JSON
            result_str = outer.get("result", "")
            if isinstance(result_str, str) and result_str.strip().startswith("{"):
                try:
                    inner = json.loads(result_str)
                except json.JSONDecodeError:
                    inner = {}
            else:
                # Manager returned plain text — treat as reply
                inner = {"action": "reply", "reply_text": str(result_str or inner or "")}

        return cls(
            action=inner.get("action", "reply"),
            session_id=inner.get("session_id"),
            prompt=inner.get("prompt"),
            cwd=inner.get("cwd"),
            reply_text=inner.get("reply_text"),
            dedicated_chat=inner.get("dedicated_chat", False),
            model=inner.get("model"),
        )


_BOT_STATE_MANAGER_SESSION = "manager_session_id"


class Manager:
    """Stateful Manager that persists across interactions via --resume."""

    def __init__(self, config: ClaudeConfig, db: Optional["Database"] = None) -> None:
        self._config = config
        self._db = db
        self._session_id: Optional[str] = None
        self._initialized = False

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
                logger.info("Resumed Manager session from DB: %s", saved[:12])
        except Exception:
            logger.warning("Could not load manager session from DB", exc_info=True)

    async def decide(
        self,
        *,
        user_message: str,
        user_email: str,
        context: str = "",
    ) -> ManagerDecision:
        """Send a message to the Manager and get a structured decision back.

        The Manager session is resumed each time, maintaining full conversation history.
        Context can include worker results, status updates, etc.
        """
        prompt = self._build_prompt(user_message, user_email, context)

        # Manager uses tools freely + returns JSON as final text.
        # No --json-schema (broken on --resume). System prompt instructs
        # JSON output; from_claude_output parses it from result text.
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

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()

            # If resume failed because session was deleted/expired, auto-create new session
            if self._session_id and "No conversation found" in error_msg:
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
                return await self.decide(
                    user_message=user_message,
                    user_email=user_email,
                    context=context,
                )

            raise RuntimeError(
                f"Manager claude call failed (exit {proc.returncode}): "
                f"{error_msg[:200]}"
            )

        raw = stdout.decode()
        outer = json.loads(raw)

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

        return ManagerDecision.from_claude_output(raw)

    async def feed_worker_result(
        self,
        *,
        session_id: str,
        result: str,
        status: str,
    ) -> ManagerDecision:
        """Feed a worker's result back to the Manager for processing.

        The Manager can then decide to report to user, assign follow-up, etc.
        Errors are caught and logged so callers (the watch loop) remain unaffected.
        """
        context = (
            f"[WORKER RESULT] Session [{session_id}] finished with status={status}.\n"
            f"Output:\n{result[:3000]}"
        )
        try:
            return await self.decide(
                user_message="",
                user_email="system",
                context=context,
            )
        except Exception:
            logger.exception(
                "feed_worker_result failed for session %s — returning no-op reply", session_id
            )
            return ManagerDecision(action="reply", reply_text="")

    def _build_prompt(
        self, user_message: str, user_email: str, context: str
    ) -> str:
        parts = []
        if context:
            parts.append(context)
        if user_message:
            parts.append(f"[USER MESSAGE from {user_email}]: {user_message}")
        return "\n\n".join(parts) if parts else "No new input."
