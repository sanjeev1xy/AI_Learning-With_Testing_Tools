"""Jira QA Crew — Streamlit entry point.

Run:  streamlit run app.py
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from jira_qa_crew.config import reload_config  # noqa: E402
from jira_qa_crew.crew.callbacks import ProgressTracker  # noqa: E402
from jira_qa_crew.logging_utils import configure_logging  # noqa: E402
from jira_qa_crew.services.artifacts import list_runs, load_run  # noqa: E402
from jira_qa_crew.services.pipeline import run_pipeline  # noqa: E402
from jira_qa_crew.services.reconstruct import backfill_snapshots  # noqa: E402
from jira_qa_crew.ui import components as C  # noqa: E402
from jira_qa_crew.ui import results as Results  # noqa: E402
from jira_qa_crew.ui import state as S  # noqa: E402

st.set_page_config(page_title="Jira QA Crew", page_icon="🧪", layout="wide")
configure_logging()

CONFIG = reload_config()

C.header()
C.demo_banner(CONFIG)

left, right = st.columns([2, 1], gap="large")

with right:
    C.readiness_panel(CONFIG)

with left:
    form = C.input_area(CONFIG)

# -- Previous runs (survive websocket drops / page reloads) --------------
with contextlib.suppress(Exception):  # snapshot backfill is best-effort
    backfill_snapshots(CONFIG.output_dir)
_runs = list_runs(CONFIG.output_dir)
if _runs:
    with st.expander(f"📂 Previous runs ({len(_runs)})", expanded=not S.get_run()):
        labels = {p.name: p for p in _runs}
        choice = st.selectbox("Load a completed run from disk", ["—", *labels.keys()], key="prev_run")
        if choice != "—":
            loaded = load_run(labels[choice])
            if loaded:
                S.set_run(loaded)
                st.caption(f"Loaded {choice}.")

progress_area = st.container()

if form["clicked"] and form["parsed"] and form["parsed"].valid:
    S.clear_run()
    tickets = form["parsed"].valid
    with progress_area:
        st.subheader("3 · Pipeline execution")
        overall = st.progress(0.0, text="Starting…")
        boards: dict[str, st.delta_generator.DeltaGenerator] = {t: st.empty() for t in tickets}
        done = {"n": 0}

        def _progress(key: str, tracker: ProgressTracker) -> None:
            stages = tracker.ordered()
            with boards[key].container():
                st.markdown(f"### {key}")
                C.stage_board(stages, title=f"CrewAI stages — {key}")
            terminal = {"COMPLETED", "WARNING", "FAILED"}
            completed = sum(1 for s in stages if s.status.value in terminal)
            running = any(s.status.value == "RUNNING" for s in stages)
            frac = (done["n"] + completed / 4) / len(tickets)
            overall.progress(min(frac, 1.0), text=f"{key}: {'running' if running else 'working'}…")

        try:
            with st.spinner("Running CrewAI pipeline… this calls the real LLM and can take a few minutes."):
                run = run_pipeline(form["raw"], mode=form["mode"], progress=_progress)
            S.set_run(run)
            overall.progress(1.0, text="Done.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Pipeline failed: {exc}")

run = S.get_run()
if run is None and _runs:
    # Auto-restore the most recent completed run so results are never lost.
    run = load_run(_runs[0])
    if run:
        S.set_run(run)

if run:
    st.divider()
    if not (form["clicked"]):
        st.caption(f"Showing run **{run.run_id}** (loaded from `{run.run_dir}`).")
    Results.render_run(run)
else:
    st.divider()
    st.info("Enter one or more Jira ticket IDs and click **Analyze & Generate QA Pack** to start.")
