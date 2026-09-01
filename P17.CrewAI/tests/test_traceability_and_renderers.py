from __future__ import annotations

import csv
import io
import json

from jira_qa_crew.models import (
    AutomatedTestLink,
    PlaywrightBundle,
    PlaywrightFile,
    TestPlan,
    TestPlanSection,
    TestScenario,
)
from jira_qa_crew.services import renderers as R
from jira_qa_crew.services.traceability import build_coverage
from jira_qa_crew.services.validation import validate_analysis, validate_cases, validate_plan


def test_build_coverage_flags_orphans(sample_analysis, sample_suite):
    bundle = PlaywrightBundle(
        ticket_key="VWO-48",
        files=[PlaywrightFile(path="tests/vwo-48.spec.ts", content="import { test } from '@playwright/test';")],
        automated_links=[
            AutomatedTestLink(spec_title="disc", test_case_id="VWO-48-TC-001", jira_key="VWO-48",
                              requirement_ids=["REQ-001"], acceptance_criteria_ids=["AC-001"]),
        ],
    )
    cov = build_coverage(sample_analysis, sample_suite, bundle)
    assert cov.total_requirements == 2
    assert cov.covered_requirements == 2
    assert cov.automated_test_cases == 1
    assert cov.total_test_cases == 2
    # deterministic csv
    rows = list(csv.reader(io.StringIO(R.traceability_to_csv(cov))))
    assert rows[0] == ["requirement_id", "acceptance_criterion_id", "test_case_ids",
                       "automated_test_ids", "coverage_status", "reason"]


def test_renderers_are_deterministic(sample_analysis, sample_suite):
    a1 = R.analysis_to_markdown(sample_analysis)
    a2 = R.analysis_to_markdown(sample_analysis)
    assert a1 == a2
    parsed = json.loads(R.analysis_to_json(sample_analysis))
    assert parsed["ticket_key"] == "VWO-48"
    csv_text = R.cases_to_csv(sample_suite)
    assert "VWO-48-TC-001" in csv_text
    assert csv_text.splitlines()[0].startswith("test_case_id,")


def test_validation_detects_bad_plan(sample_analysis):
    plan = TestPlan(
        ticket_key="VWO-48",
        sections=[TestPlanSection(number=1, title="x", content="c")],  # missing 2..12
        scenarios=[TestScenario(id="SC-001", title="s", requirement_ids=["REQ-001"])],
    )
    out = validate_plan(plan, sample_analysis)
    assert not out.ok
    assert any("1..12" in p for p in out.problems)


def test_validation_duplicate_ids(sample_analysis, sample_suite):
    sample_suite.test_cases[1].id = "VWO-48-TC-001"
    out = validate_cases(sample_suite, sample_analysis)
    assert any("Duplicate test-case id" in p for p in out.problems)


def test_validate_analysis_ok(sample_analysis):
    assert validate_analysis(sample_analysis, "VWO-48").ok
