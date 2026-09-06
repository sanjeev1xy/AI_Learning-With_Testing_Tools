"""RAG suite fixtures.

The `rag` / `judge` fixtures and the `needs_rag` skip live in the framework-root
conftest.py. This adds one RAG-scoped helper: a cached (reply, retrieval_context)
per question so several metrics can score the same call without re-querying.
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def rag_answer(rag):
    cache: dict[str, tuple[str, list[str]]] = {}

    def _get(question: str) -> tuple[str, list[str]]:
        if question not in cache:
            r = rag.chat(question)
            cache[question] = (r.reply, r.retrieval_context)
        return cache[question]

    return _get
