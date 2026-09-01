"""Deterministic post-stage validation.

These checks run in plain Python after each CrewAI stage. Failing a hard check
raises :class:`ValidationFailedError`; soft issues are returned as warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..models import (
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TestPlan,
)

_REQ_RE = re.compile(r"^REQ-\d{3,}$")
_AC_RE = re.compile(r"^AC-\d{3,}$")


@dataclass
class ValidationOutcome:
    problems: list[str] = field(default_factory=list)  # hard failures
    warnings: list[str] = field(default_factory=list)  # soft issues

    @property
    def ok(self) -> bool:
        return not self.problems

    def merge(self, other: ValidationOutcome) -> None:
        self.problems.extend(other.problems)
        self.warnings.extend(other.warnings)


def _dupes(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for v in values:
        if v in seen:
            dupes.add(v)
        seen.add(v)
    return sorted(dupes)


def validate_analysis(analysis: RequirementAnalysis, ticket_key: str) -> ValidationOutcome:
    out = ValidationOutcome()
    if analysis.ticket_key.upper() != ticket_key.upper():
        out.problems.append(f"Analysis ticket_key '{analysis.ticket_key}' != requested '{ticket_key}'.")

    req_ids = [r.id for r in analysis.requirements]
    ac_ids = [a.id for a in analysis.acceptance_criteria]
    for dup in _dupes(req_ids):
        out.problems.append(f"Duplicate requirement id: {dup}")
    for dup in _dupes(ac_ids):
        out.problems.append(f"Duplicate acceptance-criterion id: {dup}")
    for rid in req_ids:
        if not _REQ_RE.match(rid):
            out.warnings.append(f"Requirement id '{rid}' does not match REQ-000 pattern.")
    for aid in ac_ids:
        if not _AC_RE.match(aid):
            out.warnings.append(f"Acceptance-criterion id '{aid}' does not match AC-000 pattern.")

    if not analysis.requirements:
        out.problems.append("Analysis produced zero requirements.")
    if not analysis.acceptance_criteria and not analysis.missing_information:
        out.warnings.append("No acceptance criteria and no missing-information note — verify the ticket.")
    for r in analysis.requirements:
        if not r.text.strip():
            out.problems.append(f"Requirement {r.id} has empty text.")
    return out


def validate_plan(plan: TestPlan, analysis: RequirementAnalysis) -> ValidationOutcome:
    out = ValidationOutcome()
    numbers = sorted(s.number for s in plan.sections)
    if numbers != list(range(1, 13)):
        out.problems.append(f"Test plan must have sections 1..12, got {numbers}.")
    for s in plan.sections:
        if not s.content.strip():
            out.problems.append(f"Test plan section {s.number} ('{s.title}') is empty.")

    known = {r.id for r in analysis.requirements} | {a.id for a in analysis.acceptance_criteria}
    if not plan.scenarios:
        out.warnings.append("Test plan has no scenarios list.")
    for sc in plan.scenarios:
        if not sc.requirement_ids:
            out.problems.append(f"Scenario {sc.id} references no REQ-*/AC- id.")
        for rid in sc.requirement_ids:
            if known and rid not in known:
                out.warnings.append(f"Scenario {sc.id} references unknown id '{rid}'.")
    return out


def validate_cases(suite: TestCaseSuite, analysis: RequirementAnalysis) -> ValidationOutcome:
    out = ValidationOutcome()
    ids = [tc.id for tc in suite.test_cases]
    for dup in _dupes(ids):
        out.problems.append(f"Duplicate test-case id: {dup}")
    if not suite.test_cases:
        out.problems.append("Test-case suite is empty.")

    known_req = {r.id for r in analysis.requirements}
    known_ac = {a.id for a in analysis.acceptance_criteria}
    for tc in suite.test_cases:
        if not tc.steps:
            out.problems.append(f"Test case {tc.id} has no steps.")
        if not tc.expected_result.strip() and not any(s.expected for s in tc.steps):
            out.warnings.append(f"Test case {tc.id} has no expected result.")
        for rid in tc.requirement_ids:
            if known_req and rid not in known_req:
                out.warnings.append(f"Test case {tc.id} references unknown requirement '{rid}'.")
        for aid in tc.acceptance_criteria_ids:
            if known_ac and aid not in known_ac:
                out.warnings.append(f"Test case {tc.id} references unknown AC '{aid}'.")

    # Every explicit AC needs at least one positive test.
    covered_ac = {aid for tc in suite.test_cases for aid in tc.acceptance_criteria_ids}
    for ac in analysis.acceptance_criteria:
        if ac.id not in covered_ac:
            out.warnings.append(f"Acceptance criterion {ac.id} has no test case.")
    return out


def validate_playwright(bundle: PlaywrightBundle, suite: TestCaseSuite) -> ValidationOutcome:
    out = ValidationOutcome()
    automatable = {tc.id for tc in suite.test_cases if tc.automation_candidate.value in {"Yes", "Partial"}}

    if automatable and not bundle.files:
        out.problems.append("Test cases are marked automatable but no Playwright files were produced.")
    for f in bundle.files:
        if not f.path.endswith((".ts", ".tsx")):
            out.warnings.append(f"Playwright file '{f.path}' is not a TypeScript file.")
        if "page.waitForTimeout" in f.content:
            out.problems.append(f"Playwright file '{f.path}' uses page.waitForTimeout().")
        if "@playwright/test" not in f.content and f.path.endswith(".spec.ts"):
            out.warnings.append(f"Playwright spec '{f.path}' does not import from @playwright/test.")
        if _looks_like_secret(f.content):
            # The renderer/parser scrubs obvious credential literals to process.env;
            # anything left is a soft flag, not a reason to fail the whole ticket.
            out.warnings.append(
                f"Playwright file '{f.path}' still contains a credential-looking literal — review before use."
            )

    for link in bundle.automated_links:
        if link.test_case_id not in {tc.id for tc in suite.test_cases}:
            out.warnings.append(f"Automated link references unknown test case '{link.test_case_id}'.")

    if bundle.readiness.value == "READY" and bundle.missing_information:
        out.warnings.append("Bundle marked READY but still lists missing information.")
    return out


_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9/\+_\-]{12,}['\"]"
)


_SECRET_ALLOW = ("PLACEHOLDER", "YOUR_", "EXAMPLE", "TEST", "DUMMY", "FAKE", "CHANGEME", "SAMPLE", "XXX", "REDACTED")


def _looks_like_secret(text: str) -> bool:
    for m in _SECRET_RE.finditer(text):
        snippet = m.group(0).upper()
        if "process.env" in text[max(0, m.start() - 40) : m.start()]:
            continue
        if any(tok in snippet for tok in _SECRET_ALLOW):
            continue
        return True
    return False
