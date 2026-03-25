# tests/test_responder.py
from __future__ import annotations

import pytest

from niuma.responder import format_result, format_processing


def test_format_result_short() -> None:
    html = format_result(session_id="a3f7", result="Analysis complete.")
    assert "a3f7" in html
    assert "Analysis complete." in html


def test_format_result_truncated() -> None:
    long_result = "x" * 3000
    html = format_result(session_id="a3f7", result=long_result)
    assert "truncated" in html.lower() or "output saved" in html.lower()
    assert len(html) < 3000


def test_format_result_error() -> None:
    html = format_result(session_id="a3f7", result=None, error="Claude crashed")
    assert "a3f7" in html
    assert "Claude crashed" in html


def test_format_processing() -> None:
    html = format_processing(session_id="a3f7")
    assert "a3f7" in html
