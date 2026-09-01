"""CrewAI agent construction. Prompt text lives in ../prompts/agents.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from crewai import LLM, Agent

from ..tools.jira_tool import FetchJiraIssueTool

_PROMPTS = Path(__file__).resolve().parent.parent / "prompts" / "agents.yaml"


@lru_cache(maxsize=1)
def _agent_specs() -> dict:
    return yaml.safe_load(_PROMPTS.read_text(encoding="utf-8"))


def _fmt(value: str, ticket_key: str) -> str:
    return value.format(ticket_key=ticket_key).strip()


def build_agents(llm: LLM, ticket_key: str, jira_tool: FetchJiraIssueTool) -> dict[str, Agent]:
    specs = _agent_specs()
    common = {"llm": llm, "verbose": False, "allow_delegation": False, "max_iter": 6, "cache": False}

    analyst = Agent(
        role=_fmt(specs["jira_analyst"]["role"], ticket_key),
        goal=_fmt(specs["jira_analyst"]["goal"], ticket_key),
        backstory=_fmt(specs["jira_analyst"]["backstory"], ticket_key),
        tools=[jira_tool],
        **common,
    )
    plan_writer = Agent(
        role=_fmt(specs["test_plan_writer"]["role"], ticket_key),
        goal=_fmt(specs["test_plan_writer"]["goal"], ticket_key),
        backstory=_fmt(specs["test_plan_writer"]["backstory"], ticket_key),
        **common,
    )
    case_writer = Agent(
        role=_fmt(specs["test_case_writer"]["role"], ticket_key),
        goal=_fmt(specs["test_case_writer"]["goal"], ticket_key),
        backstory=_fmt(specs["test_case_writer"]["backstory"], ticket_key),
        **common,
    )
    pw_coder = Agent(
        role=_fmt(specs["playwright_coder"]["role"], ticket_key),
        goal=_fmt(specs["playwright_coder"]["goal"], ticket_key),
        backstory=_fmt(specs["playwright_coder"]["backstory"], ticket_key),
        **common,
    )
    return {
        "jira_analyst": analyst,
        "test_plan_writer": plan_writer,
        "test_case_writer": case_writer,
        "playwright_coder": pw_coder,
    }
