# src/niuma/teams_api.py
"""Direct Microsoft Graph API calls for Teams operations not supported by teams-cli."""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_TOKEN_CACHE = Path.home() / ".ai-pim-utils" / "token-cache-ai-pim-utils"

# Thread-safe in-memory cache for refreshed tokens (RLock = reentrant, avoids deadlock)
_token_lock = threading.RLock()
_cached_token: str = ""
_cached_token_expiry: int = 0


def force_refresh() -> str:
    """Force-refresh the token (thread-safe). Used by proactive refresh."""
    with _token_lock:
        global _cached_token, _cached_token_expiry
        _cached_token = ""
        _cached_token_expiry = 0
        return _get_access_token()


def _get_access_token() -> str:
    """Read a valid access token from the shared ai-pim-utils token cache.

    If no valid (non-expired) access token is found, attempts to use a refresh
    token from the cache to obtain a new access token via the OAuth token endpoint.
    If refresh fails, logs a clear error directing the user to re-authenticate.

    Thread-safe: uses _token_lock for cache reads/writes.
    """
    global _cached_token, _cached_token_expiry
    now = int(time.time())

    with _token_lock:
        if _cached_token and _cached_token_expiry > now + 60:
            return _cached_token

    if not _TOKEN_CACHE.exists():
        raise RuntimeError("Token cache not found. Run 'READ_WRITE_MODE=1 teams-cli auth login' first.")

    # Auto-fix permissive permissions on token cache
    import stat as _stat
    _mode = _TOKEN_CACHE.stat().st_mode
    if _mode & (_stat.S_IRGRP | _stat.S_IROTH):
        logger.warning("Fixing permissive permissions on token cache %s", _TOKEN_CACHE)
        _TOKEN_CACHE.chmod(0o600)

    with open(_TOKEN_CACHE) as f:
        data = json.load(f)

    # Check file cache for a valid access token
    for _key, token_entry in data.get("AccessToken", {}).items():
        if int(token_entry.get("expires_on", 0)) > now:
            with _token_lock:
                _cached_token = token_entry["secret"]
                _cached_token_expiry = int(token_entry.get("expires_on", 0))
            return _cached_token

    # No valid access token found — try to refresh using a refresh token
    logger.warning("Access token expired. Attempting to refresh using refresh token...")
    refresh_token = None
    client_id = None
    tenant_id = None

    # Prefer write-capable OAuth client (Microsoft "Office Desktop" — has Chat.ReadWrite scope)
    _WRITE_CAPABLE_CLIENT_PREFIX = "29c0325f"
    fallback_rt = None
    fallback_cid = None
    for _key, rt_entry in data.get("RefreshToken", {}).items():
        rt = rt_entry.get("secret")
        cid = rt_entry.get("client_id") or rt_entry.get("clientId")
        if rt and cid:
            if cid.startswith(_WRITE_CAPABLE_CLIENT_PREFIX):
                refresh_token = rt
                client_id = cid
                break
            elif not fallback_rt:
                fallback_rt = rt
                fallback_cid = cid

    if not refresh_token:
        refresh_token = fallback_rt
        client_id = fallback_cid

    # Try to get tenant from Account or token entry metadata
    for _key, acct in data.get("Account", {}).items():
        realm = acct.get("realm")
        if realm and realm != "common":
            tenant_id = realm
            break

    if not refresh_token:
        logger.error(
            "No refresh token found in cache. Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate."
        )
        raise RuntimeError(
            "Access token expired and no refresh token available. "
            "Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate."
        )

    if not client_id or not tenant_id:
        logger.error(
            "Cannot refresh token: missing client_id or tenant_id in cache. "
            "Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate."
        )
        raise RuntimeError(
            "Access token expired. Could not find client_id/tenant_id for refresh. "
            "Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate."
        )

    try:
        import urllib.parse
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        post_data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "scope": "https://graph.microsoft.com/.default offline_access",
        }).encode()

        req = urllib.request.Request(token_url, data=post_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        resp = urllib.request.urlopen(req, timeout=15)
        token_response = json.loads(resp.read())
        new_access_token = token_response.get("access_token")
        if not new_access_token:
            raise RuntimeError("Token refresh response missing access_token")
        # Cache in memory (token typically valid for 1 hour)
        with _token_lock:
            _cached_token = new_access_token
            _cached_token_expiry = now + 3600
        logger.info("Successfully refreshed access token via refresh token.")
        return new_access_token
    except Exception as exc:
        logger.error(
            "Token refresh failed: %s. Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate.", exc
        )
        raise RuntimeError(
            f"Access token expired and refresh failed: {exc}. "
            "Run 'READ_WRITE_MODE=1 teams-cli auth login' to re-authenticate."
        ) from exc


def _graph_post_sync(endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    """Make a POST request to Microsoft Graph API (synchronous, run via asyncio.to_thread)."""
    token = _get_access_token()
    url = f"https://graph.microsoft.com/v1.0{endpoint}"
    data = json.dumps(body).encode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        logger.error("Graph API error %d: %s", e.code, error_body)
        raise RuntimeError(f"Graph API error {e.code}: {error_body}")


def _get_me_sync() -> dict[str, Any]:
    """Fetch current user info from Graph API (synchronous, run via asyncio.to_thread)."""
    token = _get_access_token()
    req = urllib.request.Request("https://graph.microsoft.com/v1.0/me")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:300]
        raise RuntimeError(f"Graph /me failed ({e.code}): {error_body}")


def create_session_chat(
    *,
    session_id: str,
    topic: str,
    user_email: str,
) -> dict[str, str]:
    """Create a dedicated group chat for a J-Bot session (synchronous).

    Returns dict with 'chat_id' and 'web_url'.
    Call via asyncio.to_thread() from async contexts.
    """
    chat_topic = topic

    # Use 'me' endpoint to get current user's ID for self-chats
    # when user_email might be a displayName instead of email
    me = _get_me_sync()
    user_id = me["id"]

    result = _graph_post_sync("/chats", {
        "chatType": "group",
        "topic": chat_topic,
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{user_id}",
            }
        ],
    })

    return {
        "chat_id": result["id"],
        "web_url": result.get("webUrl", ""),
        "topic": chat_topic,
    }


async def create_session_chat_async(
    *,
    session_id: str,
    topic: str,
    user_email: str,
) -> dict[str, str]:
    """Async wrapper for create_session_chat using asyncio.to_thread."""
    return await asyncio.to_thread(
        create_session_chat,
        session_id=session_id,
        topic=topic,
        user_email=user_email,
    )


def add_chat_member(*, chat_id: str, user_email: str) -> None:
    """Add a user to an existing group chat via Graph API."""
    token = _get_access_token()
    body = {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": ["owner"],
        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{user_email}",
    }
    _graph_post_sync(f"/chats/{chat_id}/members", body)


async def add_chat_member_async(*, chat_id: str, user_email: str) -> None:
    """Async wrapper for add_chat_member."""
    await asyncio.to_thread(add_chat_member, chat_id=chat_id, user_email=user_email)


def send_chat_message_sync(*, chat_id: str, html_body: str) -> dict[str, Any]:
    """Send an HTML message to a Teams chat via Graph API (no teams-cli needed).

    Uses the same token cache and refresh logic as other Graph API calls.
    Eliminates dependency on teams-cli write mode auth.
    """
    result = _graph_post_sync(f"/chats/{chat_id}/messages", {
        "body": {
            "contentType": "html",
            "content": html_body,
        }
    })
    return result


async def send_chat_message_async(*, chat_id: str, html_body: str) -> dict[str, Any]:
    """Async wrapper for send_chat_message_sync."""
    return await asyncio.to_thread(
        send_chat_message_sync, chat_id=chat_id, html_body=html_body,
    )
