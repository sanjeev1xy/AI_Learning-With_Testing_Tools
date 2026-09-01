"""Provider-neutral Jira issue representation and the provider interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class JiraIssue:
    """Normalised Jira issue. ``source`` is 'MCP', 'REST' or 'FIXTURE'."""

    key: str
    summary: str = ""
    description: str = ""
    issue_type: str = ""
    status: str = ""
    priority: str = ""
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    parent: str = ""
    subtasks: list[str] = field(default_factory=list)
    linked_issues: list[str] = field(default_factory=list)
    acceptance_criteria: str = ""
    comments: list[str] = field(default_factory=list)
    url: str = ""
    source: str = "REST"
    raw_excerpt: str = ""

    def to_prompt_text(self) -> str:
        """A compact, LLM-friendly rendering. Contains only Jira business data."""
        parts = [
            f"JIRA KEY: {self.key}",
            f"SOURCE: {self.source}",
            f"SUMMARY: {self.summary}",
            f"ISSUE TYPE: {self.issue_type}",
            f"STATUS: {self.status}",
            f"PRIORITY: {self.priority}",
            f"LABELS: {', '.join(self.labels) or '(none)'}",
            f"COMPONENTS: {', '.join(self.components) or '(none)'}",
            f"PARENT: {self.parent or '(none)'}",
            f"SUBTASKS: {', '.join(self.subtasks) or '(none)'}",
            f"LINKED ISSUES: {', '.join(self.linked_issues) or '(none)'}",
            f"URL: {self.url or '(none)'}",
            "",
            "DESCRIPTION:",
            self.description or "(empty)",
        ]
        if self.acceptance_criteria:
            parts += ["", "ACCEPTANCE CRITERIA FIELD:", self.acceptance_criteria]
        if self.comments:
            parts += ["", "COMMENTS:"] + [f"- {c}" for c in self.comments]
        return "\n".join(parts)


class JiraProvider(abc.ABC):
    name: str = "provider"

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider looks usable. Must not raise."""

    @abc.abstractmethod
    def fetch_issue(self, key: str) -> JiraIssue:
        """Fetch a single issue or raise a typed :class:`JiraError`."""
