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
from typing import Any, Optional

from niuma.config import ClaudeConfig

logger = logging.getLogger(__name__)

_MANAGER_SYSTEM_PROMPT = """\
You are the niuma-bot Manager — the team lead of an AI worker team.

## Your Role
You receive messages from users via Teams chat. You decide how to handle each message:
- Answer simple questions yourself (action: "reply")
- Delegate complex tasks to worker sessions (action: "new")
- Follow up with existing workers (action: "resume")

## Your Capabilities
You have MEMORY — you remember all previous conversations, worker assignments, and results.
You manage a team of Claude Code worker sessions. Each worker has:
- A session ID (e.g. "0320-a7f3")
- A status (pending/running/completed/failed)
- A working directory
- A claude_session UUID for resuming

## Worker Infrastructure
Workers have access to:
- File system, shell commands, code editing
- teams-cli for Teams messages
- niuma DB at ~/.niuma/niuma.db
- Claude session history at ~/.claude/projects/

## Instructions Format
Return a JSON object with ONE of these actions:

1. {"action": "reply", "reply_text": "your answer"}
   For simple questions you can answer from memory/knowledge

2. {"action": "new", "prompt": "task description", "cwd": "/path", "dedicated_chat": true/false}
   Delegate a new task. Set dedicated_chat=true for complex tasks with lots of output.

3. {"action": "resume", "session_id": "XXXX", "prompt": "follow-up instructions"}
   Send follow-up to an existing worker

4. {"action": "report", "reply_text": "status update"}
   Proactively report status/summary to the user

## Guidelines
- When a user asks about worker status, check your memory first (you saw the results)
- When a worker finishes, you'll receive its output. Summarize and report to user.
- For complex requests, break them into subtasks and assign to multiple workers
- Keep the user informed about what's happening
- You are the SINGLE point of contact. Users don't talk to workers directly.

Return ONLY valid JSON. No other text.\
"""

_MANAGER_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "action": {"enum": ["new", "resume", "reply", "report"]},
        "session_id": {"type": "string"},
        "prompt": {"type": "string"},
        "cwd": {"type": "string"},
        "reply_text": {"type": "string"},
        "dedicated_chat": {"type": "boolean"},
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

    @classmethod
    def from_claude_output(cls, raw_output: str) -> "ManagerDecision":
        """Parse the JSON output from claude -p --output-format json."""
        outer = json.loads(raw_output)

        inner = outer.get("structured_output")
        if inner is None:
            result_str = outer.get("result", "{}")
            inner = json.loads(result_str) if isinstance(result_str, str) and result_str else {}

        return cls(
            action=inner.get("action", "reply"),
            session_id=inner.get("session_id"),
            prompt=inner.get("prompt"),
            cwd=inner.get("cwd"),
            reply_text=inner.get("reply_text"),
            dedicated_chat=inner.get("dedicated_chat", False),
        )


class Manager:
    """Stateful Manager that persists across interactions via --resume."""

    def __init__(self, config: ClaudeConfig) -> None:
        self._config = config
        self._session_id: Optional[str] = None
        self._initialized = False

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

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

        if self._session_id:
            # Resume existing Manager session
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p", prompt,
                "--resume", self._session_id,
                "--json-schema", _MANAGER_SCHEMA,
                "--output-format", "json",
                "--permission-mode", self._config.permission_mode,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            # First call: create new Manager session
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p", prompt,
                "--model", self._config.dispatcher_model,
                "--json-schema", _MANAGER_SCHEMA,
                "--system-prompt", _MANAGER_SYSTEM_PROMPT,
                "--output-format", "json",
                "--permission-mode", self._config.permission_mode,
                "-n", "niuma-manager",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Manager claude call failed (exit {proc.returncode}): "
                f"{stderr.decode().strip()[:200]}"
            )

        raw = stdout.decode()
        outer = json.loads(raw)

        # Save session ID for future resume
        new_sid = outer.get("session_id")
        if new_sid:
            self._session_id = new_sid
            self._initialized = True

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
        """
        context = (
            f"[WORKER RESULT] Session [{session_id}] finished with status={status}.\n"
            f"Output:\n{result[:3000]}"
        )
        return await self.decide(
            user_message="",
            user_email="system",
            context=context,
        )

    def _build_prompt(
        self, user_message: str, user_email: str, context: str
    ) -> str:
        parts = []
        if context:
            parts.append(context)
        if user_message:
            parts.append(f"[USER MESSAGE from {user_email}]: {user_message}")
        return "\n\n".join(parts) if parts else "No new input."
