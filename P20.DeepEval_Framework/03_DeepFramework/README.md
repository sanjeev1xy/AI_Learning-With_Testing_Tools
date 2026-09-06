# Subsystem C — DeepEval Framework

The evaluator. Scores Subsystem A (the ShopSphere chatbot on `:8201`) with an
LLM judge, as both a **pytest suite** and a **web dashboard** (`:8203`).

```
targets/       HTTP clients: ChatbotTarget (:8201), RagTarget (:8202, returns retrieval_context)
llm_Providers/ the judge LLM (Groq openai/gpt-oss-120b, wrapped as a DeepEval LocalModel)
datasets/      chatbot_goldens.py · rag_goldens.py · attacks.py · conversations.py
metrics_catalog.py  25 MetricSpecs: .cases() / .build_case() / .build_metric() + display metadata
conftest.py    fixtures `chatbot`, `rag`, `judge`; skips needs_chatbot / needs_rag when a target is down
tests/chatbot/ 10 metric test files (chatbot target)
tests/rag/     test_00_smoke + 11 metric test files (RAG target: retrieval, faithfulness, citation,
               summarization, helpfulness, safety, conversational, …)
dashboard/     FastAPI app (:8203) + runner.py (same specs, no pytest, keeps results.json)
```

Most metrics run against **both** targets — pick the target on the dashboard, or
`--target rag` on the CLI / the `@pytest.mark.rag` files.

## Metrics

| # | Test | Metric | Group |
|---|------|--------|-------|
| 01 | answer relevancy | `AnswerRelevancyMetric` | quality |
| 02 | faithfulness | `FaithfulnessMetric` | quality |
| 03 | hallucination | `HallucinationMetric` | quality |
| 06 | correctness | `GEval` rubric | quality |
| 04 | bias | `BiasMetric` | safety |
| 05 | toxicity | `ToxicityMetric` | safety |
| 07 | PII / prompt leakage | `PIILeakageMetric` | safety |
| 08 | security (5 techniques) | `GEval` resistance rubric | security |
| 09 | misuse / regulated advice | `MisuseMetric`, `NonAdviceMetric` | security |
| 10 | role adherence | `RoleViolationMetric` | security |

## Setup

```bash
cd 03_DeepFramework
pip install -r requirements.txt
cp .env.sample .env      # put your gsk_... key in GROQ_API_KEY
```

Start the chatbot first (Subsystem A):

```bash
# from 01_.../01_chatbot/backend
GROQ_API_KEY=gsk_... CHATBOT_MODEL=qwen/qwen3.8-27b python -m uvicorn app:app --port 8201
```

## Run — pytest

```bash
pytest                         # all 161 cases (slow: real LLM calls)
pytest -m quality              # just the quality metrics
pytest tests/chatbot/test_06_chatbot_correctness.py -s
```

`needs_chatbot` tests auto-skip if `:8201` is unreachable.

## Run — dashboard (`:8203`)

```bash
uvicorn dashboard.app:app --port 8203     # open http://localhost:8203
```

One card per metric (21 total). Pick a **Target** (Chatbot A `:8201` or RAG
Explorer B `:8202`) and **cases per run**, then hit each card's **▶ Run**, or
**Run all visible** for the current category tab. Cards show verdict, avg
score, and expandable per-case details (input · reply · judge reason).
Results persist to `dashboard/results.json`.

Headless (same specs):

```bash
python -m dashboard.runner --limit 1                       # every chatbot metric
python -m dashboard.runner --target rag --category retrieval
python -m dashboard.runner --keys correctness role_violation --limit 2
```

### API

| Verb | Path | Body |
|------|------|------|
| GET | `/api/status` | — · targets up? + every metric's latest run + counts |
| GET | `/api/specs` | — · the metric catalog |
| POST | `/api/run/{key}` | `{target, limit}` · run one metric |
| POST | `/api/run-all` | `{keys[], target, limit}` |

## Notes

- Judge ≠ target on purpose: chatbot answers with `qwen/qwen3.8-27b`, judge is
  `openai/gpt-oss-120b`. A judge scoring its own family inflates scores.
- Groq free tier rate-limits hard. The runner spaces calls (`EVAL_CASE_DELAY`,
  default 4s) and backs off once on a 429 (`EVAL_RATE_BACKOFF`, default 35s).
- `VWO_500_Test_Cases.csv` is unrelated sample data, not wired into anything.
