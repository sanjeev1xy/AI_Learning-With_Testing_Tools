"""Structured logging plus secret redaction helpers."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable

_SECRET_ENV_HINTS = ("TOKEN", "API_KEY", "SECRET", "PASSWORD", "BEARER")
_REDACTION = "***REDACTED***"


def _collect_secret_values() -> list[str]:
    values: list[str] = []
    for key, value in os.environ.items():
        if not value or len(value) < 6:
            continue
        if any(hint in key.upper() for hint in _SECRET_ENV_HINTS):
            values.append(value)
    return values


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")
_BASIC_RE = re.compile(r"(?i)basic\s+[A-Za-z0-9+/=]+")
_ATLASSIAN_TOKEN_RE = re.compile(r"ATATT[A-Za-z0-9_\-=]{10,}")


def redact(text: str, extra_secrets: Iterable[str] | None = None) -> str:
    """Remove known secret material from ``text`` before it is logged or displayed."""
    if not text:
        return text
    cleaned = text
    for secret in list(_collect_secret_values()) + list(extra_secrets or []):
        if secret:
            cleaned = cleaned.replace(secret, _REDACTION)
    cleaned = _BEARER_RE.sub("Bearer " + _REDACTION, cleaned)
    cleaned = _BASIC_RE.sub("Basic " + _REDACTION, cleaned)
    cleaned = _ATLASSIAN_TOKEN_RE.sub(_REDACTION, cleaned)
    cleaned = _EMAIL_RE.sub(_REDACTION, cleaned)
    return cleaned


class RedactingFilter(logging.Filter):
    """Logging filter that scrubs secrets from every emitted record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        try:
            record.msg = redact(str(record.getMessage()))
            record.args = ()
        except Exception:  # pragma: no cover - logging must never raise
            pass
        return True


_CONFIGURED = False


def configure_logging(level: str | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    log_level = getattr(logging, (level or os.getenv("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s"))
    handler.addFilter(RedactingFilter())
    root = logging.getLogger("jira_qa_crew")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"jira_qa_crew.{name}")
