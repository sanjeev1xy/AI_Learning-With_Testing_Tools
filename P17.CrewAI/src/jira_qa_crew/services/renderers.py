"""Deterministic renderers: validated Pydantic objects -> Markdown / CSV / JSON / TS.

Raw LLM markdown is never used as the source of truth; every file here is built
from the structured models.
"""

from __future__ import annotations

import csv
import io
import json

from ..models import (
    CoverageReport,
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TestPlan,
)


def _bullets(items: list[str], empty: str = "_None recorded._") -> str:
    items = [i for i in items if str(i).strip()]
    if not items:
        return empty
    return "\n".join(f"- {i}" for i in items)


def _cell(text: str) -> str:
    """Escape a value for use inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------
# Requirements analysis
# --------------------------------------------------------------------------
def analysis_to_markdown(a: RequirementAnalysis) -> str:
    m = a.meta
    lines = [
        f"# Requirements Analysis — {a.ticket_key}",
        "",
        f"- **Summary:** {m.summary}",
        f"- **Issue type:** {m.issue_type or 'n/a'}",
        f"- **Status:** {m.status or 'n/a'}",
        f"- **Priority:** {m.priority or 'n/a'}",
        f"- **Labels:** {', '.join(m.labels) or 'n/a'}",
        f"- **Components:** {', '.join(m.components) or 'n/a'}",
        f"- **Parent:** {m.parent or 'n/a'}",
        f"- **Subtasks:** {', '.join(m.subtasks) or 'n/a'}",
        f"- **Linked issues:** {', '.join(m.linked_issues) or 'n/a'}",
        f"- **Source provider:** {a.provider or 'n/a'}",
        f"- **Fetched at:** {a.fetched_at}",
        "",
        "## Description",
        "",
        a.description_text or "_Empty._",
        "",
        "## Functional & Non-Functional Requirements",
        "",
        "| ID | Kind | Provenance | Requirement | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in a.requirements:
        lines.append(
            f"| {r.id} | {r.kind} | {r.provenance.value} | {_cell(r.text)} | {r.source or '-'} |"
        )
    lines += ["", "## Acceptance Criteria", "", "| ID | Provenance | Criterion |", "| --- | --- | --- |"]
    for ac in a.acceptance_criteria:
        lines.append(f"| {ac.id} | {ac.provenance.value} | {_cell(ac.text)} |")
    if not a.acceptance_criteria:
        lines.append("| — | MISSING | No acceptance criteria stated on the ticket. |")

    lines += [
        "",
        "## Business Rules",
        "",
        _bullets(a.business_rules),
        "",
        "## Non-Functional Requirements",
        "",
        _bullets(a.non_functional_requirements),
        "",
        "## Dependencies",
        "",
        _bullets(a.dependencies),
        "",
        "## Constraints",
        "",
        _bullets(a.constraints),
        "",
        "## Risks",
        "",
        _bullets(a.risks),
        "",
        "## Assumptions",
        "",
        _bullets(a.assumptions),
        "",
        "## Missing Information",
        "",
        _bullets(a.missing_information, "_No gaps recorded._"),
        "",
        "## Open Questions",
        "",
        _bullets(a.open_questions, "_None._"),
        "",
    ]
    return "\n".join(lines)


def analysis_to_json(a: RequirementAnalysis) -> str:
    return json.dumps(a.model_dump(mode="json"), indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------
# Compact context strings passed between CrewAI stages (token-budget aware)
# --------------------------------------------------------------------------
def analysis_context(a: RequirementAnalysis) -> str:
    lines = [f"TICKET {a.ticket_key}: {a.meta.summary}", f"TYPE {a.meta.issue_type} | PRIORITY {a.meta.priority}", ""]
    lines.append("REQUIREMENTS:")
    lines += [f"  {r.id} ({r.kind}/{r.provenance.value}): {r.text}" for r in a.requirements] or ["  (none)"]
    lines.append("ACCEPTANCE CRITERIA:")
    lines += [f"  {c.id} ({c.provenance.value}): {c.text}" for c in a.acceptance_criteria] or ["  (none)"]
    if a.business_rules:
        lines.append("BUSINESS RULES: " + "; ".join(a.business_rules))
    if a.non_functional_requirements:
        lines.append("NON-FUNCTIONAL: " + "; ".join(a.non_functional_requirements))
    if a.dependencies:
        lines.append("DEPENDENCIES: " + "; ".join(a.dependencies))
    if a.risks:
        lines.append("RISKS: " + "; ".join(a.risks))
    if a.missing_information:
        lines.append("MISSING INFO: " + "; ".join(a.missing_information))
    return "\n".join(lines)


def plan_context(p: TestPlan) -> str:
    lines = ["TEST PLAN SCENARIOS:"]
    lines += [f"  {s.id}: {s.title} -> {', '.join(s.requirement_ids)}" for s in p.scenarios] or ["  (none)"]
    strat = next((s.content for s in p.sections if s.number == 6), "")
    if strat:
        lines.append("STRATEGY: " + strat[:600])
    return "\n".join(lines)


def cases_context_for_playwright(suite: TestCaseSuite) -> str:
    lines = [f"TEST CASES for {suite.ticket_key} (automate only Yes/Partial):"]
    for tc in suite.test_cases:
        steps = " | ".join(f"{s.order}.{s.action}" for s in tc.steps)
        lines.append(
            f"  {tc.id} [{tc.automation_candidate.value}] {tc.title}\n"
            f"    REQ={','.join(tc.requirement_ids)} AC={','.join(tc.acceptance_criteria_ids)}\n"
            f"    steps: {steps}\n"
            f"    expected: {tc.expected_result}"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Test plan
# --------------------------------------------------------------------------
def plan_to_markdown(p: TestPlan) -> str:
    lines = [f"# Test Plan — {p.ticket_key}", ""]
    for section in sorted(p.sections, key=lambda s: s.number):
        lines += [f"## {section.number}. {section.title}", "", section.content.strip(), ""]
    if p.scenarios:
        lines += ["## Scenario Traceability", "", "| Scenario | Title | Requirement / AC IDs |", "| --- | --- | --- |"]
        for sc in p.scenarios:
            lines.append(f"| {sc.id} | {_cell(sc.title)} | {', '.join(sc.requirement_ids)} |")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------------
def cases_to_markdown(suite: TestCaseSuite) -> str:
    lines = [f"# Test Cases — {suite.ticket_key}", "", f"Total: {len(suite.test_cases)}", ""]
    for tc in suite.test_cases:
        steps = "\n".join(f"  {s.order}. {s.action}" + (f" → _{s.expected}_" if s.expected else "") for s in tc.steps)
        lines += [
            f"## {tc.id} — {tc.title}",
            "",
            f"- **Objective:** {tc.objective or 'n/a'}",
            f"- **Jira:** {tc.jira_key}",
            f"- **Requirements:** {', '.join(tc.requirement_ids) or 'n/a'}",
            f"- **Acceptance criteria:** {', '.join(tc.acceptance_criteria_ids) or 'n/a'}",
            f"- **Priority:** {tc.priority} | **Type:** {tc.test_type}",
            f"- **Preconditions:** {'; '.join(tc.preconditions) or 'none'}",
            f"- **Test data:** {'; '.join(tc.test_data) or 'none'}",
            "",
            "**Steps:**",
            "",
            steps or "_No steps._",
            "",
            f"**Expected result:** {tc.expected_result or 'n/a'}",
            "",
            f"- **Automation candidate:** {tc.automation_candidate.value} — {tc.automation_rationale or 'n/a'}",
            f"- **Tags:** {', '.join(tc.tags) or 'none'}",
            f"- **Assumptions / blockers:** {'; '.join(tc.assumptions_or_blockers) or 'none'}",
            "",
        ]
    return "\n".join(lines)


_CASE_CSV_HEADER = [
    "test_case_id",
    "jira_key",
    "requirement_ids",
    "acceptance_criteria_ids",
    "title",
    "objective",
    "priority",
    "test_type",
    "preconditions",
    "test_data",
    "steps",
    "expected_result",
    "automation_candidate",
    "automation_rationale",
    "tags",
    "assumptions_or_blockers",
]


def cases_to_csv(suite: TestCaseSuite) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(_CASE_CSV_HEADER)
    for tc in suite.test_cases:
        w.writerow(
            [
                tc.id,
                tc.jira_key,
                " ".join(tc.requirement_ids),
                " ".join(tc.acceptance_criteria_ids),
                tc.title,
                tc.objective,
                tc.priority,
                tc.test_type,
                " | ".join(tc.preconditions),
                " | ".join(tc.test_data),
                " | ".join(f"{s.order}. {s.action}" + (f" -> {s.expected}" if s.expected else "") for s in tc.steps),
                tc.expected_result,
                tc.automation_candidate.value,
                tc.automation_rationale,
                " ".join(tc.tags),
                " | ".join(tc.assumptions_or_blockers),
            ]
        )
    return buf.getvalue()


# --------------------------------------------------------------------------
# Traceability
# --------------------------------------------------------------------------
def traceability_to_csv(cov: CoverageReport) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "requirement_id",
            "acceptance_criterion_id",
            "test_case_ids",
            "automated_test_ids",
            "coverage_status",
            "reason",
        ]
    )
    for row in cov.rows:
        w.writerow(
            [
                row.requirement_id,
                row.acceptance_criterion_id,
                " ".join(row.test_case_ids),
                " ".join(row.automated_test_ids),
                row.coverage_status.value,
                row.reason,
            ]
        )
    return buf.getvalue()


def coverage_to_markdown(cov: CoverageReport) -> str:
    lines = [
        f"# Traceability Matrix — {cov.ticket_key}",
        "",
        f"- Requirements covered: {cov.covered_requirements}/{cov.total_requirements} "
        f"({cov.requirement_coverage_pct}%)",
        f"- Acceptance criteria covered: {cov.covered_acceptance_criteria}/{cov.total_acceptance_criteria} "
        f"({cov.ac_coverage_pct}%)",
        f"- Test cases: {cov.total_test_cases} (automated: {cov.automated_test_cases}, {cov.automation_pct}%)",
        f"- Orphan requirements: {', '.join(cov.orphan_requirements) or 'none'}",
        f"- Orphan test cases: {', '.join(cov.orphan_test_cases) or 'none'}",
        "",
        "| Requirement | AC | Test Cases | Automated | Status | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in cov.rows:
        lines.append(
            f"| {row.requirement_id or '-'} | {row.acceptance_criterion_id or '-'} | "
            f"{', '.join(row.test_case_ids) or '-'} | {', '.join(row.automated_test_ids) or '-'} | "
            f"{row.coverage_status.value} | {row.reason} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Playwright
# --------------------------------------------------------------------------
def playwright_to_markdown(b: PlaywrightBundle) -> str:
    lines = [
        f"# Playwright Automation — {b.ticket_key}",
        "",
        f"**Automation readiness:** `{b.readiness.value}`",
        "",
        "## Setup Notes",
        "",
        b.setup_notes or "_None._",
        "",
        "## Coverage Notes",
        "",
        b.coverage_notes or "_None._",
        "",
        "## Traceability",
        "",
        "| Spec | Test Case | Jira | Requirements | Acceptance Criteria |",
        "| --- | --- | --- | --- | --- |",
    ]
    for link in b.automated_links:
        lines.append(
            f"| {link.spec_title} | {link.test_case_id} | {link.jira_key} | "
            f"{', '.join(link.requirement_ids) or '-'} | {', '.join(link.acceptance_criteria_ids) or '-'} |"
        )
    lines += ["", "## Assumptions", "", _bullets(b.assumptions), "", "## Missing Information", "",
              _bullets(b.missing_information, "_None._"), ""]
    for f in b.files:
        lang = "typescript" if f.path.endswith((".ts", ".tsx")) else ""
        lines += [f"## `{f.path}`", "", f"```{lang}", f.content.rstrip(), "```", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Playwright project config (deterministic, not from the LLM)
# --------------------------------------------------------------------------
def playwright_config_ts() -> str:
    return (
        "import { defineConfig, devices } from '@playwright/test';\n\n"
        "export default defineConfig({\n"
        "  testDir: './tests',\n"
        "  fullyParallel: true,\n"
        "  forbidOnly: !!process.env.CI,\n"
        "  retries: process.env.CI ? 2 : 0,\n"
        "  reporter: 'list',\n"
        "  use: {\n"
        "    baseURL: process.env.BASE_URL || 'http://localhost:3000',\n"
        "    trace: 'on-first-retry',\n"
        "  },\n"
        "  projects: [\n"
        "    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },\n"
        "    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },\n"
        "  ],\n"
        "});\n"
    )


def playwright_package_json(ticket_key: str) -> str:
    return json.dumps(
        {
            "name": f"qa-automation-{ticket_key.lower()}",
            "version": "0.1.0",
            "private": True,
            "scripts": {"test": "playwright test", "test:list": "playwright test --list"},
            "devDependencies": {"@playwright/test": "^1.47.0", "typescript": "^5.5.0"},
        },
        indent=2,
    )


def playwright_tsconfig_json() -> str:
    return json.dumps(
        {
            "compilerOptions": {
                "target": "ES2022",
                "module": "commonjs",
                "moduleResolution": "node",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "types": ["@playwright/test", "node"],
            },
            "include": ["tests/**/*.ts", "pages/**/*.ts", "fixtures/**/*.ts"],
        },
        indent=2,
    )
