#!/usr/bin/env python3
"""Poll Teams chats via Graph API with auto token refresh.

Replaces teams-cli for polling — no interactive auth needed.
Uses the same token cache + refresh logic as J-Bot's teams_api.py.

Usage:
    python3 scripts/jbot-poll.py <chat_id> [--limit N] [--json]
"""
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

_TOKEN_CACHE = Path.home() / ".ai-pim-utils" / "token-cache-ai-pim-utils"
_cached_token = ""
_cached_token_expiry = 0


def _get_access_token() -> str:
    """Read/refresh access token from ai-pim-utils cache."""
    global _cached_token, _cached_token_expiry
    now = int(time.time())

    if _cached_token and _cached_token_expiry > now + 60:
        return _cached_token

    if not _TOKEN_CACHE.exists():
        print("ERROR: Token cache not found. Run 'teams-cli auth login' first.", file=sys.stderr)
        sys.exit(2)

    with open(_TOKEN_CACHE) as f:
        data = json.load(f)

    # Look for valid access token (prefer write-capable client 29c0325f)
    _WRITE_CLIENT = "29c0325f"
    write_token = None
    for _key, entry in data.get("AccessToken", {}).items():
        if int(entry.get("expires_on", 0)) > now:
            cid = entry.get("client_id") or entry.get("clientId", "")
            if cid.startswith(_WRITE_CLIENT):
                write_token = entry
                break

    if write_token:
        _cached_token = write_token["secret"]
        _cached_token_expiry = int(write_token.get("expires_on", 0))
        return _cached_token

    # No valid token — refresh using refresh token
    refresh_token = None
    client_id = None
    tenant_id = None

    for _key, rt_entry in data.get("RefreshToken", {}).items():
        rt = rt_entry.get("secret")
        cid = rt_entry.get("client_id") or rt_entry.get("clientId")
        if rt and cid and cid.startswith(_WRITE_CLIENT):
            refresh_token = rt
            client_id = cid
            break

    for _key, acct in data.get("Account", {}).items():
        realm = acct.get("realm")
        if realm and realm != "common":
            tenant_id = realm
            break

    if not refresh_token or not client_id or not tenant_id:
        print("ERROR: Cannot refresh token. Run 'teams-cli auth login'.", file=sys.stderr)
        sys.exit(2)

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    post_data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default offline_access",
    }).encode()

    req = urllib.request.Request(token_url, data=post_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        token_response = json.loads(resp.read())
        new_token = token_response.get("access_token")
        if not new_token:
            print("ERROR: Refresh response missing access_token.", file=sys.stderr)
            sys.exit(2)

        # Update file cache so teams-cli also benefits
        new_rt = token_response.get("refresh_token")
        if new_rt:
            _update_token_cache(data, new_token, new_rt, client_id, tenant_id, token_response)

        _cached_token = new_token
        _cached_token_expiry = now + int(token_response.get("expires_in", 3600))
        logger.info("Token refreshed successfully.")
        return _cached_token
    except Exception as exc:
        print(f"ERROR: Token refresh failed: {exc}", file=sys.stderr)
        sys.exit(2)


def _update_token_cache(data, access_token, refresh_token, client_id, tenant_id, token_response):
    """Update the file-based token cache so teams-cli also gets the refreshed token."""
    now = int(time.time())
    expires_in = int(token_response.get("expires_in", 3600))

    # Update AccessToken entries for this client
    for key, entry in list(data.get("AccessToken", {}).items()):
        cid = entry.get("client_id") or entry.get("clientId", "")
        if cid.startswith(client_id[:8]):
            entry["secret"] = access_token
            entry["expires_on"] = str(now + expires_in)

    # Update RefreshToken entries for this client
    for key, entry in list(data.get("RefreshToken", {}).items()):
        cid = entry.get("client_id") or entry.get("clientId", "")
        if cid.startswith(client_id[:8]):
            entry["secret"] = refresh_token

    try:
        with open(_TOKEN_CACHE, "w") as f:
            json.dump(data, f)
        os.chmod(str(_TOKEN_CACHE), 0o600)
    except Exception as exc:
        logger.warning("Failed to update token cache file: %s", exc)


def read_chat_messages(chat_id, limit=5):
    """Read recent messages from a Teams chat via Graph API."""
    token = _get_access_token()
    url = f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages?$top={limit}&$orderby=createdDateTime%20desc"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return data.get("value", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        print(f"ERROR: Graph API {e.code}: {error_body}", file=sys.stderr)
        return []


def format_message(msg: dict) -> dict:
    """Extract key fields from a Graph API message."""
    from_user = msg.get("from", {}).get("user", {})
    body = msg.get("body", {})
    return {
        "id": msg.get("id", ""),
        "createdDateTime": msg.get("createdDateTime", ""),
        "sender": from_user.get("displayName", "Unknown"),
        "contentType": body.get("contentType", ""),
        "content": body.get("content", ""),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Poll Teams chat via Graph API")
    parser.add_argument("chat_id", help="Teams chat ID")
    parser.add_argument("--limit", type=int, default=5, help="Number of messages")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    messages = read_chat_messages(args.chat_id, args.limit)

    if args.json:
        print(json.dumps({"data": [format_message(m) for m in messages]}, indent=2))
    else:
        for msg in messages:
            fm = format_message(msg)
            # Strip HTML tags for display
            import re
            text = re.sub(r'<[^>]+>', ' ', fm["content"]).strip()[:200]
            print(f'[{fm["createdDateTime"]}] {fm["sender"]}: {text}')


if __name__ == "__main__":
    main()
