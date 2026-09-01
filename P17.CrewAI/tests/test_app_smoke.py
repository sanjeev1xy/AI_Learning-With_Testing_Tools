"""Streamlit AppTest smoke tests — initial render and validation feedback."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _app(monkeypatch) -> AppTest:
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("LLM_MODEL", "openai/test-model")
    monkeypatch.setenv("LLM_API_KEY", "k")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")
    return AppTest.from_file(APP, default_timeout=30)


def test_initial_render(monkeypatch):
    at = _app(monkeypatch).run()
    assert not at.exception
    assert any("Jira QA Crew" in t.value for t in at.title)
    # DEMO MODE banner present
    assert any("DEMO MODE" in w.value for w in at.warning)


def test_invalid_ticket_feedback(monkeypatch):
    at = _app(monkeypatch).run()
    at.text_area(key="ticket_input").set_value("not-a-ticket").run()
    assert any("Ignored" in w.value for w in at.warning)


def test_valid_ticket_enables_button(monkeypatch):
    at = _app(monkeypatch).run()
    at.text_area(key="ticket_input").set_value("VWO-48").run()
    assert any("VWO-48" in s.value for s in at.success)
    btns = [b for b in at.button if "Analyze" in b.label]
    assert btns and btns[0].disabled is False


@pytest.mark.skip(reason="Full run exercised by run_demo.py against the real LLM.")
def test_full_run(monkeypatch):  # pragma: no cover
    ...
