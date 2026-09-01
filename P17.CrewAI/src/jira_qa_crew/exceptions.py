"""Typed exceptions for the Jira QA Crew pipeline."""

from __future__ import annotations


class JiraQACrewError(Exception):
    """Base class for all application errors."""


class ConfigurationError(JiraQACrewError):
    """Raised when required configuration is missing or invalid."""


class TicketInputError(JiraQACrewError):
    """Raised when the user-supplied ticket input cannot be parsed."""


class JiraError(JiraQACrewError):
    """Base class for Jira provider failures."""


class JiraAuthError(JiraError):
    """Authentication or permission failure talking to Jira."""


class JiraNotFoundError(JiraError):
    """The requested issue does not exist or is not visible."""


class JiraRateLimitError(JiraError):
    """Jira returned HTTP 429 / rate limit."""


class JiraTransportError(JiraError):
    """Network, timeout or malformed-response failure."""


class JiraProviderUnavailableError(JiraError):
    """A provider is disabled or not configured for the requested mode."""


class AllProvidersFailedError(JiraError):
    """Both MCP and REST providers failed in auto mode."""

    def __init__(self, message: str, mcp_error: Exception | None = None, rest_error: Exception | None = None) -> None:
        super().__init__(message)
        self.mcp_error = mcp_error
        self.rest_error = rest_error


class PipelineError(JiraQACrewError):
    """Raised when a CrewAI stage fails irrecoverably."""


class ValidationFailedError(JiraQACrewError):
    """Deterministic post-stage validation failed."""

    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = problems or []
