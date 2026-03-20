# src/niuma/poller.py
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from niuma.config import TeamsConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TeamsMessage:
    id: str
    sender: str
    sender_email: str
    body: str
    timestamp: str


class TeamsCliError(RuntimeError):
    """Error from teams-cli with exit code for specific handling."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class Poller:
    def __init__(self, config: TeamsConfig) -> None:
        self._config = config

    async def poll_chat(self, chat_id: str, limit: int = 25) -> str:
        """Call teams-cli chat read and return raw JSON output."""
        proc = await asyncio.create_subprocess_exec(
            "teams-cli", "chat", "read", chat_id,
            "--limit", str(limit), "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            raise TeamsCliError(
                exit_code=proc.returncode,
                message=f"teams-cli chat read failed (exit {proc.returncode}): {error_msg}",
            )
        return stdout.decode()

    def parse_messages(self, raw_json: str) -> list[TeamsMessage]:
        """Parse teams-cli JSON output into TeamsMessage objects."""
        data = json.loads(raw_json)
        if not data.get("success"):
            logger.warning("teams-cli returned unsuccessful response")
            return []

        messages_data = data.get("data", {}).get("messages", [])
        result = []
        for msg in messages_data:
            from_user = msg.get("from", {}).get("user", {})
            result.append(TeamsMessage(
                id=msg["id"],
                sender=from_user.get("displayName", "unknown"),
                sender_email=from_user.get("email", "unknown"),
                body=msg.get("body", {}).get("content", ""),
                timestamp=msg.get("createdDateTime", ""),
            ))
        return result

    def filter_triggered(self, messages: list[TeamsMessage]) -> list[TeamsMessage]:
        """Return only messages that start with the trigger prefix."""
        trigger = self._config.trigger.lower()
        return [m for m in messages if m.body.strip().lower().startswith(trigger)]

    def extract_prompt(self, message: TeamsMessage) -> str:
        """Strip trigger prefix from message body."""
        trigger = self._config.trigger
        body = message.body.strip()
        if body.lower().startswith(trigger.lower()):
            body = body[len(trigger):]
        return body.strip()

    def filter_new(
        self, messages: list[TeamsMessage], last_seen_id: Optional[str]
    ) -> list[TeamsMessage]:
        """Return messages newer than last_seen_id.

        Assumes messages are ordered oldest-first by the API.
        If last_seen_id is None, return all messages.
        """
        if last_seen_id is None:
            return messages

        found = False
        new_messages = []
        for msg in messages:
            if found:
                new_messages.append(msg)
            elif msg.id == last_seen_id:
                found = True

        return new_messages
