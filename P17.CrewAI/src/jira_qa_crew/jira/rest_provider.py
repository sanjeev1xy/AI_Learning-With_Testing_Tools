"""Jira Cloud REST API v3 provider (fallback path)."""

from __future__ import annotations

import time

import requests

from ..config import JiraRestConfig
from ..exceptions import (
    JiraAuthError,
    JiraNotFoundError,
    JiraProviderUnavailableError,
    JiraRateLimitError,
    JiraTransportError,
)
from ..logging_utils import get_logger, redact
from .adf import adf_to_text
from .base import JiraIssue, JiraProvider

logger = get_logger("jira.rest")

_TRANSIENT = {429, 500, 502, 503, 504}
_RETRY_BACKOFF = (1.0, 2.0, 4.0, 8.0, 12.0)


def _atlassian_error(resp) -> tuple[str, str]:
    """Best-effort extraction of Atlassian's error message / code from a response."""
    try:
        body = resp.json()
    except ValueError:
        return (resp.text or "")[:200], ""
    if isinstance(body, dict):
        msg = body.get("errorMessage") or "; ".join(body.get("errorMessages", []) or [])
        if not msg and isinstance(body.get("errors"), dict):
            msg = "; ".join(f"{k}: {v}" for k, v in body["errors"].items())
        return str(msg or "")[:300], str(body.get("errorCode", ""))
    return str(body)[:200], ""


class JiraRestProvider(JiraProvider):
    name = "REST"

    def __init__(self, config: JiraRestConfig, timeout: float = 20.0) -> None:
        self._cfg = config
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json", "User-Agent": "jira-qa-crew/1.0"})
        if config.auth_mode == "bearer" and config.bearer_token:
            self._session.headers["Authorization"] = f"Bearer {config.bearer_token}"
        elif config.email and config.api_token:
            self._session.auth = (config.email, config.api_token)

    # -- helpers --------------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self._cfg.url}/rest/api/{self._cfg.api_version}{path}"

    def _get(self, path: str, params: dict | None = None) -> dict:
        last_exc: Exception | None = None
        for attempt in range(len(_RETRY_BACKOFF) + 1):
            try:
                resp = self._session.get(self._url(path), params=params, timeout=self._timeout)
            except requests.Timeout as exc:
                last_exc = JiraTransportError(f"Jira REST timeout after {self._timeout}s")
                logger.warning("REST timeout (attempt %s): %s", attempt + 1, exc)
            except requests.RequestException as exc:
                last_exc = JiraTransportError(f"Jira REST transport error: {redact(str(exc))}")
                logger.warning("REST transport error (attempt %s): %s", attempt + 1, redact(str(exc)))
            else:
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise JiraTransportError("Jira REST returned malformed JSON") from exc

                api_msg, api_code = _atlassian_error(resp)
                if api_code == "SUSPENDED_INACTIVITY" or "deactivated due to inactivity" in api_msg.lower():
                    raise JiraTransportError(
                        "Jira Cloud site is suspended for inactivity. Open "
                        f"{self._cfg.url} in a browser and sign in to reactivate it (takes a few "
                        "minutes), then retry. This is an Atlassian site state, not an app bug."
                    )
                if resp.status_code in (401, 403):
                    raise JiraAuthError(
                        f"Jira REST authentication/permission failed (HTTP {resp.status_code})."
                        + (f" {api_msg}" if api_msg else "")
                    )
                if resp.status_code == 404:
                    raise JiraNotFoundError("Jira issue not found or not visible (HTTP 404).")
                if resp.status_code == 429:
                    last_exc = JiraRateLimitError("Jira REST rate limited (HTTP 429).")
                elif resp.status_code in _TRANSIENT:
                    last_exc = JiraTransportError(
                        f"Jira REST transient error (HTTP {resp.status_code})."
                        + (f" {api_msg}" if api_msg else "")
                    )
                else:
                    raise JiraTransportError(
                        f"Jira REST unexpected status HTTP {resp.status_code}."
                        + (f" {api_msg}" if api_msg else "")
                    )
            if attempt < len(_RETRY_BACKOFF):
                time.sleep(_RETRY_BACKOFF[attempt])
        raise last_exc or JiraTransportError("Jira REST failed for an unknown reason.")

    # -- interface -----------------------------------------------------
    def health_check(self) -> bool:
        if not self._cfg.configured:
            return False
        try:
            self._get("/myself")
            return True
        except Exception as exc:  # noqa: BLE001 - health check must not raise
            logger.info("REST health check failed: %s", redact(str(exc)))
            return False

    def fetch_issue(self, key: str) -> JiraIssue:
        if not self._cfg.configured:
            raise JiraProviderUnavailableError("Jira REST is not configured (missing URL or credentials).")

        fields = "summary,description,issuetype,status,priority,labels,components,parent,subtasks,issuelinks"
        if self._cfg.acceptance_criteria_field:
            fields += f",{self._cfg.acceptance_criteria_field}"
        data = self._get(f"/issue/{key}", params={"fields": fields})
        f = data.get("fields", {}) or {}

        linked: list[str] = []
        for link in f.get("issuelinks", []) or []:
            for side in ("inwardIssue", "outwardIssue"):
                if side in link and link[side].get("key"):
                    linked.append(link[side]["key"])

        acceptance = ""
        if self._cfg.acceptance_criteria_field and f.get(self._cfg.acceptance_criteria_field):
            acceptance = adf_to_text(f[self._cfg.acceptance_criteria_field])

        comments: list[str] = []
        if self._cfg.include_comments:
            try:
                cdata = self._get(f"/issue/{key}/comment", params={"maxResults": self._cfg.max_comments})
                comments = [adf_to_text(c.get("body")) for c in cdata.get("comments", [])][: self._cfg.max_comments]
            except Exception as exc:  # noqa: BLE001
                logger.info("Could not fetch comments for %s: %s", key, redact(str(exc)))

        issue = JiraIssue(
            key=data.get("key", key).upper(),
            summary=f.get("summary", "") or "",
            description=adf_to_text(f.get("description")),
            issue_type=(f.get("issuetype") or {}).get("name", ""),
            status=(f.get("status") or {}).get("name", ""),
            priority=(f.get("priority") or {}).get("name", ""),
            labels=list(f.get("labels", []) or []),
            components=[c.get("name", "") for c in f.get("components", []) or []],
            parent=(f.get("parent") or {}).get("key", ""),
            subtasks=[s.get("key", "") for s in f.get("subtasks", []) or []],
            linked_issues=linked,
            acceptance_criteria=acceptance,
            comments=comments,
            url=f"{self._cfg.url}/browse/{key}",
            source="REST",
        )
        logger.info("Fetched %s via REST (%d chars description).", issue.key, len(issue.description))
        return issue
