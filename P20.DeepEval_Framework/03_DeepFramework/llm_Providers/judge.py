"""The judge LLM every DeepEval metric scores with.

Groq's OpenAI-compatible endpoint, wrapped as a DeepEval ``LocalModel`` so it
is treated as a native model (no dependence on cwd / the pytest plugin import
order that the ``USE_LOCAL_MODEL`` env lookup is sensitive to).

Deliberately NOT the same family as the chatbot under test: the chatbot runs
``qwen/qwen3.8-27b``, the judge runs ``openai/gpt-oss-120b``. A judge scoring
its own family inflates scores.
"""
from __future__ import annotations

import os

from deepeval.models import LocalModel

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def _groq_key() -> str:
    key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("LOCAL_MODEL_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not key:
        raise RuntimeError(
            "No Groq API key. Set GROQ_API_KEY (gsk_...) in the environment or .env"
        )
    return key


def build_judge(model: str | None = None) -> LocalModel:
    return LocalModel(
        model=model or JUDGE_MODEL,
        api_key=_groq_key(),
        base_url=GROQ_BASE_URL,
    )
