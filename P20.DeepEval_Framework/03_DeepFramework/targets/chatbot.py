"""HTTP client for Subsystem A — the ShopSphere chatbot (default :8201).

This is the "system under test". The eval suite only ever talks to it through
this class, so swapping the target (a different port, a mock, a competitor
bot) is a one-line change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import httpx

CHATBOT_URL = os.getenv("CHATBOT_URL", "http://localhost:8201").rstrip("/")


@dataclass
class ChatbotReply:
    reply: str
    model: str = "unknown"
    mode: str = "unknown"
    usage: dict | None = None
    # The chatbot is not RAG (it carries policy in its system prompt), so it
    # returns no retrieval context. Faithfulness needs one, so the caller
    # fills this from the golden's ground-truth snippets.
    retrieval_context: list[str] = field(default_factory=list)


class ChatbotTarget:
    def __init__(self, base_url: str = CHATBOT_URL, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)

    def health(self) -> dict:
        r = self._client.get(f"{self.base_url}/health")
        r.raise_for_status()
        return r.json()

    def is_up(self) -> bool:
        try:
            return self.health().get("status") == "ok"
        except Exception:
            return False

    def chat(self, message: str, history: list[dict] | None = None) -> ChatbotReply:
        r = self._client.post(
            f"{self.base_url}/chat",
            json={"message": message, "history": history},
        )
        r.raise_for_status()
        data = r.json()
        return ChatbotReply(
            reply=data.get("reply", ""),
            model=data.get("model", "unknown"),
            mode=data.get("mode", "unknown"),
            usage=data.get("usage"),
        )

    def close(self) -> None:
        self._client.close()
