"""MCP server exposing the VWO manual QA test-case dataset as Tools, Resources and Prompts."""

from __future__ import annotations

import csv
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any, Literal
from urllib.parse import unquote

from fastmcp import FastMCP
from fastmcp.exceptions import FastMCPError, PromptError, ResourceError, ToolError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("testcase-creator-mcp")

CSV_NAME = "VWO_test_cases.csv"
CSV_ENV_VAR = "VWO_TESTCASES_CSV"
COLUMNS = ("id", "jira_id", "priority", "module", "title", "steps", "expected", "tags")
TEXT_FIELDS = ("title", "steps", "expected")

TestCase = dict[str, Any]


def _resolve_csv_path() -> Path:
    """Locate the dataset via env override, else relative to this file."""
    override = os.environ.get(CSV_ENV_VAR)
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise RuntimeError(f"{CSV_ENV_VAR} points at {path}, which is not a readable file.")
        return path
    here = Path(__file__).resolve().parent
    for candidate in (here / "resource" / CSV_NAME, here.parent / "resource" / CSV_NAME):
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        f"Dataset {CSV_NAME} not found under {here / 'resource'} or {here.parent / 'resource'}. "
        f"Set {CSV_ENV_VAR} to an explicit path."
    )


def _load_cases(path: Path) -> list[TestCase]:
    """Read every row of the CSV into memory, splitting the semicolon-delimited tags column."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or ())]
        if missing:
            raise RuntimeError(f"{path.name} is missing required column(s): {', '.join(missing)}.")
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"{path.name} has a header but no test-case rows.")
    return [
        {
            **{col: (row[col] or "").strip() for col in COLUMNS if col != "tags"},
            "tags": [tag.strip() for tag in (row["tags"] or "").split(";") if tag.strip()],
        }
        for row in rows
    ]


try:
    CSV_PATH = _resolve_csv_path()
    CASES: list[TestCase] = _load_cases(CSV_PATH)
except (RuntimeError, OSError, csv.Error) as exc:
    logger.error("Startup aborted: %s", exc)
    raise SystemExit(1) from None

BY_KEY: dict[str, TestCase] = {c["id"].lower(): c for c in CASES} | {c["jira_id"].lower(): c for c in CASES}
MODULES: list[str] = sorted({c["module"] for c in CASES})
PRIORITIES: list[str] = sorted({c["priority"] for c in CASES})
TAGS: list[str] = sorted({tag for c in CASES for tag in c["tags"]})
logger.info("Loaded %d test cases from %s", len(CASES), CSV_PATH)

SCHEMA: dict[str, Any] = {
    "source": CSV_PATH.name,
    "row_count": len(CASES),
    "columns": {
        "id": {"type": "string", "description": "Unique test-case key, e.g. TC-00001."},
        "jira_id": {"type": "string", "description": "Linked Jira issue key, e.g. VWO-1001."},
        "priority": {"type": "string", "enum": PRIORITIES, "description": "Severity band."},
        "module": {"type": "string", "enum": MODULES, "description": "Owning product area."},
        "title": {"type": "string", "description": "One-line summary of the case."},
        "steps": {"type": "string", "description": "Newline-separated numbered reproduction steps."},
        "expected": {"type": "string", "description": "Expected result assertion."},
        "tags": {"type": "array[string]", "enum": TAGS, "description": "Labels, split from a semicolon-delimited cell."},
    },
}

mcp = FastMCP(
    name="vwo-testcases",
    instructions=(
        "Read-only access to a VWO manual QA test-case export. Use tools to search, fetch and "
        "aggregate cases; read resources for schema and bulk context; use prompts to review a "
        "case or draft a regression suite."
    ),
)


def _resolve_choice(value: str, allowed: list[str], label: str, err: type[FastMCPError] = ToolError) -> str:
    """Case-insensitively map a supplied facet value onto a known value, or raise a readable MCP error."""
    match = {a.lower(): a for a in allowed}.get(unquote(value).strip().lower())
    if match is None:
        raise err(f"Unknown {label} {value!r}. Valid values: {', '.join(allowed)}.")
    return match


def _lookup(test_id: str, err: type[FastMCPError] = ToolError) -> TestCase:
    """Fetch one case by id or jira_id, or raise a readable MCP error."""
    case = BY_KEY.get(unquote(test_id).strip().lower())
    if case is None:
        raise err(f"Unknown test case {test_id!r}. Expected an id like TC-00001 or a jira_id like VWO-1001.")
    return case


@mcp.tool
def search_test_cases(
    query: str = "",
    module: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    limit: int = 20,
) -> list[TestCase]:
    """Search test cases by free text across title/steps/expected, with optional module, priority and tag filters."""
    if not 1 <= limit <= len(CASES):
        raise ToolError(f"limit must be between 1 and {len(CASES)}, got {limit}.")
    wanted_module = _resolve_choice(module, MODULES, "module") if module else None
    wanted_priority = _resolve_choice(priority, PRIORITIES, "priority") if priority else None
    wanted_tag = _resolve_choice(tag, TAGS, "tag") if tag else None

    needle = query.strip().lower()
    hits = [
        case
        for case in CASES
        if (not needle or any(needle in case[field].lower() for field in TEXT_FIELDS))
        and (wanted_module is None or case["module"] == wanted_module)
        and (wanted_priority is None or case["priority"] == wanted_priority)
        and (wanted_tag is None or wanted_tag in case["tags"])
    ]
    if not hits:
        raise ToolError(
            f"No test cases matched query={query!r}, module={module!r}, priority={priority!r}, tag={tag!r}. "
            "Call list_facets to see the valid filter values."
        )
    return hits[:limit]


@mcp.tool
def get_test_case(test_id: str) -> TestCase:
    """Return a single test case by its id (TC-00001) or its jira_id (VWO-1001)."""
    return _lookup(test_id)


@mcp.tool
def test_case_stats(group_by: Literal["module", "priority", "tag"] = "module") -> dict[str, Any]:
    """Count test cases grouped by module, priority or tag, ordered by descending count."""
    if group_by == "tag":
        counter = Counter(tag for case in CASES for tag in case["tags"])
    else:
        counter = Counter(case[group_by] for case in CASES)
    return {
        "group_by": group_by,
        "total_cases": len(CASES),
        "distinct_groups": len(counter),
        "counts": dict(counter.most_common()),
    }


@mcp.tool
def list_facets() -> dict[str, list[str]]:
    """List every valid module, priority and tag value accepted by the search and stats tools."""
    return {"modules": MODULES, "priorities": PRIORITIES, "tags": TAGS}


@mcp.resource("testcases://schema", mime_type="application/json")
def schema_resource() -> dict[str, Any]:
    """Column names, inferred types and enumerated values for the test-case dataset."""
    return SCHEMA


@mcp.resource("testcases://all", mime_type="application/json")
def all_cases_resource() -> list[TestCase]:
    """The complete test-case dataset as JSON."""
    return CASES


@mcp.resource("testcases://module/{name}", mime_type="application/json")
def cases_by_module_resource(name: str) -> list[TestCase]:
    """All test cases belonging to a given module."""
    wanted = _resolve_choice(name, MODULES, "module", ResourceError)
    return [case for case in CASES if case["module"] == wanted]


@mcp.resource("testcases://case/{test_id}", mime_type="application/json")
def case_resource(test_id: str) -> TestCase:
    """One test case addressed by its id or jira_id."""
    return _lookup(test_id, ResourceError)


@mcp.prompt
def review_test_case(test_id: str) -> str:
    """Prompt template that asks the model to critique one test case for coverage and clarity."""
    case = _lookup(test_id, PromptError)
    return (
        "You are a senior QA lead reviewing one manual test case.\n\n"
        f"ID: {case['id']}  (Jira {case['jira_id']})\n"
        f"Module: {case['module']}\nPriority: {case['priority']}\n"
        f"Tags: {', '.join(case['tags']) or 'none'}\n"
        f"Title: {case['title']}\n\nSteps:\n{case['steps']}\n\n"
        f"Expected result: {case['expected']}\n\n"
        "Critique it on: (1) coverage gaps and missing negative or boundary paths, "
        "(2) clarity and reproducibility of the steps, (3) whether the expected result is a "
        "single verifiable assertion, (4) whether the priority and tags fit the described risk. "
        "Finish with a rewritten version of the case that fixes every issue you raised."
    )


@mcp.prompt
def generate_regression_suite(module: str) -> str:
    """Prompt template that turns one module's test cases into an ordered regression suite."""
    wanted = _resolve_choice(module, MODULES, "module", PromptError)
    cases = [case for case in CASES if case["module"] == wanted]
    inventory = "\n".join(
        f"- {c['id']} [{c['priority']}] {c['title']} (tags: {', '.join(c['tags']) or 'none'})" for c in cases
    )
    return (
        f"You are building a regression suite for the {wanted!r} module from {len(cases)} existing manual "
        f"test cases.\n\nInventory:\n{inventory}\n\n"
        "Produce: (1) a smoke tier of the cases that must pass before any deeper testing, ordered by "
        "execution dependency, (2) a full regression tier with an estimated runtime per case, "
        "(3) the coverage gaps this module still has, written as new cases in the same "
        "id/priority/title/steps/expected shape, (4) which cases are automation candidates and why. "
        f"Use only these {len(cases)} cases as the existing baseline; do not invent history for them."
    )


if __name__ == "__main__":
    mcp.run()
