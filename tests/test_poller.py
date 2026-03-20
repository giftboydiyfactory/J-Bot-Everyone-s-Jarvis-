from __future__ import annotations

import json
import pytest
from pathlib import Path

from niuma.poller import Poller, TeamsMessage, TeamsCliError


def _make_messages(messages: list[dict]) -> str:
    """Simulate teams-cli chat read --json output."""
    return json.dumps({
        "success": True,
        "data": {"messages": messages},
        "metadata": {},
    })


@pytest.fixture
def poller(sample_config: dict) -> Poller:
    from niuma.config import load_config
    import yaml
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        path = Path(f.name)
    config = load_config(path)
    return Poller(config.teams)


def test_parse_messages(poller: Poller) -> None:
    raw = _make_messages([
        {
            "id": "msg-1",
            "from": {"user": {"displayName": "Jack", "email": "jack@nvidia.com"}},
            "body": {"content": "@niuma analyze this code"},
            "createdDateTime": "2026-03-19T10:00:00Z",
        },
        {
            "id": "msg-2",
            "from": {"user": {"displayName": "Alice", "email": "alice@nvidia.com"}},
            "body": {"content": "just a normal message"},
            "createdDateTime": "2026-03-19T10:01:00Z",
        },
    ])
    messages = poller.parse_messages(raw)
    assert len(messages) == 2
    assert messages[0].sender_email == "jack@nvidia.com"


def test_filter_triggered_messages(poller: Poller) -> None:
    messages = [
        TeamsMessage(id="1", sender="Jack", sender_email="j@n.com",
                     body="@niuma do stuff", timestamp="t1"),
        TeamsMessage(id="2", sender="Alice", sender_email="a@n.com",
                     body="normal chat", timestamp="t2"),
        TeamsMessage(id="3", sender="Bob", sender_email="b@n.com",
                     body="@niuma help me", timestamp="t3"),
    ]
    triggered = poller.filter_triggered(messages)
    assert len(triggered) == 2
    assert triggered[0].id == "1"
    assert triggered[1].id == "3"


def test_extract_prompt(poller: Poller) -> None:
    msg = TeamsMessage(id="1", sender="Jack", sender_email="j@n.com",
                       body="@niuma   analyze this code  ", timestamp="t1")
    prompt = poller.extract_prompt(msg)
    assert prompt == "analyze this code"


def test_filter_new_messages(poller: Poller) -> None:
    messages = [
        TeamsMessage(id="1", sender="J", sender_email="j@n.com", body="@niuma a", timestamp="t"),
        TeamsMessage(id="2", sender="J", sender_email="j@n.com", body="@niuma b", timestamp="t"),
        TeamsMessage(id="3", sender="J", sender_email="j@n.com", body="@niuma c", timestamp="t"),
    ]
    new = poller.filter_new(messages, last_seen_id="1")
    assert len(new) == 2
    assert new[0].id == "2"
