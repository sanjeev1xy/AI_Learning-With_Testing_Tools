"""CrewAI task construction. Prompt text lives in ../prompts/tasks.yaml.

Each stage runs as its own single-task crew. Rather than letting CrewAI dump the
full raw output of every previous task into the next prompt (which blows small
free-tier token budgets), the pipeline passes a compact, deterministically
rendered summary of prior stages via ``context_text``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from crewai import Agent, Task

from ..models import PlaywrightBundle, RequirementAnalysis, TestCaseSuite, TestPlan

_PROMPTS = Path(__file__).resolve().parent.parent / "prompts" / "tasks.yaml"

STAGE_MODELS = {
    "analysis": RequirementAnalysis,
    "test_plan": TestPlan,
    "test_cases": TestCaseSuite,
    "playwright": PlaywrightBundle,
}


@lru_cache(maxsize=1)
def _task_specs() -> dict:
    return yaml.safe_load(_PROMPTS.read_text(encoding="utf-8"))


def _fmt(text: str, ticket_key: str) -> str:
    return text.format(ticket_key=ticket_key, ticket_key_lower=ticket_key.lower()).strip()


def build_stage_task(
    stage: str,
    agent: Agent,
    ticket_key: str,
    *,
    context_text: str = "",
    callback=None,
) -> Task:
    spec = _task_specs()[stage]
    description = _fmt(spec["description"], ticket_key)
    if context_text:
        description = f"{description}\n\n--- CONTEXT FROM PRIOR STAGES ---\n{context_text}\n--- END CONTEXT ---"
    kwargs: dict = {
        "description": description,
        "expected_output": _fmt(spec["expected_output"], ticket_key),
        "agent": agent,
        "callback": callback,
        "markdown": False,
    }
    # The Playwright stage emits free-form markdown with fenced .ts code blocks and
    # is parsed deterministically in Python. Forcing a strict JSON schema with large
    # embedded code strings is fragile on small models / strict-schema providers.
    if stage != "playwright":
        kwargs["output_pydantic"] = STAGE_MODELS[stage]
    return Task(**kwargs)
