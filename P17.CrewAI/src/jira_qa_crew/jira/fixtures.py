"""Local fixture provider for DEMO MODE.

Fixtures are Jira REST v3 issue payloads stored under ``fixtures/``. They are
ONLY used when ``DEMO_MODE=true`` and no live Jira provider is configured, and
the resulting issue is always tagged ``source='FIXTURE'`` so it can never be
mistaken for live data.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..exceptions import JiraNotFoundError
from ..logging_utils import get_logger
from .adf import adf_to_text
from .base import JiraIssue, JiraProvider

logger = get_logger("jira.fixture")

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures"


class JiraFixtureProvider(JiraProvider):
    name = "FIXTURE"

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self._dir = fixtures_dir or FIXTURES_DIR

    def available_keys(self) -> list[str]:
        return sorted(p.stem.upper() for p in self._dir.glob("*.json"))

    def has_fixture(self, key: str) -> bool:
        return any(p.stem.upper() == key.upper() for p in self._dir.glob("*.json"))

    def health_check(self) -> bool:
        return self._dir.is_dir() and any(self._dir.glob("*.json"))

    def synthesize(self, key: str) -> JiraIssue:
        """Build a clearly-labelled SYNTHETIC demo ticket for a key with no fixture.

        Only reachable from DEMO MODE. It is never presented as live data: the
        summary, description and URL all say SYNTHETIC, and the analyst prompt
        will record the details as MISSING / ASSUMPTION.
        """
        key = key.upper()
        description = (
            "[SYNTHETIC DEMO TICKET] No real Jira fixture exists for this key. "
            "This placeholder lets the pipeline run end-to-end in DEMO MODE. "
            "It is NOT live Jira data and NOT a real requirement source.\n\n"
            "Feature under test: a generic user-facing form submission flow.\n\n"
            "Steps to reproduce / walkthrough:\n"
            "1. Open the feature screen.\n"
            "2. Enter valid input into the primary field.\n"
            "3. Submit the form.\n\n"
            "Expected: the submission succeeds and a confirmation message is shown.\n"
            "Actual: to be confirmed with the real ticket."
        )
        acceptance = (
            "AC-1: Submitting the form with valid input shows a success confirmation.\n"
            "AC-2: Submitting with an empty required field shows an inline validation error and blocks submission.\n"
            "AC-3: The primary control is reachable by keyboard and has an accessible name."
        )
        return JiraIssue(
            key=key,
            summary=f"[SYNTHETIC DEMO] {key} — no fixture available; generic form-submission flow",
            description=description,
            issue_type="Story",
            status="Unknown",
            priority="Medium",
            labels=["synthetic-demo"],
            components=[],
            acceptance_criteria=acceptance,
            url=f"https://demo.invalid/browse/{key}",
            source="FIXTURE",
            raw_excerpt="SYNTHETIC DEMO TICKET",
        )

    def fetch_issue(self, key: str) -> JiraIssue:
        path = self._dir / f"{key.upper()}.json"
        if not path.exists():
            # case-insensitive fallback
            for candidate in self._dir.glob("*.json"):
                if candidate.stem.upper() == key.upper():
                    path = candidate
                    break
            else:
                raise JiraNotFoundError(
                    f"No demo fixture for '{key}'. Available: {', '.join(self.available_keys()) or '(none)'}"
                )
        data = json.loads(path.read_text(encoding="utf-8"))
        f = data.get("fields", {}) or {}
        linked: list[str] = []
        for link in f.get("issuelinks", []) or []:
            for side in ("inwardIssue", "outwardIssue"):
                if side in link:
                    linked.append(link[side].get("key", ""))
        ac_field = data.get("_acceptance_criteria_field")
        acceptance = adf_to_text(f.get(ac_field)) if ac_field else adf_to_text(f.get("acceptance_criteria"))
        issue = JiraIssue(
            key=data.get("key", key).upper(),
            summary=f.get("summary", ""),
            description=adf_to_text(f.get("description")),
            issue_type=(f.get("issuetype") or {}).get("name", ""),
            status=(f.get("status") or {}).get("name", ""),
            priority=(f.get("priority") or {}).get("name", ""),
            labels=list(f.get("labels", []) or []),
            components=[c.get("name", "") for c in f.get("components", []) or []],
            parent=(f.get("parent") or {}).get("key", ""),
            subtasks=[s.get("key", "") for s in f.get("subtasks", []) or []],
            linked_issues=[k for k in linked if k],
            acceptance_criteria=acceptance,
            comments=[adf_to_text(c.get("body")) for c in (data.get("_comments") or [])],
            url=data.get("_url", f"https://demo.invalid/browse/{key}"),
            source="FIXTURE",
        )
        logger.info("Loaded DEMO fixture %s from %s", issue.key, path.name)
        return issue
