"""End-to-end orchestration: ticket input -> 4 CrewAI agents -> artifacts."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from ..config import AppConfig, reload_config
from ..crew.callbacks import ProgressTracker
from ..crew.factory import build_ticket_crew_context
from ..crew.llm import build_llm
from ..exceptions import JiraError, PipelineError
from ..jira.gateway import JiraGateway
from ..logging_utils import get_logger, redact
from ..models import (
    PlaywrightBundle,
    RequirementAnalysis,
    RunResult,
    StageStatus,
    TestCaseSuite,
    TestPlan,
    TicketResult,
)
from . import artifacts as artifacts_mod
from . import renderers as R
from . import validation as V
from .playwright_parse import parse_playwright_markdown
from .ticket_parser import parse_ticket_input
from .traceability import build_coverage

logger = get_logger("services.pipeline")

ProgressHook = Callable[[str, ProgressTracker], None]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _apply_mode_override(mode: str | None) -> AppConfig:
    if mode:
        os.environ["JIRA_INTEGRATION_MODE"] = mode
    return reload_config()


def _repair(llm, raw_text: str, model_cls: type[BaseModel]) -> BaseModel:
    """One controlled repair attempt for malformed structured output."""
    schema = json.dumps(model_cls.model_json_schema())
    prompt = (
        "The following text should be a single JSON object matching this JSON schema.\n"
        f"SCHEMA:\n{schema}\n\nTEXT:\n{raw_text}\n\n"
        "Return ONLY the corrected JSON object, no prose, no code fences."
    )
    reply = llm.call(prompt)
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise PipelineError(f"Repair produced no JSON for {model_cls.__name__}.")
    return model_cls.model_validate_json(match.group(0))


def _run_stage_validation(kind: str, obj, *args) -> V.ValidationOutcome:
    return {
        "analysis": V.validate_analysis,
        "plan": V.validate_plan,
        "cases": V.validate_cases,
        "playwright": V.validate_playwright,
    }[kind](obj, *args)


def process_ticket(
    ticket_key: str,
    *,
    llm,
    gateway: JiraGateway,
    config: AppConfig,
    hook: Callable[[ProgressTracker], None] | None = None,
) -> TicketResult:
    tracker = ProgressTracker(ticket_key, hook)
    result = TicketResult(ticket_key=ticket_key, stages=tracker.ordered())

    # -- Stage 0: deterministic Jira fetch (provider decision, provenance) --
    tracker.start("Jira Analyst", "Fetching Jira issue via gateway")
    try:
        outcome = gateway.fetch(ticket_key)
    except JiraError as exc:
        tracker.fail("Jira Analyst", f"Jira fetch failed: {exc}")
        result.status = StageStatus.FAILED
        result.error = redact(str(exc))
        result.stages = tracker.ordered()
        return result

    result.provider = outcome.provider
    result.demo_mode = outcome.demo
    for note in outcome.notes:
        tracker.note("Jira Analyst", note)

    ctx = build_ticket_crew_context(llm=llm, ticket_key=ticket_key, gateway=gateway, prefetched=outcome)

    all_warnings: list[str] = []
    models: dict[str, BaseModel] = {}

    stage_plan = [
        ("Jira Analyst", "analysis", RequirementAnalysis),
        ("Test Plan Writer", "test_plan", TestPlan),
        ("Test Case Writer", "test_cases", TestCaseSuite),
        ("Playwright Coder", "playwright", PlaywrightBundle),
    ]

    for stage_name, stage_key, model_cls in stage_plan:
        if stage_name != "Jira Analyst":
            tracker.start(stage_name, "agent running")

        context_text = _stage_context(stage_key, models, outcome)
        obj, raw, exc = _run_stage_with_retry(
            ctx, stage_key, context_text, _stage_note_callback(tracker, stage_name),
            attempts=1 + max(0, config.max_retries), tracker=tracker, stage_name=stage_name,
            max_rpm=config.max_rpm,
        )
        if exc is not None:
            msg = redact(str(exc))
            tracker.fail(stage_name, f"CrewAI execution failed: {msg}")
            result.status = StageStatus.FAILED
            result.error = f"{stage_name}: {msg}"
            result.stages = tracker.ordered()
            return result

        if stage_key == "playwright":
            # The Playwright stage returns markdown; parse it deterministically.
            obj = parse_playwright_markdown(raw, ticket_key, models["test_cases"])  # type: ignore[arg-type]
            tracker.note(stage_name, f"parsed {len(obj.files)} spec file(s) from agent markdown")
        elif not isinstance(obj, model_cls):
            tracker.note(stage_name, "structured output missing — attempting one repair")
            try:
                obj = _repair(llm, raw, model_cls)
            except (PipelineError, ValidationError) as exc:
                tracker.fail(stage_name, f"structured output invalid: {redact(str(exc))}")
                result.status = StageStatus.FAILED
                result.error = f"{stage_name}: invalid structured output."
                result.stages = tracker.ordered()
                return result

        if stage_key == "analysis":
            obj = _finalize_analysis(obj, outcome)
            vo = _run_stage_validation("analysis", obj, ticket_key)
        elif stage_key == "test_plan":
            vo = _run_stage_validation("plan", obj, models["analysis"])
        elif stage_key == "test_cases":
            vo = _run_stage_validation("cases", obj, models["analysis"])
        else:
            vo = _run_stage_validation("playwright", obj, models["test_cases"])

        if not vo.ok:
            tracker.fail(stage_name, "; ".join(vo.problems))
            result.status = StageStatus.FAILED
            result.error = f"{stage_name} validation failed: {'; '.join(vo.problems)}"
            result.stages = tracker.ordered()
            return result

        for w in vo.warnings:
            tracker.note(stage_name, f"warning: {w}")
        all_warnings.extend(f"[{stage_name}] {w}" for w in vo.warnings)
        models[stage_key] = obj
        # Persist each validated stage immediately, so a later-stage failure still
        # leaves the earlier artifacts available in the UI.
        result.analysis = models.get("analysis")  # type: ignore[assignment]
        result.test_plan = models.get("test_plan")  # type: ignore[assignment]
        result.test_suite = models.get("test_cases")  # type: ignore[assignment]
        result.playwright = models.get("playwright")  # type: ignore[assignment]
        if result.analysis and result.test_suite:
            result.coverage = build_coverage(result.analysis, result.test_suite, result.playwright)
        tracker.complete(stage_name, f"{model_cls.__name__} validated", warning=bool(vo.warnings))

    result.warnings = all_warnings
    result.status = StageStatus.WARNING if all_warnings else StageStatus.COMPLETED
    result.stages = tracker.ordered()
    return result


def _run_stage_with_retry(ctx, stage_key, context_text, callback, *, attempts, tracker, stage_name, max_rpm=3):
    """Run a stage; on failure retry up to ``attempts`` times. Returns (obj, raw, exc)."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            obj, raw = ctx.run_stage(
                stage_key, context_text=context_text, callback=callback, max_rpm=max_rpm
            )
            return obj, raw, None
        except Exception as exc:  # noqa: BLE001 - retry any crew/LLM failure once or twice
            last_exc = exc
            if i + 1 < attempts:
                tracker.note(stage_name, f"attempt {i + 1} failed ({redact(str(exc))[:120]}); retrying")
                time.sleep(3)
    return None, "", last_exc


def _stage_context(stage_key: str, models: dict[str, BaseModel], outcome) -> str:
    if stage_key == "analysis":
        return outcome.issue.to_prompt_text()
    if stage_key == "test_plan":
        return R.analysis_context(models["analysis"])  # type: ignore[arg-type]
    if stage_key == "test_cases":
        return R.analysis_context(models["analysis"]) + "\n\n" + R.plan_context(models["test_plan"])  # type: ignore[arg-type]
    return R.cases_context_for_playwright(models["test_cases"])  # type: ignore[arg-type]


def _stage_note_callback(tracker: ProgressTracker, stage_name: str):
    def _cb(task_output) -> None:  # noqa: ANN001
        chars = len(getattr(task_output, "raw", "") or "")
        tracker.note(stage_name, f"agent produced {chars} chars; validating")

    return _cb


def _finalize_analysis(obj: RequirementAnalysis, outcome) -> RequirementAnalysis:
    issue = outcome.issue
    obj.provider = outcome.provider
    if not obj.meta or not obj.meta.key:
        obj.meta.key = issue.key
    # Trust the deterministically fetched metadata over the LLM copy.
    obj.meta.key = issue.key
    obj.meta.summary = obj.meta.summary or issue.summary
    obj.meta.url = issue.url
    if not obj.meta.labels:
        obj.meta.labels = issue.labels
    if not obj.meta.components:
        obj.meta.components = issue.components
    if not obj.description_text:
        obj.description_text = issue.description
    return obj


def run_pipeline(
    raw_ticket_input: str,
    *,
    mode: str | None = None,
    progress: Callable[[str, ProgressTracker], None] | None = None,
    output_root: Path | None = None,
) -> RunResult:
    config = _apply_mode_override(mode)
    parsed = parse_ticket_input(raw_ticket_input, max_tickets=config.max_tickets)
    if not parsed.has_valid:
        raise PipelineError(
            f"No valid Jira ticket ids found. Invalid tokens: {parsed.invalid or '(none)'}"
        )

    run_id = artifacts_mod.new_run_id()
    root = (output_root or config.output_dir).resolve()
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    run = RunResult(
        run_id=run_id,
        integration_mode=config.integration_mode,
        demo_mode=config.effective_demo_mode(),
        requested_tickets=parsed.valid,
        run_dir=str(run_dir),
    )

    llm = build_llm(config)
    gateway = JiraGateway(config)

    for key in parsed.valid:
        logger.info("=== Processing %s ===", key)
        started = time.time()

        def _hook(tracker: ProgressTracker, _key=key) -> None:
            if progress:
                progress(_key, tracker)

        try:
            ticket_result = process_ticket(key, llm=llm, gateway=gateway, config=config, hook=_hook)
        except Exception as exc:  # noqa: BLE001 - one ticket must never kill the run
            logger.exception("Unhandled error processing %s", key)
            ticket_result = TicketResult(
                ticket_key=key, status=StageStatus.FAILED, error=redact(str(exc))
            )

        try:
            if ticket_result.analysis:
                artifacts_mod.write_ticket_artifacts(run_dir, ticket_result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Artifact write failed for %s", key)
            ticket_result.warnings.append(f"Artifact write failed: {redact(str(exc))}")

        logger.info("%s finished in %.1fs -> %s", key, time.time() - started, ticket_result.status.value)
        run.tickets.append(ticket_result)
        if progress:
            progress(key, ProgressTracker(key))  # nudge UI

    artifacts_mod.write_run_summary(run)
    try:
        artifacts_mod.build_zip(run)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ZIP build failed: %s", redact(str(exc)))

    return run
