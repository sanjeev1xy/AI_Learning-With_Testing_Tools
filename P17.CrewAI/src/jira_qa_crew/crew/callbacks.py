"""Genuine stage-level progress capture (no fake token streaming)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from ..logging_utils import get_logger, redact
from ..models import StageResult, StageStatus

logger = get_logger("crew.callbacks")

ProgressHook = Callable[[StageResult], None]

STAGE_NAMES = ["Jira Analyst", "Test Plan Writer", "Test Case Writer", "Playwright Coder"]


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ProgressTracker:
    """Tracks the four pipeline stages for one ticket and fans events out to a hook."""

    def __init__(self, ticket_key: str, hook: ProgressHook | None = None) -> None:
        self.ticket_key = ticket_key
        self._hook = hook
        self.stages: dict[str, StageResult] = {name: StageResult(name=name) for name in STAGE_NAMES}

    # -- lifecycle -------------------------------------------------
    def _emit(self, stage: StageResult) -> None:
        if self._hook:
            try:
                self._hook(stage)
            except Exception as exc:  # noqa: BLE001 - UI hook must never break the pipeline
                logger.debug("progress hook error: %s", exc)

    def start(self, name: str, message: str = "") -> None:
        stage = self.stages[name]
        stage.status = StageStatus.RUNNING
        stage.started_at = _now()
        if message:
            stage.messages.append(redact(message))
        logger.info("[%s] %s started. %s", self.ticket_key, name, message)
        self._emit(stage)

    def note(self, name: str, message: str) -> None:
        stage = self.stages[name]
        stage.messages.append(redact(message))
        self._emit(stage)

    def complete(self, name: str, message: str = "", warning: bool = False) -> None:
        stage = self.stages[name]
        stage.status = StageStatus.WARNING if warning else StageStatus.COMPLETED
        stage.finished_at = _now()
        if message:
            stage.messages.append(redact(message))
        logger.info("[%s] %s %s. %s", self.ticket_key, name, stage.status.value, message)
        self._emit(stage)

    def fail(self, name: str, error: str) -> None:
        stage = self.stages[name]
        stage.status = StageStatus.FAILED
        stage.finished_at = _now()
        stage.error = redact(error)
        stage.messages.append(f"FAILED: {redact(error)}")
        logger.error("[%s] %s FAILED: %s", self.ticket_key, name, redact(error))
        self._emit(stage)

    def ordered(self) -> list[StageResult]:
        return [self.stages[name] for name in STAGE_NAMES]
