from __future__ import annotations

import pytest

from jira_qa_crew.config import reload_config
from jira_qa_crew.exceptions import AllProvidersFailedError, JiraTransportError
from jira_qa_crew.jira.base import JiraIssue
from jira_qa_crew.jira.gateway import JiraGateway


def _issue(source: str) -> JiraIssue:
    return JiraIssue(key="VWO-48", summary="s", description="d", source=source)


@pytest.fixture
def live_config(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("JIRA_URL", "https://x.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "a@b.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "tok")
    monkeypatch.setenv("JIRA_MCP_URL", "https://mcp.example/mcp")
    monkeypatch.setenv("JIRA_INTEGRATION_MODE", "auto")
    return reload_config()


def test_demo_mode_uses_fixture(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.delenv("JIRA_URL", raising=False)
    monkeypatch.delenv("JIRA_MCP_URL", raising=False)
    cfg = reload_config()
    gw = JiraGateway(cfg)
    out = gw.fetch("VWO-48")
    assert out.provider == "FIXTURE"
    assert out.demo is True
    assert out.issue.source == "FIXTURE"


def test_demo_synthesizes_when_no_fixture(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DEMO_ALLOW_SYNTHETIC", "true")
    monkeypatch.delenv("JIRA_URL", raising=False)
    monkeypatch.delenv("JIRA_MCP_URL", raising=False)
    cfg = reload_config()
    out = JiraGateway(cfg).fetch("ZZZ-999")
    assert out.provider == "FIXTURE"
    assert out.demo is True
    assert "SYNTHETIC" in out.issue.summary.upper()
    assert any("SYNTHETIC" in n.upper() for n in out.notes)


def test_demo_no_synthetic_when_disabled(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DEMO_ALLOW_SYNTHETIC", "false")
    monkeypatch.delenv("JIRA_URL", raising=False)
    cfg = reload_config()
    with pytest.raises(Exception, match="No demo fixture"):
        JiraGateway(cfg).fetch("ZZZ-999")


def test_auto_falls_back_mcp_to_rest(live_config, monkeypatch):
    gw = JiraGateway(live_config)
    monkeypatch.setattr(gw._mcp, "fetch_issue", lambda k: (_ for _ in ()).throw(JiraTransportError("mcp down")))
    monkeypatch.setattr(gw._rest, "fetch_issue", lambda k: _issue("REST"))
    out = gw.fetch("VWO-48")
    assert out.provider == "REST"
    assert any("MCP failed" in n for n in out.notes)


def test_auto_mcp_success(live_config, monkeypatch):
    gw = JiraGateway(live_config)
    monkeypatch.setattr(gw._mcp, "fetch_issue", lambda k: _issue("MCP"))
    out = gw.fetch("VWO-48")
    assert out.provider == "MCP"


def test_both_providers_fail(live_config, monkeypatch):
    gw = JiraGateway(live_config)
    monkeypatch.setattr(gw._mcp, "fetch_issue", lambda k: (_ for _ in ()).throw(JiraTransportError("mcp")))
    monkeypatch.setattr(gw._rest, "fetch_issue", lambda k: (_ for _ in ()).throw(JiraTransportError("rest")))
    with pytest.raises(AllProvidersFailedError):
        gw.fetch("VWO-48")


def test_no_silent_demo_fallback_when_live_fails(live_config, monkeypatch):
    """A failed live integration must NOT silently return fixture data."""
    gw = JiraGateway(live_config)
    monkeypatch.setattr(gw._mcp, "fetch_issue", lambda k: (_ for _ in ()).throw(JiraTransportError("mcp")))
    monkeypatch.setattr(gw._rest, "fetch_issue", lambda k: (_ for _ in ()).throw(JiraTransportError("rest")))
    with pytest.raises(AllProvidersFailedError):
        gw.fetch("VWO-48")
    assert gw.demo_active is False


def test_rest_surfaces_suspended_site(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("JIRA_URL", "https://x.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "a@b.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "tok")
    monkeypatch.setenv("JIRA_INTEGRATION_MODE", "rest")
    cfg = reload_config()

    class _Resp:
        status_code = 503

        @staticmethod
        def json():
            return {"errorMessage": "Your Jira Cloud subscription has been deactivated due to inactivity",
                    "errorCode": "SUSPENDED_INACTIVITY"}

    from jira_qa_crew.exceptions import JiraTransportError
    from jira_qa_crew.jira.rest_provider import JiraRestProvider

    prov = JiraRestProvider(cfg.rest)
    monkeypatch.setattr(prov._session, "get", lambda *a, **k: _Resp())
    with pytest.raises(JiraTransportError, match="suspended for inactivity"):
        prov.fetch_issue("KAN-5")


def test_rest_only_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("JIRA_URL", "https://x.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "a@b.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "tok")
    monkeypatch.setenv("JIRA_INTEGRATION_MODE", "rest")
    cfg = reload_config()
    gw = JiraGateway(cfg)
    monkeypatch.setattr(gw._rest, "fetch_issue", lambda k: _issue("REST"))
    assert gw.fetch("VWO-48").provider == "REST"
