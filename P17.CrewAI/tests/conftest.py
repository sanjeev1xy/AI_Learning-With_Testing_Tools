from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Force a clean, offline test baseline. Setting these (even to "") means
# python-dotenv's load_dotenv(override=False) will NOT pull real values from a
# developer's .env, so tests never touch a live Jira / paid LLM.
os.environ["DEMO_MODE"] = "true"
os.environ["DEMO_ALLOW_SYNTHETIC"] = "true"
os.environ["LLM_MODEL"] = "openai/test-model"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_BASE_URL"] = "https://example.invalid/v1"
os.environ["LLM_REASONING_EFFORT"] = ""
for _k in (
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_BEARER_TOKEN",
    "JIRA_MCP_URL",
    "JIRA_MCP_COMMAND",
    "JIRA_ACCEPTANCE_CRITERIA_FIELD",
):
    os.environ[_k] = ""
os.environ["JIRA_INTEGRATION_MODE"] = "auto"
os.environ.setdefault("OUTPUT_DIR", str(ROOT / "outputs"))


@pytest.fixture(autouse=True)
def _reset_config():
    from jira_qa_crew.config import get_config

    get_config.cache_clear()
    yield
    get_config.cache_clear()


@pytest.fixture
def sample_analysis():
    from jira_qa_crew.models import (
        AcceptanceCriterion,
        JiraTicketMeta,
        Requirement,
        RequirementAnalysis,
    )

    return RequirementAnalysis(
        ticket_key="VWO-48",
        meta=JiraTicketMeta(key="VWO-48", summary="Cart total shows $0.00"),
        description_text="Cart total is wrong for 3+ items.",
        requirements=[
            Requirement(id="REQ-001", text="Total must equal subtotal minus discount for 3+ items"),
            Requirement(id="REQ-002", text="Total must never render as $0.00 when API returns non-zero"),
        ],
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001", text="3+ items + code -> correct discounted total"),
            AcceptanceCriterion(id="AC-002", text="never $0.00 when API non-zero"),
        ],
        missing_information=["Exact selector for the order-summary total element"],
        provider="FIXTURE",
    )


@pytest.fixture
def sample_suite():
    from jira_qa_crew.models import TestCase, TestCaseSuite, TestStep

    return TestCaseSuite(
        ticket_key="VWO-48",
        test_cases=[
            TestCase(
                id="VWO-48-TC-001",
                jira_key="VWO-48",
                requirement_ids=["REQ-001"],
                acceptance_criteria_ids=["AC-001"],
                title="Discounted total correct with 3 items",
                steps=[TestStep(order=1, action="Add 3 items", expected="cart has 3 items")],
                expected_result="Total = subtotal - 20%",
                automation_candidate="Yes",
                automation_rationale="UI assertion",
            ),
            TestCase(
                id="VWO-48-TC-002",
                jira_key="VWO-48",
                requirement_ids=["REQ-002"],
                acceptance_criteria_ids=["AC-002"],
                title="Total never zero",
                steps=[TestStep(order=1, action="Apply code", expected="total updates")],
                expected_result="Total != $0.00",
                automation_candidate="No",
                automation_rationale="Needs API stub",
            ),
        ],
    )
