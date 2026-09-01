"""Reusable Streamlit UI blocks: input, readiness, pipeline stage board."""

from __future__ import annotations

import streamlit as st

from ..config import AppConfig
from ..crew.callbacks import STAGE_NAMES
from ..models import StageResult, StageStatus
from ..services.ticket_parser import parse_ticket_input

_STATUS_ICON = {
    StageStatus.PENDING: "⚪",
    StageStatus.RUNNING: "🔵",
    StageStatus.COMPLETED: "🟢",
    StageStatus.WARNING: "🟡",
    StageStatus.FAILED: "🔴",
}


def header() -> None:
    st.title("Jira QA Crew")
    st.caption(
        "Generate test plans, test cases, traceability, and Playwright automation directly from Jira."
    )


def demo_banner(config: AppConfig) -> None:
    if config.effective_demo_mode():
        reason = (
            "live Jira credentials are configured but `DEMO_MODE=true` is set — flip it to "
            "`false` in `.env` for live tickets"
            if config.rest.configured or config.mcp.configured
            else "no live Jira credentials are configured"
        )
        st.warning(
            f"**DEMO MODE** — {reason}. Tickets are served from local fixtures in `fixtures/` "
            "(unknown keys get a labelled synthetic placeholder). Results are **not** live Jira data.",
            icon="🧪",
        )
    elif not config.llm.configured:
        st.error("LLM is not configured. Set `LLM_MODEL` and `LLM_API_KEY` in `.env` before running.", icon="⛔")


def input_area(config: AppConfig) -> dict:
    st.subheader("1 · Jira tickets")
    raw = st.text_area(
        "Jira ticket ID(s)",
        placeholder="VWO-48\nVWO-48, VWO-49; VWO-50",
        height=110,
        help="Separate IDs with commas, spaces, new lines or semicolons.",
        key="ticket_input",
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        mode = st.radio(
            "2 · Integration mode",
            options=["auto", "mcp", "rest"],
            format_func={"auto": "Auto (MCP → REST)", "mcp": "MCP only", "rest": "REST only"}.get,
            horizontal=True,
            key="integration_mode",
        )
    with col2:
        with st.expander("Advanced settings"):
            st.write(f"Max tickets per run: **{config.max_tickets}**")
            st.write(f"Repair attempts: **{config.max_retries}**")
            st.write(f"Per-ticket timeout: **{config.ticket_timeout_seconds}s**")
            st.write(f"Output dir: `{config.output_dir}`")

    parsed = parse_ticket_input(raw) if raw.strip() else None
    if parsed:
        if parsed.valid:
            st.success(f"Valid: {', '.join(parsed.valid)}")
        if parsed.duplicates:
            st.info(f"Duplicates removed: {', '.join(parsed.duplicates)}")
        if parsed.invalid:
            st.warning(f"Ignored (not a Jira key): {', '.join(parsed.invalid)}")
        if parsed.truncated:
            st.warning(f"Only the first {config.max_tickets} tickets will be processed.")

    disabled = not (parsed and parsed.valid) or not config.llm.configured
    clicked = st.button("Analyze & Generate QA Pack", type="primary", disabled=disabled, use_container_width=True)
    return {"raw": raw, "mode": mode, "parsed": parsed, "clicked": clicked}


def readiness_panel(config: AppConfig) -> None:
    st.subheader("Configuration / readiness")
    r = config.readiness()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM", "ready" if r["llm_configured"] else "missing", r["llm_model"])
    c2.metric("Jira MCP", "configured" if r["jira_mcp_configured"] else "off")
    c3.metric("Jira REST", "configured" if r["jira_rest_configured"] else "off")
    c1.metric("Integration mode", r["integration_mode"])
    c2.metric("Live Jira", "yes" if r["live_jira_available"] else "no")
    c3.metric("Demo mode", "ACTIVE" if r["effective_demo_mode"] else ("enabled" if r["demo_mode_enabled"] else "off"))
    for w in config.warnings:
        st.caption(f"⚠️ {w}")


def stage_board(stages: list[StageResult], title: str = "CrewAI pipeline") -> None:
    st.markdown(f"**{title}**")
    cols = st.columns(4)
    by_name = {s.name: s for s in stages}
    for col, name in zip(cols, STAGE_NAMES, strict=False):
        s = by_name.get(name) or StageResult(name=name)
        icon = _STATUS_ICON.get(s.status, "⚪")
        dur = s.duration_seconds()
        dur_txt = f"\n\n{dur}s" if dur is not None else ""
        col.markdown(f"{icon} **{name}**\n\n`{s.status.value}`{dur_txt}")
    latest = [s for s in stages if s.messages]
    if latest:
        last = latest[-1]
        st.caption(f"{last.name}: {last.messages[-1]}")


def provider_badge(provider: str, demo: bool) -> str:
    label = provider or "unknown"
    if demo:
        return f"🧪 `{label}` (DEMO fixture)"
    return f"🔌 `{label}`"
