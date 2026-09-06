"""Embeddings.

Original design used Ollama `nomic-embed-text`. Patched to a local fallback:
ChromaDB's bundled ONNX all-MiniLM-L6-v2 (384-dim). No Ollama, no torch —
the model (~80MB) is downloaded once to ~/.cache/chroma on first use.

Set EMBED_BACKEND=ollama to restore the original path (needs a running Ollama
with `ollama pull nomic-embed-text`).
"""
from __future__ import annotations

import os
from typing import Sequence

EMBED_BACKEND = os.getenv("EMBED_BACKEND", "onnx").lower()

if EMBED_BACKEND == "ollama":
    import ollama

    EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _client() -> "ollama.Client":
        return ollama.Client(host=OLLAMA_HOST)

    def embed_texts(texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        client = _client()
        return [
            list(client.embeddings(model=EMBED_MODEL, prompt=t)["embedding"])
            for t in texts
        ]

    def model_info() -> dict:
        return {"model": EMBED_MODEL, "host": OLLAMA_HOST, "backend": "ollama"}

else:
    from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

    EMBED_MODEL = "all-MiniLM-L6-v2"
    OLLAMA_HOST = "n/a (local onnx fallback)"

    _ef = ONNXMiniLM_L6_V2()

    def embed_texts(texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return [list(map(float, v)) for v in _ef(list(texts))]

    def model_info() -> dict:
        return {"model": EMBED_MODEL, "host": OLLAMA_HOST, "backend": "onnx"}


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
