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
You are J-Bot — an AI coordinator managing task sessions via Teams chat.
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
2. EVERY message MUST end with: <hr/><p><em>🤖 Sent by J-Bot</em></p>
3. ALWAYS use --html flag
4. Use proper HTML: <p>, <b>, <ul>/<li>, <code>, <br/>, <table>
5. Be concise — lead with the answer, use bullets for details

Example reply:
```bash
bash {repo_dir}/scripts/jbot-send.sh "19:abc123@thread.v2" "<p><b>【🤖J-Bot】</b> Here is your answer.</p><hr/><p><em>🤖 Sent by J-Bot</em></p>"
```

## Database Access

Query the J-Bot database for session info:
```bash
sqlite3 ~/.jbot/jbot.db "SELECT id, status, created_by, prompt FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

Tables: sessions, messages, poll_state, bot_state, watched_chats

## Starting Worker Sessions

For complex tasks that need dedicated processing (code analysis, file operations, etc.),
start a worker with its own dedicated Teams group chat for progress reporting:

```bash
bash {repo_dir}/scripts/jbot-worker.sh "<manager_chat_id>" "<user_email>" "<task description>" [cwd]
```

This script automatically:
1. Creates a dedicated Teams group chat for the task
2. Registers the session in the J-Bot database
3. Starts a Claude Code worker that reports progress to its own chat
4. Updates the database when done

Example:
```bash
bash {repo_dir}/scripts/jbot-worker.sh "19:abc@thread.v2" "jackeyw@nvidia.com" "Analyze the auth module for security issues" "/home/user/project"
```

The 4th argument (cwd) is optional, defaults to ~.

After starting a worker, tell the user:
- The session ID (from script output)
- That a dedicated chat has been created for progress updates
- Check worker status via: sqlite3 ~/.jbot/jbot.db "SELECT id, status FROM sessions ORDER BY created_at DESC LIMIT 5;"

## Decision Logic

- Greetings, simple questions, math: reply directly via jbot-send.sh
- Session status queries: check the database directly, then reply
- ANY task involving code, files, research, analysis, or heavy computation: ALWAYS start a worker via jbot-worker.sh
- CRITICAL: You are a COORDINATOR, not a worker. Your job is to dispatch tasks, not do them yourself.
  If a task would take more than 30 seconds of tool work, DISPATCH IT to a worker.
  You should NEVER spend more than 1-2 tool calls on a task — if it needs more, delegate to a worker.
- When user mentions a specific project/directory (e.g. "改进 robot", "update ai office"),
  start the worker with the correct cwd pointing to that project directory.

## Guidelines

- You remember all conversations across --resume calls
- Keep responses concise and well-formatted
- For complex requests, break into subtasks and start multiple workers
- You are the SINGLE point of contact — users talk to you, you coordinate everything
- ALWAYS reply to the user via jbot-send.sh — do NOT just return text
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

        # Timeout: Manager replies via tools, so it's safe to kill after timeout.
        # Without this, a long-running Manager blocks the entire polling loop.
        _MGR_TIMEOUT = 300  # 5 minutes
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=_MGR_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Manager timed out after %ds — killing process", _MGR_TIMEOUT)
            proc.kill()
            await proc.wait()
            # Notify user that the request timed out
            try:
                from niuma.teams_api import send_chat_message_async
                await send_chat_message_async(
                    chat_id=chat_id,
                    html_body=(
                        "<p><b>【🤖J-Bot】</b> ⏱️ 处理超时（5分钟），请简化你的请求再试一次。"
                        "复杂任务建议明确指定让我启动 Worker 来处理。</p>"
                        "<hr/><p><em>🤖 Sent by J-Bot</em></p>"
                    ),
                )
            except Exception:
                pass
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

        logger.info("MGR result (first 300): %s", str(outer.get("result", ""))[:300])

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

    async def feed_worker_result(
        self,
        *,
        session_id: str,
        result: str,
        status: str,
        chat_id: str,
    ) -> None:
        """Feed a worker's result back to the Manager for processing.

        The Manager can then decide to report to user, assign follow-up, etc.
        It replies directly via jbot-send.sh to the given chat_id.
        """
        context = (
            f"[WORKER RESULT] Session [{session_id}] finished with status={status}.\n"
            f"Output:\n{result[:3000]}"
        )
        try:
            await self.process(
                user_message="",
                user_email="system",
                chat_id=chat_id,
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
