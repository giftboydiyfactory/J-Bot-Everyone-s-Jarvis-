# src/niuma/responder.py
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Optional

import markdown

logger = logging.getLogger(__name__)

_DEFAULT_BOT_NAME = "jbot"
_MAX_BODY_LEN = 2000


def _make_signature(bot_name: str = _DEFAULT_BOT_NAME, bot_emoji: str = "🤖") -> str:
    display_name = "J-Bot" if bot_name == "jbot" else bot_name
    return ""


# Marker appended to all bot messages — Teams strips HTML comments,
# so we use a visible but subtle signature that the poller can detect.
_BOT_MARKER = '<hr/><p><em>🤖 Sent by J-Bot</em></p>'


def _make_prefix(bot_name: str = _DEFAULT_BOT_NAME, bot_emoji: str = "🤖") -> str:
    display_name = "J-Bot" if bot_name == "jbot" else bot_name
    return f"【{bot_emoji}{display_name}】"


def format_processing(session_id: str, bot_name: str = _DEFAULT_BOT_NAME, bot_emoji: str = "🤖") -> str:
    sig = _make_signature(bot_name, bot_emoji)
    return f"<p>session [<b>{_escape(session_id)}</b>] processing...</p>{sig}"


def format_result(
    session_id: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
    output_dir: Optional[str] = None,
    bot_name: str = _DEFAULT_BOT_NAME,
    bot_emoji: str = "🤖",
) -> str:
    sig = _make_signature(bot_name, bot_emoji)
    safe_sid = _escape(session_id)
    if error:
        return (
            f"<p>session [<b>{safe_sid}</b>] failed</p>"
            f"<p><code>{_escape(error[:500])}</code></p>"
            f"{sig}"
        )

    text = result or ""
    if len(text) <= _MAX_BODY_LEN:
        body_html = _md_to_html(text)
        return (
            f"<p><b>session [{safe_sid}] done</b></p>"
            f"{body_html}"
            f"{sig}"
        )

    # Save full output, send truncated
    saved_path = ""
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{session_id}.md"
        out_file.write_text(text)
        saved_path = str(out_file)

    summary = text[:_MAX_BODY_LEN]
    body_html = _md_to_html(summary)
    truncated_note = (
        f" Full output saved to <code>{saved_path}</code>"
        if saved_path else " (output truncated)"
    )

    return (
        f"<p><b>session [{safe_sid}] done</b></p>"
        f"{body_html}"
        f"<p><em>...{truncated_note}</em></p>"
        f"{sig}"
    )


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_to_html(text: str) -> str:
    """Convert Markdown text to HTML for Teams rendering."""
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "nl2br"],
    )


class Responder:
    def __init__(self, output_dir: str = "~/.jbot/outputs", bot_name: str = _DEFAULT_BOT_NAME, bot_emoji: str = "🤖") -> None:
        self._output_dir = str(Path(output_dir).expanduser())
        self._bot_name = bot_name
        self._bot_emoji = bot_emoji

    async def send(
        self, chat_id: str, html_body: str,
        reply_to: Optional[str] = None,
    ) -> None:
        """Send an HTML message to a Teams chat.

        Note: Teams chat API does not support thread replies (only channel messages do).
        The reply_to parameter is accepted but currently unused — kept for future
        channel support.
        """
        html_body = f"{html_body}{_BOT_MARKER}"
        env = {**os.environ, "READ_WRITE_MODE": "1"}
        proc = await asyncio.create_subprocess_exec(
            "teams-cli", "chat", "send", chat_id,
            "--html", "--body", html_body,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            logger.warning("teams-cli send timed out after 30s for chat %s", chat_id)
            return
        if proc.returncode != 0:
            logger.error(
                "Failed to send Teams message (exit %d): %s",
                proc.returncode, stderr.decode().strip()[:200],
            )
            raise RuntimeError(f"teams-cli send failed: {stderr.decode().strip()}")

    async def send_processing(
        self, chat_id: str, session_id: str,
        reply_to: Optional[str] = None,
    ) -> None:
        await self.send(chat_id, format_processing(session_id, self._bot_name, self._bot_emoji), reply_to=reply_to)

    async def send_result(
        self, chat_id: str, session_id: str,
        result: Optional[str] = None, error: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> None:
        html = format_result(session_id, result, error, self._output_dir, self._bot_name, self._bot_emoji)
        await self.send(chat_id, html, reply_to=reply_to)

    async def send_text(
        self, chat_id: str, text: str,
        reply_to: Optional[str] = None,
    ) -> None:
        prefix = _make_prefix(self._bot_name, self._bot_emoji)
        body_html = _md_to_html(text)
        html = f"<p><b>{prefix}</b> {body_html}</p>" if "<p>" not in body_html else body_html.replace("<p>", f"<p><b>{prefix}</b> ", 1)
        await self.send(chat_id, html, reply_to=reply_to)
