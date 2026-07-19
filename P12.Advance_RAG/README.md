# Advanced RAG Explorer (P12)

End-to-end teaching demo for The Testing Academy. Upgrades a basic single-embedding RAG
with techniques that matter at scale on a real corpus (5,000 VWO test cases):

- **Hybrid retrieval** — `bge-m3` produces dense + sparse vectors from one model
- **Vector DB** — Qdrant (embedded/local, no Docker) with native dense + sparse + filters
- **Re-ranking** — `BAAI/bge-reranker-v2-m3` cross-encoder
- **Query rewriting** — alternate phrasings before retrieval
- **Generation** — grounded Q&A + structured test-case generation

> The original spec called for **OpenRouter (deepseek)** for rewriting/generation; this build
> uses **Groq** (`openai/gpt-oss-120b`) instead, since that's the only LLM API key configured
> in this repo. Swap `lib/groq_client.py` for an OpenRouter client if you have a key.

UI uses a Claude-inspired theme (warm cream + coral) with a two-pane layout: left = pipeline
stage tracker (live), right = active content / chat. See `static/explainer.html` for a full
animated write-up of the architecture.

This is a sibling build to [`P11.Advance_RAG_Pipeline/Advance_RAG`](../P11.Advance_RAG_Pipeline/Advance_RAG) —
same architecture, kept as a separate project per the P12 prompt spec.

## Pipeline

**Stage 1 (Ingest):**
CSV/XLSX → rows → assemble docs → chunk (1 row = 1 chunk if small) →
bge-m3 (dense + sparse) → Qdrant collection `vwo_test_cases`

**Stage 2 (Chat):**
Question → rewrite (Groq) → embed → dense + sparse search →
RRF fuse → bge-reranker-v2-m3 → Groq → grounded answer

## Setup

```bash
cd P12_Advance_RAG
python -m venv .venv
.venv\Scripts\activate      # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
```

Qdrant runs **embedded** by default (file store at `./qdrant_data/`) — no Docker required.
To use a Qdrant server instead, set `QDRANT_URL=http://host:6333` in `.env`.

## Run

```bash
.venv\Scripts\python app.py
# open http://127.0.0.1:5050
```

The first request hits cold model loaders (bge-m3 ~2.3 GB, bge-reranker ~570 MB, downloaded
from Hugging Face on first use) — subsequent requests are fast.

### CLI ingestion (optional)

```bash
python ingest.py testcase/test_cases.csv \
  --text-cols title,steps,expected,tags \
  --meta-cols id,jira_id,priority,module
```

## What you can see in the UI

### `/upload`
- File picker accepts `.csv`, `.xlsx`, `.xls`.
- After upload: row count, columns, first 5 rows, dtypes.
- Pick text columns (concatenated into the embedded document) and metadata columns (kept in
  Qdrant payload for filtering).

### `/ingest` (live SSE)
- Stage tracker: Read → Build docs → Chunk → Embed → Index.
- **Chunk**: histogram, total chunks, avg/min/max chars, sample chunks.
- **Embed**: progress bar, dense vector preview (first 8 dims), sparse top-5 tokens by weight.
- **Index**: Qdrant collection info.

### `/chunks`
- Paginated viewer (50/page) over the entire collection.
- Search box (substring) + filters (`priority`, `module`, `jira_id`).
- Each chunk card: id, payload, dense preview, sparse preview, full text.
- Chunks used in the most recent chat answer are outlined in coral.

### `/chat`
- Chat box on the right; pipeline stage tracker on the left updates per query.
- After each turn: the 3 query rewrites, dense top-N vs sparse top-N vs RRF-fused top-N,
  re-rank before/after table, final answer with `[Chunk N]` citations.
- Two modes auto-detected:
  - **Answer** — grounded Q&A on test cases.
  - **Generate** — phrases like "create a new test case for JIRA VWO-1234" produce a
    structured test case (Title / Preconditions / Steps / Expected / Priority / Tags) using
    retrieved similar test cases as templates.

## Tunables (`.env` or `lib/config.py`)

| Knob               | Default | Meaning                                          |
|---------------------|---------|--------------------------------------------------|
| `CHUNK_SIZE`        | 1000    | Max chars per chunk before splitting             |
| `CHUNK_OVERLAP`     | 150     | Chars repeated between adjacent chunks           |
| `TOP_N_HYBRID`      | 20      | Candidates per dense / sparse search             |
| `TOP_K_RERANK`      | 4       | Final chunks sent to the LLM after rerank        |
| `RRF_K`             | 60      | Reciprocal Rank Fusion smoothing constant        |
| `REWRITE_ENABLED`   | true    | Use Groq to generate alt phrasings before search |
| `BGE_USE_FP16`      | 1       | Halves model memory (recommended on modest RAM)  |
| `INGEST_BATCH`      | 16      | Embedding batch size during ingest               |

## Troubleshooting

- **Groq 401** — `.env` is missing or `GROQ_API_KEY` is wrong.
- **First query is slow** — bge-m3 + reranker downloading + warming. Subsequent calls are
  faster (still CPU-bound without a GPU).
- **`OpenBLAS ... Memory allocation still failed`** — the machine is low on free RAM
  (bge-m3 + torch need ~2-3 GB free to load). Close other apps/processes and retry;
  `BGE_USE_FP16=1` (default) already halves the model's memory footprint.
- **Port 5050 busy** — change `PORT` in `.env`.
- **`QDRANT_URL` connection refused** — only relevant if you explicitly set it to point at a
  server. Default is embedded local storage; nothing extra to start.
