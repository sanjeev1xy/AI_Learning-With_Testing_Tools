"""00 - Smoke: free wiring checks, no LLM calls.

Confirms the RAG Explorer is reachable, the corpus is seeded, and a query
comes back with retrieved context. If this fails, nothing else in the suite
can pass — fix the target first.
"""
import pytest


@pytest.mark.rag
@pytest.mark.smoke
@pytest.mark.needs_rag
def test_rag_reachable(rag):
    assert rag.is_up(), "RAG Explorer /api/health did not return ok"


@pytest.mark.rag
@pytest.mark.smoke
@pytest.mark.needs_rag
def test_rag_corpus_seeded(rag):
    stats = rag._client.get(f"{rag.base_url}/api/stats").json()
    assert stats.get("chunks", 0) > 0, "RAG corpus is empty — hit /ingest → Seed"


@pytest.mark.rag
@pytest.mark.smoke
@pytest.mark.needs_rag
def test_rag_returns_context(rag):
    r = rag.chat("What is the refund window?")
    assert r.reply.strip(), "empty answer"
    assert r.retrieval_context, "no retrieval_context returned"
