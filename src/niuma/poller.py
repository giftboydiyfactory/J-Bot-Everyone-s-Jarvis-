# src/niuma/poller.py
"""Teams chat polling via Graph API.

Uses Graph API directly instead of teams-cli subprocess.
Token refresh is handled automatically via teams_api module.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import re
import urllib.request
import urllib.error
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
    body_raw: str  # Original HTML before stripping — used for bot message detection
    timestamp: str
    image_urls: tuple[str, ...] = ()  # Graph API URLs for inline images


class TeamsCliError(RuntimeError):
    """Error from polling with exit code for specific handling."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _graph_get_messages_sync(chat_id: str, limit: int = 25) -> list[dict[str, Any]]:
    """Fetch chat messages via Graph API (synchronous, for asyncio.to_thread)."""
    import socket
    socket.setdefaulttimeout(20)  # Force timeout on all sockets including SSL handshake

    from niuma.teams_api import _get_access_token

    token = _get_access_token()
    url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages?$top={limit}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")

    try:
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        return data.get("value", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:300]
        if e.code == 401:
            raise TeamsCliError(exit_code=2, message=f"Graph API auth failed: {error_body}")
        elif e.code == 429:
            raise TeamsCliError(exit_code=5, message=f"Graph API rate limited: {error_body}")
        elif e.code == 404:
            raise TeamsCliError(exit_code=3, message=f"Chat not found: {chat_id}")
        else:
            raise TeamsCliError(exit_code=1, message=f"Graph API error {e.code}: {error_body}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise TeamsCliError(exit_code=7, message=f"Network error: {e}")


class Poller:
    def __init__(self, config: TeamsConfig) -> None:
        self._config = config

    async def poll_chat(self, chat_id: str, limit: int = 25) -> str:
        """Fetch messages via Graph API and return as JSON string.

        Returns a JSON string in the same format parse_messages expects.
        """
        try:
            messages = await asyncio.to_thread(
                _graph_get_messages_sync, chat_id, limit
            )
        except TeamsCliError:
            raise
        except Exception as exc:
            raise TeamsCliError(exit_code=7, message=f"Poll failed: {exc}")

        # Wrap in the format parse_messages expects
        return json.dumps({"data": messages})

    def parse_messages(self, raw_json: str) -> list[TeamsMessage]:
        """Parse JSON output into TeamsMessage objects."""
        data = json.loads(raw_json)

        # Handle formats: {"data": [...]} and {"data": {"messages": [...]}}
        raw_data = data.get("data", [])
        if isinstance(raw_data, dict):
            messages_data = raw_data.get("messages", [])
        elif isinstance(raw_data, list):
            messages_data = raw_data
        else:
            logger.warning("Unexpected data format")
            return []

        result = []
        for msg in messages_data:
            # Graph API format: "from" -> "user" -> "displayName"/"id"
            from_field = msg.get("from", {})
            from_user = from_field.get("user", {}) if from_field else {}
            email = from_user.get("email", "")
            if not email:
                email = from_user.get("displayName", from_user.get("id", "unknown"))
            body_raw = msg.get("body", {}).get("content", "")
            image_urls = _extract_image_urls(body_raw)
            result.append(TeamsMessage(
                id=msg.get("id", ""),
                sender=from_user.get("displayName", "unknown"),
                sender_email=email,
                body=_strip_html(body_raw),
                body_raw=body_raw,
                timestamp=msg.get("createdDateTime", ""),
                image_urls=tuple(image_urls),
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
        """Return messages newer than last_seen_id."""
        if last_seen_id is None:
            return messages

        try:
            last_seen_num = int(last_seen_id)
            return [m for m in messages if int(m.id) > last_seen_num]
        except ValueError:
            found = False
            new_messages = []
            for msg in messages:
                if found:
                    new_messages.append(msg)
                elif msg.id == last_seen_id:
                    found = True
            return new_messages


def _extract_image_urls(body_html: str) -> list[str]:
    """Extract Graph API hosted content image URLs from Teams message HTML.

    Teams inline images use: <img src="https://graph.microsoft.com/.../hostedContents/.../$value" .../>
    """
    return re.findall(
        r'<img\s+[^>]*src="(https://graph\.microsoft\.com/[^"]*hostedContents[^"]*)"',
        body_html,
        re.IGNORECASE,
    )


def _strip_html(text: str) -> str:
    """Remove HTML tags from text, preserving link URLs inline."""
    text = re.sub(
        r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r"\2 (\1)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ")
    return text.strip()
