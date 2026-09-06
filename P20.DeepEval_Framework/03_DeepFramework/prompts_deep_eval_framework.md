# Prompts & Build Log — P20.DeepEval_Framework

Every instruction given for this project, in order, with what was done for each.
Kept as a record of how the DeepEval framework and its two targets were built.

Environment: Windows 11, Python 3.14.6, Groq free tier. Judge LLM =
`openai/gpt-oss-120b` (Groq). Chatbot/RAG answer with `qwen/qwen3.8-27b`.
Groq key lives in each subsystem's `.env` (gitignored).

---

## 1 — Run the whole project, fix everything, every URL must work

> **User:** "P20.DeepEval_Framework run this project and whatever file present in
> this project please run and why not this url run http://localhost:8203/ ,
> please run this url and whatever related to this project URL every URL must be
> run and all the bug, issue please fix it and related url must be run and give
> me output of this project"

**Finding:** `03_DeepFramework` was a skeleton — 10 test files importing a
missing `metrics_catalog` and missing `chatbot`/`judge` fixtures; `dashboard/
docs/ llm_Providers/ targets/` were empty folders. No web server, no port 8203.
`pytest` → 10 collection errors (`ModuleNotFoundError: metrics_catalog`).

> **User (decision prompt):** "How far do you want me to build it?"
> → **"Full build + dashboard on 8203"**

**Built (Subsystem C):**
- `conftest.py` — `.env` loader, key normalisation, `chatbot`/`judge` session
  fixtures, `pytest_collection_modifyitems` that skips `needs_chatbot` when
  :8201 is unreachable.
- `llm_Providers/judge.py` — `build_judge()` → DeepEval `LocalModel` pointed at
  Groq (`openai/gpt-oss-120b`).
- `targets/chatbot.py` — `ChatbotTarget` httpx client for the chatbot (:8201).
- `datasets/attacks.py` — `Attack` dataclass + adversarial library: 5 techniques
  (prompt injection, jailbreak, obfuscation, exfiltration, social engineering) +
  misuse prompts.
- `metrics_catalog.py` — `MetricSpec` (`.cases()` / `.build_case()` /
  `.build_metric()`) + the metric set (answer relevancy, faithfulness,
  hallucination, G-Eval correctness, bias, toxicity, PII, per-technique G-Eval
  resistance, misuse, non-advice, role adherence).
- `dashboard/app.py` (FastAPI :8203) + `dashboard/runner.py` (runs specs without
  pytest, writes `results.json`) + `templates/dashboard.html`.
- `pytest.ini` moved to the framework root (so `pythonpath=.` reaches
  `metrics_catalog`), `.env` / `.env.sample`, `README.md`, `requirements.txt`.

**Bugs fixed:**
- `pytest.ini` was under `tests/` → rootdir was wrong, `metrics_catalog`
  unreachable. Moved to `03_DeepFramework/`.
- G-Eval with free-text `criteria=` inverted the resistance score (0.1 with a
  reason describing a pass). Switched to explicit `evaluation_steps=` with
  LOW/HIGH anchors — also removes one LLM call per case.
- Bias / Toxicity / Hallucination are DeepEval 4.x direction (1.0 = good,
  `threshold` is the minimum) → thresholds 0.3 → 0.7.
- Groq free tier 429s after ~11 fast judge calls → runner spaces calls
  (`EVAL_CASE_DELAY`, default ~4s) and backs off once on a 429
  (`EVAL_RATE_BACKOFF`, ~35s).
- Windows cp1252 console vs DeepEval's emoji progress bar → run with
  `PYTHONIOENCODING=utf-8 python -X utf8`.
- `runner.py` crashed on string-typed cases (bias/toxicity/pii) → `_case_prompt()`
  helper.

**Output:** first dashboard run 12/15 pass. The 3 fails were real chatbot
findings — weak refund-window relevancy; the bot answers "my chest hurts" with
medical advice instead of declining.

---

## 2 — Run the RAG Explorer and open it on localhost

> **User:** "run the RAG Explorer also and open in the local host"

**Subsystem B** (`02_RAG_Explorer/…/02_rag_explorer/`, port 8202) — FastAPI +
Jinja, full RAG pipeline (ingest → chunk → embed → ChromaDB → retrieve → Groq
answer with inline citations). Blockers:

- Hard dependency on Ollama + `nomic-embed-text`; Ollama not installed, and
  `rag/embed.py` had no fallback.

> **User (decision prompt):** "How to proceed?"
> → **"Patch to local fallback embedder"**

- `rag/embed.py` rewritten with an `EMBED_BACKEND` switch. Default `onnx` uses
  ChromaDB's bundled `ONNXMiniLM_L6_V2` (all-MiniLM-L6-v2, 384-dim, ~80 MB
  one-time download, no torch). `EMBED_BACKEND=ollama` restores the original.
- `app.py` — all four `templates.TemplateResponse("x.html", {"request": …})`
  calls → new Starlette signature `TemplateResponse(request, "x.html", {…})`.
  The old signature on modern Starlette shifts the args and Jinja gets a dict as
  the template name → `TypeError: cannot use 'tuple' as a dict key`.
- `RAG_MODEL=qwen/qwen3.8-27b` at launch (default `llama-3.3-70b-versatile` is
  not on this Groq key).
- Deps unpinned (`chromadb==0.5.20` has no Python 3.14 wheel → chromadb 1.5.9;
  jinja2 must be ≥ 3.1.6).

**Verified end to end:** ingest → 21 chunks / 5 docs; search returns ranked hits
with scores; `/chat` gives grounded answers with `[source.md]` citations.

---

## 3 — Rebuild the dashboard to match the reference screenshot

> **User:** "whynot created DeepEval Dashboard url is http://localhost:8203/ ,
> please create like this is in dashboard i have provided the screenshot of
> DeepEval Dashboard, please create like this"
> *(screenshot: dark header, Target / Cases-per-run / Judge controls,
> Refresh + Run-all buttons, 3 status cards + pass·fail·pending pills, category
> tabs, one card per metric with Run + Details, "N cases available · test file")*

**Redesigned Subsystem C's dashboard to a card-per-metric UI:**
- Dark header + orange diamond logo, "DeepEval Dashboard" / "Live metric runs
  against the chatbot and RAG pipeline".
- Controls: **Target** selector (Chatbot A :8201 / RAG Explorer B :8202),
  **Cases per run**, **Judge model** field, **Refresh status**,
  **▶ Run all visible**.
- Status row: Chatbot / RAG / Judge cards + `pass · fail · pending` pills.
- Category tabs: All / Quality / Retrieval / Safety / G-Eval / Conversational.
- One card per metric: category + target chips, `≥ 0.70` threshold, title,
  question, a `NOT RUN / PASS / FAIL` box with a sample prompt and
  `N cases · tests/…`, plus **▶ Run** and **Details** (expandable per-case
  input / reply / judge reason).
- Live polling of `/api/status` while anything is running; Target selector
  filters the visible cards.

**New backend:** `MetricSpec` gained `category / threshold / test_file /
targets / conversational / retrieval / .as_dict()`. `runner.py` reworked —
per-metric threaded runs keyed `"<target>:<key>"`, batch runner for Run-all.
API: `GET /api/status`, `GET /api/specs`, `POST /api/run/{key}`,
`POST /api/run-all`.

**New targets & specs added in this pass:** `targets/rag.py` (`RagTarget` →
:8202, returns `retrieval_context`), `datasets/conversations.py` (3 multi-turn
goldens), and specs: contextual precision / recall / relevancy, G-Eval no
prompt leak, conversation completeness, knowledge retention.

---

## 4 — Add RAG to the dashboard; every related URL must work

> **User:** "Please add for RaG also and finally all the reated URL should work"

- Every card now declares which targets it supports; the Target selector shows
  the Chatbot set (19) or the full RAG set.
- Retrieval metrics wired to `RagTarget` (they need `retrieval_context`).
- Verified 4 URLs live (200): 8201, 5173, 8202, 8203.

---

## 5 — More metrics, for chatbot AND RAG

> **User:** "We can please add some of the more metrics, like prompt injection,
> Jade breaks [jailbreaks], and many more things, in chatbot as well as RAG."

- The 5 security-technique specs (prompt injection, jailbreak, obfuscation,
  exfiltration, social engineering) + bias, toxicity, PII, misuse, non-advice,
  role adherence → `targets=["chatbot", "rag"]`. They now run against both.
- New RAG-specific G-Eval specs: **Citation**, **Summarization**,
  **Helpfulness**, plus **RAG Safety** (loaded / off-corpus / injection prompts).
- Conversation completeness + knowledge retention → both targets.
- **25 metrics total**, all RAG-capable, 19 chatbot-capable.

---

## 6 — Add the RAG test-case suite

> **User:** "Please add for RaG also and finally all the related URL should work"
> **User:** "Please Add RAG TestCase also in this project after adding all the
> related URL should work"
> *(screenshot: tests/rag/ file tree — conftest.py, test_00_smoke.py,
> test_01_rag_contextual_precision.py … test_11_rag_geval_helpfulness.py)*

**Built `tests/rag/` to match the screenshot:**

| File | What it scores |
|------|----------------|
| `conftest.py` | `rag_answer` fixture — one cached (reply, retrieval_context) per question |
| `test_00_smoke.py` | 3 no-LLM checks: reachable · corpus seeded · returns context |
| `test_01_rag_contextual_precision.py` | ContextualPrecision |
| `test_02_rag_contextual_relevancy.py` | ContextualRelevancy |
| `test_03_rag_faithfulness.py` | Faithfulness |
| `test_04_rag_answer_relevancy.py` | AnswerRelevancy |
| `test_05_rag_hallucination.py` | Hallucination |
| `test_06_rag_geval_correctness.py` | G-Eval Correctness |
| `test_07_rag_geval_citation.py` | G-Eval Citation |
| `test_08_rag_safety.py` | G-Eval RAG Safety |
| `test_09_rag_geval_summarization.py` | G-Eval Summarization |
| `test_10_rag_conversational.py` | ConversationCompleteness + KnowledgeRetention |
| `test_11_rag_geval_helpfulness.py` | G-Eval Helpfulness |

**Also added:** `datasets/rag_goldens.py` (10 `RagGolden`s with
`expected_source`, `RAG_SAFETY_PROMPTS`, `RAG_CONVERSATIONS`); root `conftest.py`
gained a `rag` fixture and a `needs_rag` skip hook.

**Bug fixed:** Citation initially scored 0.00 — the RAG bot cited
`[refund_policy.md]` but the `retrieval_context` chunks carried no filename, so
the judge could not verify. `targets/rag.py` now labels each chunk
`[source] text`. Re-run → Citation **PASS 1.00**
("cites every factual claim with inline brackets that correspond to the
provided refund_policy.md chunks").

**Verified:** pytest collects **263 tests**; `tests/rag/test_00_smoke.py` 3/3;
dashboard RAG runs — contextual precision / faithfulness / summarization /
safety **1.00**, helpfulness **0.90**, citation **1.00** after the fix.

---

## 7 — This file

> **User:** "whatever we have done till now, whatever the prompts and everything
> that I have given to you, can you please put them into the
> prompts_deep_eval_framework.md file into the deepeval frame folder also?"

→ this document.

---

## The three subsystems / URLs

| Port | Subsystem | Start (from its own dir) |
|------|-----------|--------------------------|
| 8201 | A — ShopSphere chatbot API (FastAPI) | `GROQ_API_KEY=gsk_… CHATBOT_MODEL=qwen/qwen3.8-27b python -m uvicorn app:app --port 8201` |
| 5173 | A — chatbot React frontend (Vite) | `npm install && npm run dev` |
| 8202 | B — RAG Explorer (FastAPI + Jinja) | `GROQ_API_KEY=gsk_… RAG_MODEL=qwen/qwen3.8-27b python -m uvicorn app:app --port 8202` |
| 8203 | C — DeepEval Framework dashboard | `python -m uvicorn dashboard.app:app --port 8203` |

Headless eval: `python -m dashboard.runner --target rag --limit 2`
Pytest: `pytest` · `pytest -m rag` · `pytest -m "quality and not slow"`

## Recurring gotchas (Python 3.14 + Groq free tier + Windows)

- Pinned `pydantic` / `chromadb` builds have no 3.14 wheels → install unpinned.
- jinja2 must be ≥ 3.1.6 on 3.14.
- Modern Starlette `TemplateResponse` takes `request` first.
- Groq free tier: ~1000 output tok/min per model, 429s under burst → throttle +
  backoff; `qwen3` is a reasoning model → `max_tokens` + `reasoning_effort="none"`.
- `llama-3.3-70b-versatile` is not on this key → use `qwen/qwen3.8-27b`.
- Windows cp1252 console → `PYTHONIOENCODING=utf-8 python -X utf8`.
- DeepEval judge: pass an explicit `LocalModel(...)` instance (not a model
  string) so it is treated as native and bypasses the cwd/plugin-sensitive
  `USE_LOCAL_MODEL` lookup.
