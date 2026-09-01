"""Pipeline test with fully mocked CrewAI + LLM (no network, no paid calls)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from jira_qa_crew.crew.callbacks import ProgressTracker
from jira_qa_crew.models import (
    AcceptanceCriterion,
    JiraTicketMeta,
    PlaywrightBundle,
    PlaywrightFile,
    Requirement,
    RequirementAnalysis,
    TestCase,
    TestCaseSuite,
    TestPlan,
    TestPlanSection,
    TestScenario,
    TestStep,
)
from jira_qa_crew.services import pipeline as P


def _analysis():
    return RequirementAnalysis(
        ticket_key="VWO-48",
        meta=JiraTicketMeta(key="VWO-48", summary="Cart total $0.00 bug"),
        description_text="desc",
        requirements=[Requirement(id="REQ-001", text="correct discounted total for 3+ items")],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001", text="3+ items -> discounted total")],
        missing_information=["order-summary selector"],
    )


def _plan():
    return TestPlan(
        ticket_key="VWO-48",
        sections=[TestPlanSection(number=i, title=f"S{i}", content=f"c{i}") for i in range(1, 13)],
        scenarios=[TestScenario(id="SC-001", title="discount", requirement_ids=["REQ-001", "AC-001"])],
    )


def _suite():
    return TestCaseSuite(
        ticket_key="VWO-48",
        test_cases=[
            TestCase(
                id="VWO-48-TC-001", jira_key="VWO-48", requirement_ids=["REQ-001"],
                acceptance_criteria_ids=["AC-001"], title="discounted total",
                steps=[TestStep(order=1, action="add 3 items", expected="cart=3")],
                expected_result="total = subtotal-20%", automation_candidate="Yes",
                automation_rationale="ui",
            )
        ],
    )


def _bundle():
    return PlaywrightBundle(
        ticket_key="VWO-48",
        files=[PlaywrightFile(path="tests/vwo-48.spec.ts",
                              content="import { test, expect } from '@playwright/test';\ntest('t', async () => {});")],
        readiness="NEEDS_CONFIGURATION",
        missing_information=["real selectors"],
    )


_STAGE_OUTPUT = {
    "analysis": _analysis,
    "test_plan": _plan,
    "test_cases": _suite,
    "playwright": _bundle,
}


class _FakeCtx:
    def __init__(self, boom_stage: str | None = None):
        self._boom = boom_stage

    def run_stage(self, stage, *, context_text="", callback=None, max_rpm=30):
        if stage == self._boom:
            raise RuntimeError("llm exploded")
        obj = _STAGE_OUTPUT[stage]()
        if callback:
            callback(SimpleNamespace(raw=obj.model_dump_json()))
        return obj, obj.model_dump_json()


@pytest.fixture
def _mock_crew(monkeypatch):
    monkeypatch.setattr(P, "build_llm", lambda cfg=None: object())
    monkeypatch.setattr(P, "build_ticket_crew_context", lambda **kw: _FakeCtx())


def test_full_pipeline_demo(tmp_path, monkeypatch, _mock_crew):
    monkeypatch.setenv("DEMO_MODE", "true")
    run = P.run_pipeline("VWO-48", output_root=tmp_path)
    assert run.is_successful
    t = run.tickets[0]
    assert t.provider == "FIXTURE"
    assert t.demo_mode is True
    assert t.status.value in {"COMPLETED", "WARNING"}
    assert t.coverage.total_requirements >= 1
    assert "requirements_analysis.md" in t.artifacts
    assert run.zip_path


def test_partial_success_when_one_ticket_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setattr(P, "build_llm", lambda cfg=None: object())

    def _factory(**kw):
        return _FakeCtx(boom_stage="analysis" if kw["ticket_key"] == "VWO-49" else None)

    monkeypatch.setattr(P, "build_ticket_crew_context", _factory)
    run = P.run_pipeline("VWO-48, VWO-49", output_root=tmp_path)
    assert run.is_successful  # at least one ticket ok
    by_key = {t.ticket_key: t for t in run.tickets}
    assert by_key["VWO-48"].succeeded
    assert by_key["VWO-49"].status.value == "FAILED"


def test_progress_hook_receives_stage_updates(tmp_path, monkeypatch, _mock_crew):
    monkeypatch.setenv("DEMO_MODE", "true")
    seen: list[str] = []

    def hook(key: str, tracker: ProgressTracker):
        seen.append(key)

    P.run_pipeline("VWO-48", output_root=tmp_path, progress=hook)
    assert "VWO-48" in seen
