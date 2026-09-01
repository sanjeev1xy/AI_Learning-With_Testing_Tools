from __future__ import annotations

import zipfile
from pathlib import Path

from jira_qa_crew.logging_utils import redact
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
from jira_qa_crew.services.traceability import build_coverage


def test_sanitize_blocks_traversal():
    assert A.sanitize_segment("../../etc/passwd") == "etc_passwd"
    assert A.sanitize_segment("VWO-48") == "VWO-48"
    assert A.sanitize_segment("  ..  ") == "unnamed"


def test_redaction_scrubs_tokens_and_emails(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "super-secret-token-value-1234")
    text = "auth failed for user bob@corp.com token=super-secret-token-value-1234 Bearer abc.def.ghi"
    out = redact(text)
    assert "super-secret-token-value-1234" not in out
    assert "bob@corp.com" not in out
    assert "abc.def.ghi" not in out


def test_full_artifact_write_and_zip(tmp_path, sample_analysis, sample_suite):
    plan = TestPlan(
        ticket_key="VWO-48",
        sections=[TestPlanSection(number=i, title=f"S{i}", content=f"content {i}") for i in range(1, 13)],
    )
    bundle = PlaywrightBundle(
        ticket_key="VWO-48",
        files=[PlaywrightFile(path="vwo-48.spec.ts", content="import { test, expect } from '@playwright/test';\n")],
        readiness="NEEDS_CONFIGURATION",
        missing_information=["selectors"],
    )
    cov = build_coverage(sample_analysis, sample_suite, bundle)
    ticket = TicketResult(
        ticket_key="VWO-48",
        status=StageStatus.WARNING,
        provider="FIXTURE",
        demo_mode=True,
        analysis=sample_analysis,
        test_plan=plan,
        test_suite=sample_suite,
        playwright=bundle,
        coverage=cov,
    )
    run_dir = tmp_path / "RUN-1"
    written = A.write_ticket_artifacts(run_dir, ticket)
    for expected in [
        "requirements_analysis.md",
        "requirements_analysis.json",
        "test_plan.md",
        "test_cases.md",
        "test_cases.csv",
        "traceability_matrix.csv",
        "playwright_tests.md",
        "manifest.json",
    ]:
        assert expected in written
        assert Path(written[expected]).exists()

    spec = next(p for k, p in written.items() if k.endswith(".spec.ts"))
    assert "playwright/tests/" in spec.replace("\\", "/")

    run = RunResult(run_id="RUN-1", run_dir=str(run_dir), requested_tickets=["VWO-48"], tickets=[ticket])
    A.write_run_summary(run)
    zpath = A.build_zip(run)
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
    assert "run_summary.md" in names
    assert "manifest.json" in names
    assert any(n.endswith("VWO-48/test_cases.csv") for n in names)

    # Snapshot round-trips so the UI can restore results after a reload.
    restored = A.load_run(run_dir)
    assert restored is not None
    assert restored.run_id == "RUN-1"
    assert restored.tickets[0].ticket_key == "VWO-48"
    assert restored.tickets[0].analysis is not None
    assert [p.name for p in A.list_runs(tmp_path)] == ["RUN-1"]
