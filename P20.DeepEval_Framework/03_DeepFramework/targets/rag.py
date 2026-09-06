"""HTTP client for Subsystem B — the RAG Explorer (default :8202).

Unlike the chatbot, this target exposes its retrieval: ``chat()`` returns the
grounded answer AND the chunks it retrieved, so the retrieval-quality metrics
(contextual precision / recall / relevancy) have something to score.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

RAG_URL = os.getenv("RAG_URL", "http://localhost:8202").rstrip("/")


@dataclass
class RagReply:
    reply: str
    retrieval_context: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    model: str = "unknown"
    mode: str = "unknown"
    usage: dict | None = None


class RagTarget:
    def __init__(self, base_url: str = RAG_URL, timeout: float = 90.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def health(self) -> dict:
        r = self._client.get(f"{self.base_url}/api/health")
        r.raise_for_status()
        return r.json()

    def is_up(self) -> bool:
        try:
            return self.health().get("status") == "ok"
        except Exception:
            return False

    def seed(self, reset: bool = False) -> dict:
        r = self._client.post(f"{self.base_url}/api/ingest/seed", params={"reset": reset})
        r.raise_for_status()
        return r.json()

    def ensure_corpus(self) -> None:
        try:
            stats = self._client.get(f"{self.base_url}/api/stats").json()
            if not stats.get("chunks"):
                self.seed(reset=False)
        except Exception:
            pass

    def chat(self, message: str, top_k: int = 4) -> RagReply:
        r = self._client.post(
            f"{self.base_url}/api/chat", json={"message": message, "top_k": top_k}
        )
        r.raise_for_status()
        d = r.json()
        hits = d.get("hits", [])
        # Label each chunk with its source file so citation-style metrics can
        # verify inline references like [refund_policy.md] against the context.
        if hits:
            ctx = [f"[{h.get('source', '?')}] {h.get('text', '')}".strip() for h in hits]
        else:
            ctx = d.get("retrieval_context", [])
        return RagReply(
            reply=d.get("answer", ""),
            retrieval_context=ctx,
            sources=d.get("sources", []),
            model=d.get("model", "unknown"),
            mode=d.get("mode", "unknown"),
            usage=d.get("usage"),
        )

    def close(self) -> None:
        self._client.close()
