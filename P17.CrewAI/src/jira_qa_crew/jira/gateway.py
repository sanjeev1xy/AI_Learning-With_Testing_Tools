"""Deterministic Jira provider selection.

The mode (auto / mcp / rest) and the MCP->REST fallback are pure application
logic. DEMO fixtures are a separate, explicitly-requested path and never an
automatic fallback for a failed live integration.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import AppConfig, get_config
from ..exceptions import (
    AllProvidersFailedError,
    JiraError,
    JiraNotFoundError,
    JiraProviderUnavailableError,
)
from ..logging_utils import get_logger
from .base import JiraIssue
from .fixtures import JiraFixtureProvider
from .mcp_provider import JiraMCPProvider
from .rest_provider import JiraRestProvider

logger = get_logger("jira.gateway")


@dataclass
class FetchOutcome:
    issue: JiraIssue
    provider: str  # 'MCP' | 'REST' | 'FIXTURE'
    demo: bool
    notes: list[str]


class JiraGateway:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._cfg = config or get_config()
        self._mcp = JiraMCPProvider(self._cfg.mcp)
        self._rest = JiraRestProvider(self._cfg.rest, timeout=float(self._cfg.mcp.timeout_seconds or 20))
        self._fixture = JiraFixtureProvider()

    # -- introspection ------------------------------------------------
    @property
    def demo_active(self) -> bool:
        return self._cfg.effective_demo_mode()

    def status(self) -> dict[str, bool]:
        return {
            "mcp_configured": self._cfg.mcp.configured,
            "rest_configured": self._cfg.rest.configured,
            "fixtures_available": self._fixture.health_check(),
            "demo_active": self.demo_active,
        }

    # -- fetch ------------------------------------------------------
    def fetch(self, key: str) -> FetchOutcome:
        mode = self._cfg.integration_mode
        notes: list[str] = []

        if self.demo_active:
            if self._fixture.has_fixture(key):
                logger.info("DEMO MODE active — serving %s from local fixture.", key)
                issue = self._fixture.fetch_issue(key)
                return FetchOutcome(
                    issue=issue, provider="FIXTURE", demo=True, notes=["DEMO MODE: local fixture data."]
                )
            if getattr(self._cfg, "demo_allow_synthetic", True):
                logger.warning("DEMO MODE — no fixture for %s; using a SYNTHETIC placeholder ticket.", key)
                issue = self._fixture.synthesize(key)
                return FetchOutcome(
                    issue=issue,
                    provider="FIXTURE",
                    demo=True,
                    notes=[
                        f"DEMO MODE: no fixture for {key}. Using a SYNTHETIC placeholder ticket "
                        "(clearly labelled, NOT live Jira data)."
                    ],
                )
            raise JiraNotFoundError(
                f"No demo fixture for '{key}'. Available: "
                f"{', '.join(self._fixture.available_keys()) or '(none)'}"
            )

        if mode == "mcp":
            return FetchOutcome(self._mcp.fetch_issue(key), "MCP", False, notes)

        if mode == "rest":
            return FetchOutcome(self._rest.fetch_issue(key), "REST", False, notes)

        # auto: MCP first, then REST.
        mcp_error: Exception | None = None
        if self._cfg.mcp.configured:
            try:
                issue = self._mcp.fetch_issue(key)
                return FetchOutcome(issue, "MCP", False, notes)
            except JiraError as exc:
                mcp_error = exc
                notes.append(f"MCP failed ({exc.__class__.__name__}): {exc}. Falling back to REST.")
                logger.warning("MCP fetch failed for %s: %s", key, exc)
        else:
            notes.append("MCP not configured; using REST.")

        if self._cfg.rest.configured:
            try:
                issue = self._rest.fetch_issue(key)
                return FetchOutcome(issue, "REST", False, notes)
            except JiraError as rest_error:
                raise AllProvidersFailedError(
                    f"Both Jira providers failed for {key}. MCP: {mcp_error}. REST: {rest_error}",
                    mcp_error=mcp_error,
                    rest_error=rest_error,
                ) from rest_error

        raise JiraProviderUnavailableError(
            f"No Jira provider is configured for {key}. Configure MCP or REST, or enable DEMO_MODE."
        )
