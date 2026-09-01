"""Reconstructing a RunResult from on-disk artifacts (UI restore path)."""

from __future__ import annotations

from pathlib import Path

from jira_qa_crew.models import (
    PlaywrightBundle,
    PlaywrightFile,
    RunResult,
    StageStatus,
    TestPlan,
    TestPlanSection,
    TicketResult,
)
from jira_qa_crew.services import artifacts as A
from jira_qa_crew.services.reconstruct import backfill_snapshots, reconstruct_run
from jira_qa_crew.services.traceability import build_coverage


def _seed_run(tmp_path: Path, sample_analysis, sample_suite) -> Path:
    plan = TestPlan(
        ticket_key="VWO-48",
        sections=[TestPlanSection(number=i, title=f"S{i}", content=f"body {i}") for i in range(1, 13)],
    )
    bundle = PlaywrightBundle(
        ticket_key="VWO-48",
        files=[PlaywrightFile(path="tests/vwo-48.spec.ts", content="import { test } from '@playwright/test';")],
        readiness="NEEDS_CONFIGURATION",
    )
    ticket = TicketResult(
        ticket_key="VWO-48",
        status=StageStatus.COMPLETED,
        provider="FIXTURE",
        demo_mode=True,
        analysis=sample_analysis,
        test_plan=plan,
        test_suite=sample_suite,
        playwright=bundle,
        coverage=build_coverage(sample_analysis, sample_suite, bundle),
    )
    run_dir = tmp_path / "RUN-X"
    A.write_ticket_artifacts(run_dir, ticket)
    run = RunResult(run_id="RUN-X", run_dir=str(run_dir), requested_tickets=["VWO-48"], tickets=[ticket])
    A.write_run_summary(run)
    # simulate a pre-snapshot run
    (run_dir / "run_result.json").unlink()
    return run_dir


def test_reconstruct_from_artifacts(tmp_path, sample_analysis, sample_suite):
    run_dir = _seed_run(tmp_path, sample_analysis, sample_suite)
    run = reconstruct_run(run_dir)
    assert run is not None
    t = run.tickets[0]
    assert t.ticket_key == "VWO-48"
    assert len(t.test_suite.test_cases) == len(sample_suite.test_cases)
    assert {s.number for s in t.test_plan.sections} == set(range(1, 13))
    assert t.coverage.total_requirements == len(sample_analysis.requirements)
    assert t.analysis.acceptance_criteria[0].id == "AC-001"


def test_backfill_writes_snapshot(tmp_path, sample_analysis, sample_suite):
    run_dir = _seed_run(tmp_path, sample_analysis, sample_suite)
    done = backfill_snapshots(tmp_path)
    assert "RUN-X" in done
    assert (run_dir / "run_result.json").exists()
    reloaded = A.load_run(run_dir)
    assert reloaded and reloaded.tickets[0].ticket_key == "VWO-48"
