"""Render the results area: one tab per ticket, six tabs per ticket."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ..models import RunResult, TicketResult
from ..services import renderers as R
from ..services.artifacts import zip_bytes
from .components import provider_badge, stage_board


def render_run(run: RunResult) -> None:
    st.subheader("Run results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Run ID", run.run_id.replace("RUN-", ""))
    c2.metric("Completed", len(run.completed))
    c3.metric("With warnings", len(run.completed_with_warnings))
    c4.metric("Failed", len(run.failed))

    if run.demo_mode:
        st.warning("This run used **DEMO MODE** fixture data — not live Jira.", icon="🧪")

    summary_rows = [
        {
            "Ticket": t.ticket_key,
            "Status": t.status.value,
            "Source": t.provider + (" (DEMO)" if t.demo_mode else ""),
            "Automation": t.automation_readiness,
            "Warnings": len(t.warnings),
        }
        for t in run.tickets
    ]
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    if run.zip_path and Path(run.zip_path).exists():
        st.download_button(
            "⬇️ Download all artifacts (ZIP)",
            data=zip_bytes(run),
            file_name=f"{run.run_id}_artifacts.zip",
            mime="application/zip",
        )

    if not run.tickets:
        return
    tabs = st.tabs([f"{'✅' if t.succeeded else '❌'} {t.ticket_key}" for t in run.tickets])
    for tab, ticket in zip(tabs, run.tickets, strict=False):
        with tab:
            _render_ticket(ticket)


def _is_synthetic(t: TicketResult) -> bool:
    if t.analysis and t.analysis.meta.summary.upper().startswith("[SYNTHETIC DEMO"):
        return True
    return any("SYNTHETIC" in m.upper() for s in t.stages for m in s.messages)


def _dl(label: str, path_str: str, mime: str = "text/plain") -> None:
    p = Path(path_str)
    if p.exists():
        st.download_button(label, data=p.read_bytes(), file_name=p.name, mime=mime, key=f"dl_{path_str}")


def _render_ticket(t: TicketResult) -> None:
    st.markdown(
        f"**Provider:** {provider_badge(t.provider, t.demo_mode)} &nbsp;|&nbsp; "
        f"**Status:** `{t.status.value}` &nbsp;|&nbsp; **Automation:** `{t.automation_readiness}`"
    )
    if _is_synthetic(t):
        st.warning(
            "**SYNTHETIC DEMO TICKET** — no fixture matched this key, so a generic "
            "placeholder was used. Artifacts below are illustrative only, not derived "
            "from a real Jira ticket.",
            icon="🧪",
        )
    if t.error:
        st.error(t.error)
    if t.warnings:
        with st.expander(f"⚠️ {len(t.warnings)} warning(s)"):
            for w in t.warnings:
                st.write("- ", w)
    if not t.analysis:
        st.info("No artifacts — this ticket failed before analysis completed.")
        stage_board(t.stages)
        return

    sub = st.tabs(
        ["Requirements Analysis", "Test Plan", "Test Cases", "Playwright", "Traceability", "Run Details"]
    )

    with sub[0]:
        a = t.analysis
        cov = t.coverage
        if cov:
            m1, m2, m3 = st.columns(3)
            m1.metric("Requirements", cov.total_requirements)
            m2.metric("Acceptance criteria", cov.total_acceptance_criteria)
            m3.metric("Missing-info items", len(a.missing_information))
        if a.missing_information:
            st.warning("**Missing information:**\n" + "\n".join(f"- {x}" for x in a.missing_information))
        st.markdown(R.analysis_to_markdown(a))
        _dl("Download requirements_analysis.md", t.artifacts.get("requirements_analysis.md", ""))
        _dl(
            "Download requirements_analysis.json",
            t.artifacts.get("requirements_analysis.json", ""),
            "application/json",
        )

    with sub[1]:
        st.markdown(R.plan_to_markdown(t.test_plan))
        _dl("Download test_plan.md", t.artifacts.get("test_plan.md", ""))

    with sub[2]:
        suite = t.test_suite
        rows = [
            {
                "ID": tc.id,
                "Title": tc.title,
                "Priority": tc.priority,
                "Type": tc.test_type,
                "Automation": tc.automation_candidate.value,
                "Requirements": " ".join(tc.requirement_ids),
                "AC": " ".join(tc.acceptance_criteria_ids),
                "Tags": " ".join(tc.tags),
            }
            for tc in suite.test_cases
        ]
        df = pd.DataFrame(rows)
        k = t.ticket_key
        f1, f2, f3 = st.columns(3)
        pr = f1.multiselect(
            "Priority", sorted(df["Priority"].unique()) if not df.empty else [], key=f"pri_{k}"
        )
        ty = f2.multiselect(
            "Type", sorted(df["Type"].unique()) if not df.empty else [], key=f"type_{k}"
        )
        au = f3.multiselect(
            "Automation", sorted(df["Automation"].unique()) if not df.empty else [], key=f"auto_{k}"
        )
        q = st.text_input("Search (title / requirement / tag)", key=f"search_{k}")
        view = df
        if pr:
            view = view[view["Priority"].isin(pr)]
        if ty:
            view = view[view["Type"].isin(ty)]
        if au:
            view = view[view["Automation"].isin(au)]
        if q:
            mask = view.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)
            view = view[mask]
        st.dataframe(view, use_container_width=True, hide_index=True, key=f"df_{k}")
        st.caption(f"{len(view)} / {len(df)} test cases")
        with st.expander("Full test-case detail (markdown)"):
            st.markdown(R.cases_to_markdown(suite))
        _dl("Download test_cases.md", t.artifacts.get("test_cases.md", ""))
        _dl("Download test_cases.csv", t.artifacts.get("test_cases.csv", ""), "text/csv")

    with sub[3]:
        b = t.playwright
        st.markdown(f"**Automation readiness:** `{b.readiness.value}`")
        if b.missing_information:
            st.warning("**Missing information for automation:**\n" + "\n".join(f"- {x}" for x in b.missing_information))
        if b.setup_notes:
            st.info(b.setup_notes)
        for f in b.files:
            st.markdown(f"`{f.path}`")
            st.code(f.content, language="typescript")
        _dl("Download playwright_tests.md", t.artifacts.get("playwright_tests.md", ""))
        for rel, path in t.artifacts.items():
            if rel.endswith(".spec.ts"):
                _dl(f"Download {Path(path).name}", path)

    with sub[4]:
        cov = t.coverage
        if cov:
            m1, m2, m3 = st.columns(3)
            m1.metric("Requirement coverage", f"{cov.requirement_coverage_pct}%")
            m2.metric("AC coverage", f"{cov.ac_coverage_pct}%")
            m3.metric("Automated", f"{cov.automation_pct}%")
            if cov.orphan_requirements:
                st.warning(f"Orphan requirements (no test): {', '.join(cov.orphan_requirements)}")
            if cov.orphan_test_cases:
                st.warning(f"Orphan test cases (no requirement): {', '.join(cov.orphan_test_cases)}")
            st.markdown(R.coverage_to_markdown(cov))
            _dl("Download traceability_matrix.csv", t.artifacts.get("traceability_matrix.csv", ""), "text/csv")

    with sub[5]:
        st.markdown(f"- **Run/ticket dir:** `{t.artifact_dir}`")
        st.markdown(f"- **Provider:** {t.provider}  |  **Demo:** {t.demo_mode}")
        stage_board(t.stages)
        for s in t.stages:
            with st.expander(f"{s.name} — {s.status.value}"):
                st.write(f"Started: {s.started_at or '-'}")
                st.write(f"Finished: {s.finished_at or '-'}")
                for msg in s.messages:
                    st.write("• ", msg)
                if s.error:
                    st.error(s.error)
        _dl("Download manifest.json", t.artifacts.get("manifest.json", ""), "application/json")
