"""Assemble fresh, isolated per-stage CrewAI crews for a single ticket."""

from __future__ import annotations

from dataclasses import dataclass

from crewai import LLM, Agent, Crew, Process
from pydantic import BaseModel

from ..jira.gateway import FetchOutcome, JiraGateway
from ..tools.jira_tool import FetchJiraIssueTool
from .agents import build_agents
from .tasks import build_stage_task

_AGENT_FOR_STAGE = {
    "analysis": "jira_analyst",
    "test_plan": "test_plan_writer",
    "test_cases": "test_case_writer",
    "playwright": "playwright_coder",
}


@dataclass
class TicketCrewContext:
    llm: LLM
    ticket_key: str
    agents: dict[str, Agent]
    jira_tool: FetchJiraIssueTool

    def run_stage(
        self,
        stage: str,
        *,
        context_text: str = "",
        callback=None,
        max_rpm: int = 3,
    ) -> tuple[BaseModel | None, str]:
        """Execute one stage as an isolated single-task crew."""
        agent = self.agents[_AGENT_FOR_STAGE[stage]]
        task = build_stage_task(stage, agent, self.ticket_key, context_text=context_text, callback=callback)
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
            max_rpm=max_rpm,
            cache=False,
            memory=False,
        )
        output = crew.kickoff()
        task_out = output.tasks_output[0] if getattr(output, "tasks_output", None) else None
        pydantic = getattr(task_out, "pydantic", None) if task_out else None
        raw = (getattr(task_out, "raw", "") if task_out else "") or ""
        return (pydantic if isinstance(pydantic, BaseModel) else None), raw


def build_ticket_crew_context(
    *,
    llm: LLM,
    ticket_key: str,
    gateway: JiraGateway,
    prefetched: FetchOutcome | None,
) -> TicketCrewContext:
    jira_tool = FetchJiraIssueTool(gateway=gateway, allowed_key=ticket_key, prefetched=prefetched)
    agents = build_agents(llm, ticket_key, jira_tool)
    return TicketCrewContext(llm=llm, ticket_key=ticket_key, agents=agents, jira_tool=jira_tool)
