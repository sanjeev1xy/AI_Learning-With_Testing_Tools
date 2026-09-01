"""Write per-ticket artifacts to disk, build manifests and the ZIP package.

Every path segment derived from user input is sanitised; ticket input can never
create arbitrary paths or traverse directories.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from ..logging_utils import get_logger
from ..models import RunResult, TicketResult
from . import renderers as R

logger = get_logger("services.artifacts")

_SAFE_SEGMENT = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_segment(value: str) -> str:
    cleaned = _SAFE_SEGMENT.sub("_", (value or "").strip())
    cleaned = cleaned.strip("._") or "unnamed"
    return cleaned[:80]


def _safe_join(root: Path, *segments: str) -> Path:
    path = root
    for seg in segments:
        path = path / sanitize_segment(seg)
    resolved = path.resolve()
    if not str(resolved).startswith(str(root.resolve())):
        raise ValueError(f"Unsafe artifact path: {resolved}")
    return resolved


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"RUN-{now.strftime('%Y%m%d-%H%M%S')}"


def write_ticket_artifacts(run_dir: Path, ticket: TicketResult) -> dict[str, str]:
    """Render and persist every artifact for one ticket. Returns name -> abs path."""
    tdir = _safe_join(run_dir, ticket.ticket_key)
    (tdir / "playwright" / "tests").mkdir(parents=True, exist_ok=True)
    (tdir / "playwright" / "pages").mkdir(parents=True, exist_ok=True)
    (tdir / "playwright" / "fixtures").mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}

    def _write(rel: str, content: str) -> None:
        target = _safe_join(tdir, *rel.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        written[rel] = str(target)

    if ticket.analysis:
        _write("requirements_analysis.md", R.analysis_to_markdown(ticket.analysis))
        _write("requirements_analysis.json", R.analysis_to_json(ticket.analysis))
    if ticket.test_plan:
        _write("test_plan.md", R.plan_to_markdown(ticket.test_plan))
    if ticket.test_suite:
        _write("test_cases.md", R.cases_to_markdown(ticket.test_suite))
        _write("test_cases.csv", R.cases_to_csv(ticket.test_suite))
    if ticket.coverage:
        _write("traceability_matrix.csv", R.traceability_to_csv(ticket.coverage))
        _write("traceability_matrix.md", R.coverage_to_markdown(ticket.coverage))
    if ticket.playwright:
        _write("playwright_tests.md", R.playwright_to_markdown(ticket.playwright))
        _write("playwright/playwright.config.ts", R.playwright_config_ts())
        _write("playwright/package.json", R.playwright_package_json(ticket.ticket_key))
        _write("playwright/tsconfig.json", R.playwright_tsconfig_json())
        for f in ticket.playwright.files:
            rel_parts = [sanitize_segment(p) for p in f.path.split("/") if p not in ("", ".", "..")]
            if not rel_parts:
                continue
            if not rel_parts[-1].endswith((".ts", ".tsx")):
                rel_parts[-1] += ".ts"
            if len(rel_parts) == 1:
                rel_parts = ["tests", rel_parts[0]]
            _write("playwright/" + "/".join(rel_parts), f.content.rstrip() + "\n")

    manifest = _ticket_manifest(ticket, written)
    _write("manifest.json", json.dumps(manifest, indent=2))
    ticket.artifact_dir = str(tdir)
    ticket.artifacts = written
    logger.info("Wrote %d artifacts for %s", len(written), ticket.ticket_key)
    return written


def _ticket_manifest(ticket: TicketResult, written: dict[str, str]) -> dict:
    cov = ticket.coverage
    return {
        "ticket_key": ticket.ticket_key,
        "status": ticket.status.value,
        "provider": ticket.provider,
        "demo_mode": ticket.demo_mode,
        "automation_readiness": ticket.automation_readiness,
        "warnings": ticket.warnings,
        "artifacts": sorted(written.keys()),
        "coverage": None
        if not cov
        else {
            "requirements": f"{cov.covered_requirements}/{cov.total_requirements}",
            "acceptance_criteria": f"{cov.covered_acceptance_criteria}/{cov.total_acceptance_criteria}",
            "test_cases": cov.total_test_cases,
            "automated_test_cases": cov.automated_test_cases,
            "orphan_requirements": cov.orphan_requirements,
            "orphan_test_cases": cov.orphan_test_cases,
        },
        "stages": [
            {"name": s.name, "status": s.status.value, "duration_seconds": s.duration_seconds()}
            for s in ticket.stages
        ],
    }


def write_run_summary(run: RunResult) -> dict[str, str]:
    run_dir = Path(run.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Run Summary — {run.run_id}",
        "",
        f"- Created: {run.created_at}",
        f"- Integration mode: {run.integration_mode}",
        f"- Demo mode: {run.demo_mode}",
        f"- Tickets requested: {', '.join(run.requested_tickets)}",
        f"- Completed: {len(run.completed)}",
        f"- Completed with warnings: {len(run.completed_with_warnings)}",
        f"- Failed: {len(run.failed)}",
        "",
        "| Ticket | Status | Source | Automation | Warnings |",
        "| --- | --- | --- | --- | --- |",
    ]
    for t in run.tickets:
        lines.append(
            f"| {t.ticket_key} | {t.status.value} | {t.provider or '-'}"
            f"{' (DEMO)' if t.demo_mode else ''} | {t.automation_readiness} | {len(t.warnings)} |"
        )
    lines.append("")
    for t in run.tickets:
        if t.error:
            lines.append(f"- **{t.ticket_key} error:** {t.error}")
    summary_md = "\n".join(lines)
    (run_dir / "run_summary.md").write_text(summary_md, encoding="utf-8", newline="\n")

    manifest = {
        "run_id": run.run_id,
        "created_at": run.created_at,
        "integration_mode": run.integration_mode,
        "demo_mode": run.demo_mode,
        "requested_tickets": run.requested_tickets,
        "successful": run.is_successful,
        "tickets": [_ticket_manifest(t, t.artifacts) for t in run.tickets],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")

    # Full RunResult snapshot so the UI can restore results after a websocket drop
    # or a fresh page load (the pipeline can take minutes).
    (run_dir / "run_result.json").write_text(run.model_dump_json(indent=2), encoding="utf-8", newline="\n")

    return {"run_summary.md": str(run_dir / "run_summary.md"), "manifest.json": str(run_dir / "manifest.json")}


def load_run(run_dir: Path) -> RunResult | None:
    snap = Path(run_dir) / "run_result.json"
    if not snap.exists():
        return None
    try:
        return RunResult.model_validate_json(snap.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load run snapshot %s: %s", snap, exc)
        return None


def list_runs(output_dir: Path) -> list[Path]:
    if not Path(output_dir).is_dir():
        return []
    return sorted(
        (p for p in Path(output_dir).glob("RUN-*") if (p / "run_result.json").exists()),
        key=lambda p: p.name,
        reverse=True,
    )


def load_latest_run(output_dir: Path) -> RunResult | None:
    runs = list_runs(output_dir)
    return load_run(runs[0]) if runs else None


def build_zip(run: RunResult) -> str:
    run_dir = Path(run.run_dir)
    zip_path = run_dir / f"{run.run_id}_artifacts.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file() and path != zip_path:
                zf.write(path, path.relative_to(run_dir).as_posix())
    run.zip_path = str(zip_path)
    logger.info("Built ZIP %s", zip_path)
    return str(zip_path)


def zip_bytes(run: RunResult) -> bytes:
    if run.zip_path and Path(run.zip_path).exists():
        return Path(run.zip_path).read_bytes()
    buf = io.BytesIO()
    run_dir = Path(run.run_dir)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(run_dir).as_posix())
    return buf.getvalue()
