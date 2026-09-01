"""Pydantic structured models — the internal source of truth for every artifact."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Provenance(str, Enum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    ASSUMPTION_REQUIRING_CONFIRMATION = "ASSUMPTION_REQUIRING_CONFIRMATION"


class AutomationCandidate(str, Enum):
    YES = "Yes"
    NO = "No"
    PARTIAL = "Partial"


class AutomationReadiness(str, Enum):
    READY = "READY"
    NEEDS_CONFIGURATION = "NEEDS_CONFIGURATION"


class CoverageStatus(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


# --------------------------------------------------------------------------
# Stage 1 — Requirements analysis
# --------------------------------------------------------------------------
class Requirement(BaseModel):
    id: str = Field(description="Stable id, e.g. REQ-001")
    text: str
    kind: str = Field(default="functional", description="functional | non-functional | business-rule")
    provenance: Provenance = Provenance.EXPLICIT
    source: str = Field(default="", description="Jira field or location this came from")

    @field_validator("id")
    @classmethod
    def _norm_id(cls, v: str) -> str:
        return v.strip().upper()


class AcceptanceCriterion(BaseModel):
    id: str = Field(description="Stable id, e.g. AC-001")
    text: str
    provenance: Provenance = Provenance.EXPLICIT

    @field_validator("id")
    @classmethod
    def _norm_id(cls, v: str) -> str:
        return v.strip().upper()


class JiraTicketMeta(BaseModel):
    key: str
    summary: str = ""
    issue_type: str = ""
    status: str = ""
    priority: str = ""
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    parent: str = ""
    subtasks: list[str] = Field(default_factory=list)
    linked_issues: list[str] = Field(default_factory=list)
    url: str = ""


class RequirementAnalysis(BaseModel):
    ticket_key: str
    meta: JiraTicketMeta
    description_text: str = ""
    requirements: list[Requirement] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

    # Provenance / provider metadata (filled by the pipeline, not the LLM)
    provider: str = Field(default="", description="MCP | REST | FIXTURE")
    fetched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("ticket_key")
    @classmethod
    def _norm_key(cls, v: str) -> str:
        return v.strip().upper()


# --------------------------------------------------------------------------
# Stage 2 — Test plan
# --------------------------------------------------------------------------
class TestScenario(BaseModel):
    id: str = Field(description="Stable id, e.g. SC-001")
    title: str
    description: str = ""
    requirement_ids: list[str] = Field(default_factory=list)


class TestPlanSection(BaseModel):
    number: int = Field(ge=1, le=12)
    title: str
    content: str


class TestPlan(BaseModel):
    ticket_key: str
    sections: list[TestPlanSection] = Field(default_factory=list)
    scenarios: list[TestScenario] = Field(default_factory=list)

    @field_validator("ticket_key")
    @classmethod
    def _norm_key(cls, v: str) -> str:
        return v.strip().upper()


# --------------------------------------------------------------------------
# Stage 3 — Test cases
# --------------------------------------------------------------------------
class TestStep(BaseModel):
    order: int = Field(ge=1)
    action: str
    expected: str = ""


class TestCase(BaseModel):
    id: str = Field(description="e.g. VWO-48-TC-001")
    jira_key: str
    requirement_ids: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    title: str
    objective: str = ""
    priority: str = Field(default="P2", description="P0 | P1 | P2 | P3")
    test_type: str = "functional"
    preconditions: list[str] = Field(default_factory=list)
    test_data: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(default_factory=list)
    expected_result: str = ""
    automation_candidate: AutomationCandidate = AutomationCandidate.NO
    automation_rationale: str = ""
    tags: list[str] = Field(default_factory=list)
    assumptions_or_blockers: list[str] = Field(default_factory=list)

    @field_validator("id", "jira_key")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class TestCaseSuite(BaseModel):
    ticket_key: str
    test_cases: list[TestCase] = Field(default_factory=list)

    @field_validator("ticket_key")
    @classmethod
    def _norm_key(cls, v: str) -> str:
        return v.strip().upper()


# --------------------------------------------------------------------------
# Stage 4 — Playwright automation
# --------------------------------------------------------------------------
class PlaywrightFile(BaseModel):
    path: str = Field(description="Relative path, e.g. tests/vwo-48.spec.ts")
    content: str


class AutomatedTestLink(BaseModel):
    spec_title: str
    test_case_id: str
    jira_key: str
    requirement_ids: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)


class PlaywrightBundle(BaseModel):
    ticket_key: str
    files: list[PlaywrightFile] = Field(default_factory=list)
    automated_links: list[AutomatedTestLink] = Field(default_factory=list)
    setup_notes: str = ""
    coverage_notes: str = ""
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    readiness: AutomationReadiness = AutomationReadiness.NEEDS_CONFIGURATION

    @field_validator("ticket_key")
    @classmethod
    def _norm_key(cls, v: str) -> str:
        return v.strip().upper()


# --------------------------------------------------------------------------
# Deterministic traceability (computed in Python, never by the LLM)
# --------------------------------------------------------------------------
class TraceabilityRow(BaseModel):
    requirement_id: str
    acceptance_criterion_id: str = ""
    test_case_ids: list[str] = Field(default_factory=list)
    automated_test_ids: list[str] = Field(default_factory=list)
    coverage_status: CoverageStatus = CoverageStatus.NONE
    reason: str = ""


class CoverageReport(BaseModel):
    ticket_key: str
    total_requirements: int = 0
    covered_requirements: int = 0
    total_acceptance_criteria: int = 0
    covered_acceptance_criteria: int = 0
    total_test_cases: int = 0
    automated_test_cases: int = 0
    orphan_requirements: list[str] = Field(default_factory=list)
    orphan_test_cases: list[str] = Field(default_factory=list)
    rows: list[TraceabilityRow] = Field(default_factory=list)

    @property
    def requirement_coverage_pct(self) -> float:
        return round(100.0 * self.covered_requirements / self.total_requirements, 1) if self.total_requirements else 0.0

    @property
    def ac_coverage_pct(self) -> float:
        return (
            round(100.0 * self.covered_acceptance_criteria / self.total_acceptance_criteria, 1)
            if self.total_acceptance_criteria
            else 0.0
        )

    @property
    def automation_pct(self) -> float:
        return round(100.0 * self.automated_test_cases / self.total_test_cases, 1) if self.total_test_cases else 0.0


# --------------------------------------------------------------------------
# Per-ticket + run results
# --------------------------------------------------------------------------
class StageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class StageResult(BaseModel):
    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: str = ""
    finished_at: str = ""
    messages: list[str] = Field(default_factory=list)
    error: str = ""

    def duration_seconds(self) -> float | None:
        if not self.started_at or not self.finished_at:
            return None
        try:
            a = datetime.fromisoformat(self.started_at)
            b = datetime.fromisoformat(self.finished_at)
            return round((b - a).total_seconds(), 2)
        except ValueError:
            return None


class TicketResult(BaseModel):
    ticket_key: str
    status: StageStatus = StageStatus.PENDING
    provider: str = ""
    demo_mode: bool = False
    stages: list[StageResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str = ""

    analysis: RequirementAnalysis | None = None
    test_plan: TestPlan | None = None
    test_suite: TestCaseSuite | None = None
    playwright: PlaywrightBundle | None = None
    coverage: CoverageReport | None = None

    artifact_dir: str = ""
    artifacts: dict[str, str] = Field(default_factory=dict)

    @property
    def automation_readiness(self) -> str:
        return self.playwright.readiness.value if self.playwright else "N/A"

    @property
    def succeeded(self) -> bool:
        return self.status in {StageStatus.COMPLETED, StageStatus.WARNING}


class RunResult(BaseModel):
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    integration_mode: str = "auto"
    demo_mode: bool = False
    requested_tickets: list[str] = Field(default_factory=list)
    tickets: list[TicketResult] = Field(default_factory=list)
    run_dir: str = ""
    zip_path: str = ""

    @property
    def completed(self) -> list[TicketResult]:
        return [t for t in self.tickets if t.status == StageStatus.COMPLETED]

    @property
    def completed_with_warnings(self) -> list[TicketResult]:
        return [t for t in self.tickets if t.status == StageStatus.WARNING]

    @property
    def failed(self) -> list[TicketResult]:
        return [t for t in self.tickets if t.status == StageStatus.FAILED]

    @property
    def is_successful(self) -> bool:
        return any(t.succeeded for t in self.tickets)
