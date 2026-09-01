"""Rebuild a RunResult from artifacts already on disk.

Used to backfill ``run_result.json`` for runs produced before that snapshot
existed, so the Streamlit UI can display completed results with zero LLM quota.
Reconstruction is lossy for free-text sections but keeps every structured field
(requirements, acceptance criteria, test cases, coverage).
"""

from __future__ import annotations

import contextlib
import csv
import json
import re
from pathlib import Path

from ..logging_utils import get_logger
from ..models import (
    RequirementAnalysis,
    RunResult,
    StageResult,
    StageStatus,
    TestCase,
    TestCaseSuite,
    TestPlan,
    TestPlanSection,
    TestScenario,
    TestStep,
    TicketResult,
)
from .playwright_parse import parse_playwright_markdown
from .traceability import build_coverage

logger = get_logger("services.reconstruct")

_STAGES = ["Jira Analyst", "Test Plan Writer", "Test Case Writer", "Playwright Coder"]
_SECTION_TITLES = [
    "Executive Summary",
    "Test Objectives",
    "In Scope",
    "Out of Scope",
    "Requirements and Acceptance-Criteria Coverage",
    "Test Strategy, Levels, and Test Types",
    "Test Environment, Tools, and Browser Coverage",
    "Test Data Requirements",
    "High-Level Test Scenarios",
    "Entry and Exit Criteria",
    "Risks, Dependencies, Assumptions, and Mitigations",
    "Execution, Defect Management, Reporting, and Deliverables",
]


def _plan_from_md(md: str, ticket_key: str) -> TestPlan:
    sections: list[TestPlanSection] = []
    matches = list(re.finditer(r"(?m)^##\s+(\d{1,2})\.\s+(.+?)\s*$", md))
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if not 1 <= num <= 12:
            continue
        body = md[m.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(md))].strip()
        sections.append(TestPlanSection(number=num, title=m.group(2).strip(), content=body or "(recovered)"))
    have = {s.number for s in sections}
    for n in range(1, 13):
        if n not in have:
            sections.append(TestPlanSection(number=n, title=_SECTION_TITLES[n - 1], content="(section not recovered)"))
    scenarios: list[TestScenario] = []
    for m in re.finditer(r"(?m)^\|\s*(SC-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", md):
        ids = [x.strip() for x in re.split(r"[,\s]+", m.group(3)) if x.strip() and x.strip() not in {"-", "|"}]
        scenarios.append(TestScenario(id=m.group(1), title=m.group(2), requirement_ids=ids))
    return TestPlan(ticket_key=ticket_key, sections=sorted(sections, key=lambda s: s.number), scenarios=scenarios)


def _split(cell: str, sep: str = "|") -> list[str]:
    return [x.strip() for x in cell.split(sep) if x.strip()]


def _suite_from_csv(path: Path, ticket_key: str) -> TestCaseSuite:
    cases: list[TestCase] = []
    for row in csv.DictReader(path.open(encoding="utf-8")):
        steps: list[TestStep] = []
        for i, part in enumerate(_split(row.get("steps", ""), "|"), start=1):
            act = re.sub(r"^\d+\.\s*", "", part)
            exp = ""
            if " -> " in act:
                act, exp = act.split(" -> ", 1)
            steps.append(TestStep(order=i, action=act.strip() or "step", expected=exp.strip()))
        cand = (row.get("automation_candidate") or "No").strip().title()
        cand = cand if cand in {"Yes", "No", "Partial"} else "No"
        cases.append(
            TestCase(
                id=row["test_case_id"],
                jira_key=row.get("jira_key") or ticket_key,
                requirement_ids=_split(row.get("requirement_ids", ""), " "),
                acceptance_criteria_ids=_split(row.get("acceptance_criteria_ids", ""), " "),
                title=row.get("title") or row["test_case_id"],
                objective=row.get("objective", ""),
                priority=row.get("priority") or "P2",
                test_type=row.get("test_type") or "functional",
                preconditions=_split(row.get("preconditions", "")),
                test_data=_split(row.get("test_data", "")),
                steps=steps or [TestStep(order=1, action="(recovered)")],
                expected_result=row.get("expected_result", ""),
                automation_candidate=cand,
                automation_rationale=row.get("automation_rationale", ""),
                tags=_split(row.get("tags", ""), " "),
                assumptions_or_blockers=_split(row.get("assumptions_or_blockers", "")),
            )
        )
    return TestCaseSuite(ticket_key=ticket_key, test_cases=cases)


def reconstruct_ticket(tdir: Path, ticket_key: str, meta: dict) -> TicketResult | None:
    ra_path = tdir / "requirements_analysis.json"
    if not ra_path.exists():
        return None
    analysis = RequirementAnalysis.model_validate_json(ra_path.read_text(encoding="utf-8"))

    plan = None
    if (tdir / "test_plan.md").exists():
        plan = _plan_from_md((tdir / "test_plan.md").read_text(encoding="utf-8"), ticket_key)
    suite = None
    if (tdir / "test_cases.csv").exists():
        suite = _suite_from_csv(tdir / "test_cases.csv", ticket_key)
    bundle = None
    if (tdir / "playwright_tests.md").exists() and suite is not None:
        bundle = parse_playwright_markdown(
            (tdir / "playwright_tests.md").read_text(encoding="utf-8"), ticket_key, suite
        )

    coverage = build_coverage(analysis, suite, bundle) if suite is not None else None
    status = StageStatus(meta.get("status", "COMPLETED")) if meta.get("status") in StageStatus.__members__ else \
        StageStatus.COMPLETED
    stages = [
        StageResult(name=n, status=StageStatus.COMPLETED, messages=["recovered from artifacts"]) for n in _STAGES
    ]
    artifacts = {p.name: str(p) for p in tdir.rglob("*") if p.is_file()}
    return TicketResult(
        ticket_key=ticket_key,
        status=status if status != StageStatus.PENDING else StageStatus.COMPLETED,
        provider=meta.get("provider", "FIXTURE"),
        demo_mode=bool(meta.get("demo_mode", True)),
        stages=stages,
        warnings=list(meta.get("warnings", [])),
        analysis=analysis,
        test_plan=plan,
        test_suite=suite,
        playwright=bundle,
        coverage=coverage,
        artifact_dir=str(tdir),
        artifacts=artifacts,
    )


def reconstruct_run(run_dir: Path) -> RunResult | None:
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    m: dict = {}
    ticket_metas: list[dict] = []
    if manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        ticket_metas = m.get("tickets", [])
    else:
        # No run-level manifest (interrupted run) — discover from ticket subdirs.
        for sub in sorted(run_dir.iterdir()):
            if sub.is_dir() and (sub / "requirements_analysis.json").exists():
                tm = {"ticket_key": sub.name}
                if (sub / "manifest.json").exists():
                    with contextlib.suppress(Exception):
                        tm.update(json.loads((sub / "manifest.json").read_text(encoding="utf-8")))
                ticket_metas.append(tm)

    tickets: list[TicketResult] = []
    for tmeta in ticket_metas:
        key = tmeta.get("ticket_key")
        if not key:
            continue
        tr = reconstruct_ticket(run_dir / key, key, tmeta)
        if tr:
            tickets.append(tr)
    if not tickets:
        return None
    run = RunResult(
        run_id=m.get("run_id", run_dir.name),
        created_at=m.get("created_at", ""),
        integration_mode=m.get("integration_mode", "auto"),
        demo_mode=bool(m.get("demo_mode", True)),
        requested_tickets=m.get("requested_tickets", [t.ticket_key for t in tickets]),
        tickets=tickets,
        run_dir=str(run_dir),
    )
    zpath = next(run_dir.glob("*_artifacts.zip"), None)
    if zpath:
        run.zip_path = str(zpath)
    return run


def backfill_snapshots(output_dir: Path) -> list[str]:
    """Write run_result.json (and any missing run-level files) for completed runs."""
    from . import artifacts as artifacts_mod  # local import to avoid a cycle

    done: list[str] = []
    for run_dir in Path(output_dir).glob("RUN-*"):
        if (run_dir / "run_result.json").exists():
            continue
        run = reconstruct_run(run_dir)
        if not run:
            continue
        if not (run_dir / "manifest.json").exists() or not (run_dir / "run_summary.md").exists():
            with contextlib.suppress(Exception):
                artifacts_mod.write_run_summary(run)
        if not next(run_dir.glob("*_artifacts.zip"), None):
            with contextlib.suppress(Exception):
                artifacts_mod.build_zip(run)
        (run_dir / "run_result.json").write_text(run.model_dump_json(indent=2), encoding="utf-8", newline="\n")
        done.append(run.run_id)
        logger.info("Backfilled run_result.json for %s", run.run_id)
    return done
