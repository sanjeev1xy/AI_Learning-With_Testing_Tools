"""Streamlit session-state helpers so results survive normal reruns."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ..models import RunResult

_RUN_KEY = "qa_run_result"
_RUNNING_KEY = "qa_run_in_progress"
_LIVE_KEY = "qa_live_stages"


def get_run() -> RunResult | None:
    return st.session_state.get(_RUN_KEY)


def set_run(run: RunResult) -> None:
    st.session_state[_RUN_KEY] = run


def clear_run() -> None:
    st.session_state.pop(_RUN_KEY, None)
    st.session_state.pop(_LIVE_KEY, None)


def set_running(flag: bool) -> None:
    st.session_state[_RUNNING_KEY] = flag


def is_running() -> bool:
    return bool(st.session_state.get(_RUNNING_KEY))


def set_live_stages(data: dict[str, Any]) -> None:
    st.session_state[_LIVE_KEY] = data


def get_live_stages() -> dict[str, Any]:
    return st.session_state.get(_LIVE_KEY, {})
