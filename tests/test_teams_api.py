"""Tests for niuma.teams_api — Graph API operations."""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, mock_open

import pytest

from niuma import teams_api


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_token_cache():
    """Reset in-memory token cache between tests."""
    teams_api._cached_token = ""
    teams_api._cached_token_expiry = 0
    yield
    teams_api._cached_token = ""
    teams_api._cached_token_expiry = 0


@pytest.fixture
def fake_token_file(tmp_path: Path) -> Path:
    """Create a fake token cache file with valid structure."""
    now = int(time.time())
    data = {
        "AccessToken": {
            "key1": {
                "secret": "fake-access-token-write",
                "expires_on": str(now + 3600),
                "client_id": "29c0325f-4dd7-fake",
            }
        },
        "RefreshToken": {
            "rt1": {
                "secret": "fake-refresh-token",
                "client_id": "29c0325f-4dd7-fake",
            }
        },
        "Account": {
            "acct1": {
                "realm": "43083d15-fake-tenant",
            }
        },
    }
    path = tmp_path / "token-cache"
    path.write_text(json.dumps(data))
    path.chmod(0o600)
    return path


@pytest.fixture
def expired_token_file(tmp_path: Path) -> Path:
    """Token cache with expired access token but valid refresh token."""
    now = int(time.time())
    data = {
        "AccessToken": {
            "key1": {
                "secret": "expired-token",
                "expires_on": str(now - 100),
                "client_id": "29c0325f-4dd7-fake",
            }
        },
        "RefreshToken": {
            "rt1": {
                "secret": "valid-refresh-token",
                "client_id": "29c0325f-4dd7-fake",
            }
        },
        "Account": {
            "acct1": {"realm": "43083d15-fake-tenant"}
        },
    }
    path = tmp_path / "token-cache-expired"
    path.write_text(json.dumps(data))
    path.chmod(0o600)
    return path


def _mock_urlopen(response_data: Any, status: int = 200):
    """Create a mock for urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.status = status
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# _get_access_token tests
# ---------------------------------------------------------------------------

class TestGetAccessToken:
    def test_returns_cached_token_when_valid(self):
        """In-memory cache should be returned without file read."""
        teams_api._cached_token = "cached-token"
        teams_api._cached_token_expiry = int(time.time()) + 3600

        result = teams_api._get_access_token()
        assert result == "cached-token"

    def test_reads_from_file_when_cache_expired(self, fake_token_file: Path):
        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file):
            token = teams_api._get_access_token()
        assert token == "fake-access-token-write"

    def test_raises_when_no_cache_file(self, tmp_path: Path):
        missing = tmp_path / "nonexistent"
        with patch.object(teams_api, "_TOKEN_CACHE", missing):
            with pytest.raises(RuntimeError, match="Token cache not found"):
                teams_api._get_access_token()

    def test_prefers_write_client(self, tmp_path: Path):
        """Should prefer the write-capable client (29c0325f) over others."""
        now = int(time.time())
        data = {
            "AccessToken": {
                "readonly": {
                    "secret": "readonly-token",
                    "expires_on": str(now + 3600),
                    "client_id": "aaaaaaaa-read-only",
                },
                "writecap": {
                    "secret": "write-token",
                    "expires_on": str(now + 3600),
                    "client_id": "29c0325f-4dd7-write",
                },
            },
            "RefreshToken": {},
            "Account": {},
        }
        path = tmp_path / "multi-token"
        path.write_text(json.dumps(data))
        path.chmod(0o600)

        with patch.object(teams_api, "_TOKEN_CACHE", path):
            token = teams_api._get_access_token()
        assert token == "write-token"

    def test_refreshes_when_access_expired(self, expired_token_file: Path):
        """Should use refresh token when access token is expired."""
        refresh_response = {
            "access_token": "fresh-token-from-refresh",
            "expires_in": 3600,
        }
        mock_resp = _mock_urlopen(refresh_response)

        with patch.object(teams_api, "_TOKEN_CACHE", expired_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            token = teams_api._get_access_token()
        assert token == "fresh-token-from-refresh"

    def test_raises_when_no_refresh_token(self, tmp_path: Path):
        """Should raise when access expired and no refresh token available."""
        now = int(time.time())
        data = {
            "AccessToken": {
                "k": {"secret": "x", "expires_on": str(now - 100), "client_id": "29c0325f-x"}
            },
            "RefreshToken": {},
            "Account": {"a": {"realm": "tenant"}},
        }
        path = tmp_path / "no-rt"
        path.write_text(json.dumps(data))
        path.chmod(0o600)

        with patch.object(teams_api, "_TOKEN_CACHE", path):
            with pytest.raises(RuntimeError, match="no refresh token"):
                teams_api._get_access_token()

    def test_fixes_permissive_file_permissions(self, fake_token_file: Path):
        """Should auto-fix world-readable permissions."""
        fake_token_file.chmod(0o644)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file):
            teams_api._get_access_token()

        import stat
        mode = fake_token_file.stat().st_mode
        assert not (mode & stat.S_IRGRP), "Group read should be removed"
        assert not (mode & stat.S_IROTH), "Other read should be removed"


class TestForceRefresh:
    def test_clears_cache_and_calls_get(self, fake_token_file: Path):
        teams_api._cached_token = "old"
        teams_api._cached_token_expiry = int(time.time()) + 9999

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file):
            token = teams_api.force_refresh()
        assert token == "fake-access-token-write"
        # Cache should now be the new token, not "old"
        assert teams_api._cached_token == "fake-access-token-write"


# ---------------------------------------------------------------------------
# _graph_post_sync / _graph_get_sync tests
# ---------------------------------------------------------------------------

class TestGraphPost:
    def test_sends_json_body(self, fake_token_file: Path):
        response = {"id": "msg-123", "body": {"content": "ok"}}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            result = teams_api._graph_post_sync("/test/endpoint", {"key": "val"})

        assert result["id"] == "msg-123"
        call_args = mock_url.call_args
        req = call_args[0][0]
        assert req.full_url == "https://graph.microsoft.com/v1.0/test/endpoint"
        assert req.get_header("Content-type") == "application/json"

    def test_raises_on_http_error(self, fake_token_file: Path):
        import urllib.error
        error = urllib.error.HTTPError(
            url="https://graph.microsoft.com/v1.0/test",
            code=403, msg="Forbidden", hdrs={}, fp=MagicMock(read=lambda: b"forbidden")
        )
        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", side_effect=error):
            with pytest.raises(RuntimeError, match="Graph API error 403"):
                teams_api._graph_post_sync("/test", {})


class TestGraphGet:
    def test_basic_get(self, fake_token_file: Path):
        response = {"value": [{"id": "1"}, {"id": "2"}]}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            result = teams_api._graph_get_sync("/me/chats")

        assert result["value"][0]["id"] == "1"

    def test_appends_query_params(self, fake_token_file: Path):
        mock_resp = _mock_urlopen({"value": []})

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            teams_api._graph_get_sync("/me/chats", {"$top": "5", "$orderby": "name"})

        req = mock_url.call_args[0][0]
        assert "%24top=5" in req.full_url
        assert "%24orderby=name" in req.full_url


# ---------------------------------------------------------------------------
# High-level operation tests
# ---------------------------------------------------------------------------

class TestSendChatMessage:
    def test_sends_html_message(self, fake_token_file: Path):
        response = {"id": "msg-sent-1"}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            result = teams_api.send_chat_message_sync(
                chat_id="19:test@thread.v2",
                html_body="<p>Hello</p>",
            )

        assert result["id"] == "msg-sent-1"
        req = mock_url.call_args[0][0]
        body = json.loads(req.data)
        assert body["body"]["contentType"] == "html"
        assert body["body"]["content"] == "<p>Hello</p>"


class TestListChats:
    def test_returns_chat_list(self, fake_token_file: Path):
        response = {"value": [
            {"id": "chat-1", "chatType": "group", "topic": "Test"},
            {"id": "chat-2", "chatType": "oneOnOne"},
        ]}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            chats = teams_api.list_chats_sync(limit=10)

        assert len(chats) == 2
        assert chats[0]["id"] == "chat-1"


class TestReadChatMessages:
    def test_returns_messages(self, fake_token_file: Path):
        response = {"value": [
            {"id": "m1", "body": {"content": "Hello"}},
            {"id": "m2", "body": {"content": "World"}},
        ]}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            msgs = teams_api.read_chat_messages_sync(
                chat_id="19:test@thread.v2", limit=5,
            )

        assert len(msgs) == 2
        assert msgs[0]["id"] == "m1"


class TestReadEmails:
    def test_returns_emails(self, fake_token_file: Path):
        response = {"value": [
            {"id": "e1", "subject": "Hello", "isRead": False},
        ]}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            emails = teams_api.read_emails_sync(folder="inbox", limit=5)

        assert len(emails) == 1
        assert emails[0]["subject"] == "Hello"

    def test_unread_filter(self, fake_token_file: Path):
        mock_resp = _mock_urlopen({"value": []})

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            teams_api.read_emails_sync(unread_only=True)

        req = mock_url.call_args[0][0]
        assert "isRead" in req.full_url

    def test_search_param(self, fake_token_file: Path):
        mock_resp = _mock_urlopen({"value": []})

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            teams_api.read_emails_sync(search="urgent")

        req = mock_url.call_args[0][0]
        assert "urgent" in req.full_url


class TestReadEmailBody:
    def test_returns_full_body(self, fake_token_file: Path):
        response = {
            "id": "e1",
            "subject": "Test",
            "body": {"contentType": "html", "content": "<p>Full body</p>"},
        }
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            result = teams_api.read_email_body_sync(message_id="e1")

        assert result["body"]["content"] == "<p>Full body</p>"


class TestReadCalendar:
    def test_returns_events(self, fake_token_file: Path):
        response = {"value": [
            {"id": "ev1", "subject": "Standup", "start": {"dateTime": "2026-04-05T09:00:00"}},
        ]}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            events = teams_api.read_calendar_sync(
                start="2026-04-05T00:00:00Z",
                end="2026-04-05T23:59:59Z",
            )

        assert len(events) == 1
        assert events[0]["subject"] == "Standup"


class TestCreateDraft:
    def test_creates_email_draft(self, fake_token_file: Path):
        response = {"id": "draft-1", "subject": "Test"}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            result = teams_api.create_draft_sync(
                subject="Test Draft",
                to=["user@nvidia.com"],
                html_body="<p>Draft body</p>",
            )

        assert result["id"] == "draft-1"
        req = mock_url.call_args[0][0]
        body = json.loads(req.data)
        assert body["subject"] == "Test Draft"
        assert body["toRecipients"][0]["emailAddress"]["address"] == "user@nvidia.com"

    def test_includes_cc(self, fake_token_file: Path):
        mock_resp = _mock_urlopen({"id": "d2"})

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            teams_api.create_draft_sync(
                subject="With CC",
                to=["a@nvidia.com"],
                html_body="<p>body</p>",
                cc=["b@nvidia.com", "c@nvidia.com"],
            )

        body = json.loads(mock_url.call_args[0][0].data)
        assert len(body["ccRecipients"]) == 2


class TestSendEmail:
    def test_sends_immediately(self, fake_token_file: Path):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b""

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            teams_api.send_email_sync(
                subject="Urgent",
                to=["user@nvidia.com"],
                html_body="<p>Send now</p>",
            )

        req = mock_url.call_args[0][0]
        assert "sendMail" in req.full_url
        body = json.loads(req.data)
        assert "message" in body


class TestCreateCalendarEvent:
    def test_creates_event(self, fake_token_file: Path):
        response = {"id": "ev-new", "subject": "Meeting"}
        mock_resp = _mock_urlopen(response)

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            result = teams_api.create_calendar_event_sync(
                subject="Team Sync",
                start="2026-04-10T10:00:00",
                end="2026-04-10T11:00:00",
                attendees=["a@nvidia.com"],
            )

        assert result["id"] == "ev-new"
        body = json.loads(mock_url.call_args[0][0].data)
        assert body["subject"] == "Team Sync"
        assert body["isOnlineMeeting"] is True
        assert len(body["attendees"]) == 1


class TestCreateSessionChat:
    def test_creates_group_chat(self, fake_token_file: Path):
        me_resp = _mock_urlopen({"id": "user-id-123", "displayName": "Test"})
        chat_resp = _mock_urlopen({"id": "19:new@thread.v2", "webUrl": "https://teams.microsoft.com/..."})

        call_count = [0]
        def mock_urlopen_side_effect(req, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return me_resp
            return chat_resp

        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", side_effect=mock_urlopen_side_effect):
            result = teams_api.create_session_chat(
                session_id="sess-1",
                topic="J-Bot Session",
                user_email="test@nvidia.com",
            )

        assert result["chat_id"] == "19:new@thread.v2"


class TestDownloadHostedContent:
    def test_downloads_to_file(self, fake_token_file: Path, tmp_path: Path):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"\x89PNG\r\n\x1a\nfake image data"

        dest = tmp_path / "image.png"
        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            ok = teams_api.download_hosted_content_sync(
                "https://graph.microsoft.com/v1.0/chats/c/messages/m/hostedContents/hc/$value",
                str(dest),
            )

        assert ok is True
        assert dest.exists()
        assert b"PNG" in dest.read_bytes()

    def test_returns_false_on_error(self, fake_token_file: Path, tmp_path: Path):
        with patch.object(teams_api, "_TOKEN_CACHE", fake_token_file), \
             patch("urllib.request.urlopen", side_effect=Exception("network error")):
            ok = teams_api.download_hosted_content_sync(
                "https://graph.microsoft.com/v1.0/bad/url",
                str(tmp_path / "nope.png"),
            )
        assert ok is False
