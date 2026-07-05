# P10.RAG

RAG (Retrieval-Augmented Generation) experiments — from a bare-bones pipeline to a full explorer UI.

## Projects

### RestfulBooker_RAG

A RAG Explorer app that demonstrates the complete pipeline end-to-end: document upload/ingestion, chunking, embedding, vector storage, retrieval, and LLM answer generation — with a React UI that visualizes every stage.

**Source document:** `data/TEST_PLAN.pdf` — a QA Test Plan for the Restful Booker API. You can also upload your own `.pdf` or `.txt` file from the UI.

**Pipeline:**
1. Read the document (`pdf-parse` for PDFs, plain read for `.txt`)
2. Split into overlapping chunks (~800 chars, 120 overlap)
3. Embed each chunk with **Nomic Embed** (`nomic-ai/nomic-embed-text-v1.5`, run locally via `@huggingface/transformers`, no API key)
4. Store embeddings in a local file-backed vector store (cosine similarity, ChromaDB-style collection API)
5. On query: embed the question, retrieve the top-k matching chunks
6. Send the question + retrieved chunks to **Groq** (`openai/gpt-oss-120b`) to generate the final answer

**Stack:** Node.js + Express (backend), React + Vite (frontend). Pure JavaScript end to end — no Python.

**Screenshot:**

![RAG Explorer UI](RestfulBooker_RAG/docs/screenshot.png)

**Run it:**

```bash
# backend
cd RestfulBooker_RAG/backend
npm install
cp .env.example .env   # add your GROQ_API_KEY
node index.js

# frontend
cd RestfulBooker_RAG/frontend
npm install
npm run dev
```

Open http://localhost:5173, click **Ingest Document** (or upload your own file first), then ask a question.

### Basic_RAG

Prompt spec + source PRD (`data/PRD.pdf`) for a simpler single-document RAG walkthrough.

### Advance_RAG

Reserved for a more advanced RAG setup (multi-doc, re-ranking, etc.) — not yet built.
