"""Headless pipeline smoke test — runs the full 4-agent CrewAI pipeline.

Usage:
    python run_demo.py VWO-48
    python run_demo.py "VWO-48, VWO-49"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from jira_qa_crew.config import get_config  # noqa: E402
from jira_qa_crew.crew.callbacks import ProgressTracker  # noqa: E402
from jira_qa_crew.logging_utils import configure_logging  # noqa: E402
from jira_qa_crew.services.pipeline import run_pipeline  # noqa: E402


def _progress(key: str, tracker: ProgressTracker) -> None:
    stages = " | ".join(f"{s.name.split()[0]}:{s.status.value[:4]}" for s in tracker.ordered())
    print(f"  [{key}] {stages}")


def main() -> int:
    configure_logging("INFO")
    raw = sys.argv[1] if len(sys.argv) > 1 else "VWO-48"
    cfg = get_config()
    print(f"LLM configured: {cfg.llm.configured} ({cfg.llm.model})")
    print(f"Integration mode: {cfg.integration_mode} | effective demo mode: {cfg.effective_demo_mode()}")
    print(f"Processing: {raw}\n")

    run = run_pipeline(raw, progress=_progress)

    print("\n=== RUN SUMMARY ===")
    print(f"Run ID: {run.run_id}")
    print(f"Run dir: {run.run_dir}")
    print(f"ZIP: {run.zip_path}")
    for t in run.tickets:
        print(f"\n{t.ticket_key}: {t.status.value} | source={t.provider} demo={t.demo_mode} "
              f"| automation={t.automation_readiness}")
        if t.coverage:
            c = t.coverage
            print(f"  requirements {c.covered_requirements}/{c.total_requirements}, "
                  f"AC {c.covered_acceptance_criteria}/{c.total_acceptance_criteria}, "
                  f"test cases {c.total_test_cases} (automated {c.automated_test_cases})")
        if t.warnings:
            print(f"  {len(t.warnings)} warnings")
        for name in sorted(t.artifacts):
            print(f"  - {name}")
        if t.error:
            print(f"  ERROR: {t.error}")

    return 0 if run.is_successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
