"""Build the CrewAI LLM from configuration. No model id is hard-coded."""

from __future__ import annotations

import re
import time

from crewai import LLM

from ..config import AppConfig, get_config, require_llm
from ..logging_utils import get_logger

logger = get_logger("crew.llm")

_RATE_RE = re.compile(r"rate.?limit|tokens per minute|TPM|\b429\b|\b413\b|request too large", re.IGNORECASE)
_RETRY_WAITS = (20, 40, 60)


def _wrap_with_rate_limit_retry(llm: LLM) -> LLM:
    """Retry transient provider rate-limit / request-too-large errors with backoff.

    Free LLM tiers (e.g. Groq's 8000 TPM) reject an otherwise valid call with a
    429/413. Waiting for the per-minute window to roll over and retrying keeps a
    sequential crew alive instead of failing the whole ticket.
    """
    original_call = llm.call

    def call_with_retry(*args, **kwargs):
        last: Exception | None = None
        for attempt, wait in enumerate((*_RETRY_WAITS, None)):
            try:
                return original_call(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - inspect message, re-raise if not a rate error
                last = exc
                if not _RATE_RE.search(str(exc)) or wait is None:
                    raise
                logger.warning(
                    "LLM rate-limited (attempt %d); waiting %ds before retry.", attempt + 1, wait
                )
                time.sleep(wait)
        raise last  # pragma: no cover

    llm.call = call_with_retry  # type: ignore[method-assign]
    return llm


def build_llm(config: AppConfig | None = None) -> LLM:
    cfg = config or get_config()
    llm_cfg = require_llm(cfg)

    model = llm_cfg.model
    kwargs: dict[str, object] = {
        "temperature": llm_cfg.temperature,
        "api_key": llm_cfg.api_key,
    }

    if llm_cfg.base_url:
        # CrewAI routes an ``openai/<x>`` model to the native OpenAI client against
        # a custom base_url and strips exactly one leading ``openai/`` before
        # sending ``<x>`` as the model id. Groq's own id is ``openai/gpt-oss-120b``,
        # so we prepend one extra ``openai/`` to survive that strip.
        if not model.startswith("openai/openai/"):
            model = f"openai/{model}"
        kwargs["base_url"] = llm_cfg.base_url
    kwargs["model"] = model
    if llm_cfg.max_tokens:
        kwargs["max_tokens"] = llm_cfg.max_tokens
    if llm_cfg.reasoning_effort:
        kwargs["reasoning_effort"] = llm_cfg.reasoning_effort

    logger.info(
        "LLM configured: model=%s provider=%s custom_base_url=%s",
        model, llm_cfg.provider_label, bool(llm_cfg.base_url),
    )
    return _wrap_with_rate_limit_retry(LLM(**kwargs))
