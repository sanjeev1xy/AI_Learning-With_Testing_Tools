"""Read-only CrewAI tool that exposes the deterministic JiraGateway.

The provider decision lives in :class:`JiraGateway`, not here and not in the LLM.
The tool is scoped to a single ticket key per crew run so a prompt-injection
attempt inside a Jira description cannot pull an unrelated ticket.
"""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..jira.base import JiraIssue
from ..jira.gateway import FetchOutcome, JiraGateway
from ..logging_utils import get_logger

logger = get_logger("tools.jira")


class _Args(BaseModel):
    issue_key: str = Field(description="The Jira issue key to fetch, e.g. VWO-48")


class FetchJiraIssueTool(BaseTool):
    name: str = "fetch_jira_issue"
    description: str = (
        "Fetch one Jira issue as plain text. Input: issue_key. Read-only. "
        "Returns key, summary, description, acceptance criteria and metadata."
    )
    args_schema: type[BaseModel] = _Args

    _gateway: JiraGateway
    _allowed_key: str
    _cache: dict[str, FetchOutcome]

    def __init__(self, gateway: JiraGateway, allowed_key: str, prefetched: FetchOutcome | None = None, **kw: Any):
        super().__init__(**kw)
        self._gateway = gateway
        self._allowed_key = allowed_key.upper()
        self._cache = {}
        if prefetched is not None:
            self._cache[self._allowed_key] = prefetched

    # -- provenance access for the pipeline -------------------------
    def last_outcome(self) -> FetchOutcome | None:
        return self._cache.get(self._allowed_key)

    def _run(self, issue_key: str) -> str:
        key = (issue_key or "").strip().upper()
        if key != self._allowed_key:
            return (
                f"ERROR: this crew is scoped to {self._allowed_key}. "
                f"Refusing to fetch a different ticket ({key or 'empty'})."
            )
        outcome = self._cache.get(key)
        if outcome is None:
            outcome = self._gateway.fetch(key)
            self._cache[key] = outcome
        issue: JiraIssue = outcome.issue
        header = f"[provider={outcome.provider}{' DEMO' if outcome.demo else ''}]"
        logger.info("Tool served %s %s", key, header)
        return f"{header}\n{issue.to_prompt_text()}"
