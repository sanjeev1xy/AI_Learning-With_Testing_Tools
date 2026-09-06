# P20 · DeepEval Framework

An LLM-evaluation framework built around two live "apps under test" and a
separate judge LLM. Three subsystems:

| # | Subsystem | Stack | Port(s) | What it is |
|---|-----------|-------|---------|------------|
| A | **ShopSphere Chatbot** | FastAPI + React (Vite) + Groq | 8201 (API), 5173 (UI) | A support chatbot that answers order / refund / shipping / product questions. The primary system under test. |
| B | **RAG Explorer** | FastAPI + Jinja + ChromaDB + Groq | 8202 | A full RAG pipeline (ingest → chunk → embed → retrieve → grounded answer with citations) that exposes every stage. The retrieval system under test. |
| C | **DeepEval Framework** | DeepEval 4.2 + pytest + FastAPI dashboard | 8203 | Scores A and B with a judge LLM. 25 metrics, a pytest suite (263 cases), and a card-per-metric dashboard. |

```
01_Chatbot_ShopEasy_Chatbot/  →  …/01_chatbot/   (backend/ + frontend/)
02_RAG_Explorer/              →  …/02_rag_explorer/
03_DeepFramework/             →  the framework (flat)
```

Subject ≠ judge on purpose: A and B answer with `qwen/qwen3.8-27b`; the judge is
`openai/gpt-oss-120b`. Both are on Groq's OpenAI-compatible endpoint. A judge
grading its own model family inflates the scores.

---

## Setup

Every subsystem carries a `.env.sample`. Copy it and add your Groq key
(`gsk_…`, free at <https://console.groq.com>). Real `.env` files are gitignored.

```bash
cp <subsystem>/.env.sample <subsystem>/.env
```

Python 3.14 note: the pinned `requirements.txt` in A and B fail to build
(`pydantic-core` / `chromadb` have no 3.14 wheels). Install unpinned:

```bash
pip install fastapi "uvicorn[standard]" groq python-multipart \
            chromadb "jinja2>=3.1.6" pypdf deepeval pytest pytest-asyncio \
            python-dotenv httpx
```

---

## Run

Start A and B first, then C.

```bash
# A — chatbot backend        (from 01_.../01_chatbot/backend)
GROQ_API_KEY=gsk_… CHATBOT_MODEL=qwen/qwen3.8-27b \
  python -m uvicorn app:app --reload --port 8201

# A — chatbot frontend       (from 01_.../01_chatbot/frontend)
npm install && npm run dev                     # http://localhost:5173

# B — RAG Explorer           (from 02_.../02_rag_explorer)
GROQ_API_KEY=gsk_… RAG_MODEL=qwen/qwen3.8-27b \
  python -m uvicorn app:app --reload --port 8202     # then /ingest → Seed

# C — DeepEval dashboard     (from 03_DeepFramework)
python -m uvicorn dashboard.app:app --port 8203      # http://localhost:8203
```

| URL | |
|-----|--|
| http://localhost:5173 | chatbot UI |
| http://localhost:8201/health | chatbot API |
| http://localhost:8202 | RAG Explorer |
| http://localhost:8203 | DeepEval dashboard |

---

## The framework (Subsystem C)

```
targets/          ChatbotTarget (:8201) · RagTarget (:8202, returns retrieval_context)
llm_Providers/    the judge — Groq openai/gpt-oss-120b as a DeepEval LocalModel
datasets/         chatbot_goldens · rag_goldens · attacks · conversations
metrics_catalog   25 MetricSpecs: .cases() / .build_case() / .build_metric() + display metadata
conftest.py       fixtures chatbot, rag, judge; skips needs_chatbot / needs_rag when a target is down
tests/chatbot/    10 metric test files
tests/rag/        smoke + 11 metric test files
dashboard/        FastAPI app (:8203) + runner.py (headless) + build_static.py (Vercel snapshot)
docs/             build_excalidraw.py → deepeval_framework_workflow.excalidraw
```

**Metrics by category:** quality (answer relevancy, faithfulness, hallucination),
retrieval (contextual precision / recall / relevancy — RAG only), g-eval
(correctness, no-prompt-leak, citation, summarization, helpfulness), safety
(bias, toxicity, PII, RAG safety, prompt injection, jailbreak, obfuscation,
exfiltration, social engineering, misuse, regulated advice, role adherence),
conversational (completeness, knowledge retention).

```bash
# headless run
python -m dashboard.runner --target rag --limit 2
python -m dashboard.runner --keys correctness role_violation

# pytest
pytest                         # 263 cases (real LLM calls)
pytest -m "rag and not slow"
pytest tests/rag/test_00_smoke.py       # no-LLM wiring check

# static snapshot for sharing / Vercel
python -m dashboard.build_static        # → dashboard-static/
```

See `03_DeepFramework/dashboard-static/how-it-works.html` for the workflow
diagram and `03_DeepFramework/prompts_deep_eval_framework.md` for the full
build log.

---

## Sharing the dashboard

Live snapshot: **<https://dashboard-static-psi-nine.vercel.app>**
(read-only — one recorded run; the Run buttons are disabled).

The interactive dashboard is local-only — it needs A and B running, the Groq
key, and background threads. `python -m dashboard.build_static` bakes a
read-only snapshot (the 25 cards + the latest `results.json`) into
`03_DeepFramework/dashboard-static/`, then:

```bash
cd 03_DeepFramework/dashboard-static
vercel deploy --prod        # redeploys to the URL above
```

---

## Known constraints

- Groq free tier rate-limits hard (~1000 output tok/min per model). The runner
  spaces judge calls (`EVAL_CASE_DELAY`) and backs off once on a 429
  (`EVAL_RATE_BACKOFF`).
- `llama-3.3-70b-versatile` is not available on the free tier → use
  `qwen/qwen3.8-27b`.
- `qwen3` is a reasoning model → the chatbot/RAG pass `max_tokens` and
  `reasoning_effort="none"`.
- Windows consoles are cp1252 → run the dashboard / runner with
  `PYTHONIOENCODING=utf-8 python -X utf8`.
- B needs no Ollama: `rag/embed.py` defaults to ChromaDB's bundled ONNX
  MiniLM embedder (`EMBED_BACKEND=onnx`); set `EMBED_BACKEND=ollama` to restore
  `nomic-embed-text`.
