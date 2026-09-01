"""Deterministic requirement -> test -> automation traceability and coverage.

All logic here is plain Python. The LLM never computes coverage numbers.
"""

from __future__ import annotations

from ..models import (
    CoverageReport,
    CoverageStatus,
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TraceabilityRow,
)


def build_coverage(
    analysis: RequirementAnalysis,
    suite: TestCaseSuite,
    playwright: PlaywrightBundle | None,
) -> CoverageReport:
    automated_tc_ids: set[str] = set()
    if playwright:
        automated_tc_ids = {link.test_case_id.upper() for link in playwright.automated_links}
        # Also treat any Yes/Partial case as automation-targeted if links are missing.
    yes_partial = {tc.id for tc in suite.test_cases if tc.automation_candidate.value in {"Yes", "Partial"}}
    if not automated_tc_ids:
        automated_tc_ids = set(yes_partial)

    req_to_tests: dict[str, set[str]] = {r.id: set() for r in analysis.requirements}
    ac_to_tests: dict[str, set[str]] = {a.id: set() for a in analysis.acceptance_criteria}
    all_tc_ids = {tc.id for tc in suite.test_cases}
    referenced_tc_ids: set[str] = set()

    for tc in suite.test_cases:
        for rid in tc.requirement_ids:
            if rid in req_to_tests:
                req_to_tests[rid].add(tc.id)
                referenced_tc_ids.add(tc.id)
        for aid in tc.acceptance_criteria_ids:
            if aid in ac_to_tests:
                ac_to_tests[aid].add(tc.id)
                referenced_tc_ids.add(tc.id)

    rows: list[TraceabilityRow] = []

    # AC-level rows (each AC tied to its requirement where possible).
    ac_by_id = {a.id: a for a in analysis.acceptance_criteria}
    for aid, tcs in ac_to_tests.items():
        automated = sorted(t for t in tcs if t in automated_tc_ids)
        status, reason = _status(tcs, automated, ac_by_id.get(aid).text if ac_by_id.get(aid) else "")
        rows.append(
            TraceabilityRow(
                requirement_id=_owning_requirement(aid, analysis) or "",
                acceptance_criterion_id=aid,
                test_case_ids=sorted(tcs),
                automated_test_ids=automated,
                coverage_status=status,
                reason=reason,
            )
        )

    # Requirement-level rows (only requirements without AC coverage, to avoid noise).
    for rid, tcs in req_to_tests.items():
        automated = sorted(t for t in tcs if t in automated_tc_ids)
        status, reason = _status(tcs, automated, "")
        rows.append(
            TraceabilityRow(
                requirement_id=rid,
                acceptance_criterion_id="",
                test_case_ids=sorted(tcs),
                automated_test_ids=automated,
                coverage_status=status,
                reason=reason,
            )
        )

    covered_reqs = sum(1 for tcs in req_to_tests.values() if tcs)
    covered_acs = sum(1 for tcs in ac_to_tests.values() if tcs)
    orphan_reqs = sorted(rid for rid, tcs in req_to_tests.items() if not tcs)
    orphan_tcs = sorted(all_tc_ids - referenced_tc_ids)

    return CoverageReport(
        ticket_key=analysis.ticket_key,
        total_requirements=len(analysis.requirements),
        covered_requirements=covered_reqs,
        total_acceptance_criteria=len(analysis.acceptance_criteria),
        covered_acceptance_criteria=covered_acs,
        total_test_cases=len(suite.test_cases),
        automated_test_cases=len(all_tc_ids & automated_tc_ids),
        orphan_requirements=orphan_reqs,
        orphan_test_cases=orphan_tcs,
        rows=rows,
    )


def _status(tcs: set[str], automated: list[str], _text: str) -> tuple[CoverageStatus, str]:
    if not tcs:
        return CoverageStatus.NONE, "No test case references this item."
    if automated:
        if len(automated) == len(tcs):
            return CoverageStatus.FULL, "All linked test cases have automation."
        return CoverageStatus.PARTIAL, "Some linked test cases are automated; others are manual."
    return CoverageStatus.PARTIAL, "Manual test coverage only; no automated test linked yet."


def _owning_requirement(ac_id: str, analysis: RequirementAnalysis) -> str | None:
    # Best-effort: link AC to a requirement that mentions it, else first requirement.
    for r in analysis.requirements:
        if ac_id in r.text:
            return r.id
    return analysis.requirements[0].id if analysis.requirements else None
