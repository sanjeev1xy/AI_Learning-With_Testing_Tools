"""Shared fixtures + environment wiring for the whole suite.

Lives at the framework root so pytest prepends this directory to sys.path,
which is what makes ``import metrics_catalog`` / ``import datasets.*`` work
from the test files.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

# Load env from the framework root, then fall back to the sibling chatbot's
# .env files — a single Groq key is shared across all subsystems.
for env_path in (
    ROOT / ".env",
    ROOT / ".env.local",
    ROOT.parent / "01_Chatbot_ShopEasy_Chatbot" / "01_Chatbot_Shopeasy_chatbot" / "01_chatbot" / ".env",
):
    if env_path.exists():
        load_dotenv(env_path)

# Normalise whatever the key is called into GROQ_API_KEY + OPENAI_API_KEY
# (the latter is what a few DeepEval code paths still read).
_key = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("LOCAL_MODEL_API_KEY")
    or os.getenv("DeepEvaluation_Groq_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
if _key:
    os.environ.setdefault("GROQ_API_KEY", _key)
    os.environ["OPENAI_API_KEY"] = _key

from llm_Providers import build_judge  # noqa: E402  (after env is loaded)
from targets import ChatbotTarget, RagTarget  # noqa: E402


@pytest.fixture(scope="session")
def chatbot() -> ChatbotTarget:
    bot = ChatbotTarget()
    yield bot
    bot.close()


@pytest.fixture(scope="session")
def rag() -> RagTarget:
    r = RagTarget()
    if r.is_up():
        r.ensure_corpus()
    yield r
    r.close()


@pytest.fixture(scope="session")
def judge():
    return build_judge()


def pytest_collection_modifyitems(config, items):
    """Skip target-bound tests when their target is unreachable."""
    chatbot_up = ChatbotTarget().is_up()
    rag_up = RagTarget().is_up()
    skip_chatbot = pytest.mark.skip(reason="chatbot not reachable (start Subsystem A on :8201)")
    skip_rag = pytest.mark.skip(reason="RAG Explorer not reachable (start Subsystem B on :8202)")
    for item in items:
        if "needs_chatbot" in item.keywords and not chatbot_up:
            item.add_marker(skip_chatbot)
        if "needs_rag" in item.keywords and not rag_up:
            item.add_marker(skip_rag)
