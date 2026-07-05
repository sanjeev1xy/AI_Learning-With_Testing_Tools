import { useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

const STAGES = [
  { key: 'read', label: 'Read PDF' },
  { key: 'chunk', label: 'Chunk' },
  { key: 'embed', label: 'Embed (Nomic)' },
  { key: 'store', label: 'Store (ChromaDB)' },
]

function App() {
  const [ingesting, setIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState(null)
  const [ingestError, setIngestError] = useState(null)
  const [completedStages, setCompletedStages] = useState([])

  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryResult, setQueryResult] = useState(null)
  const [queryError, setQueryError] = useState(null)

  const runIngest = async () => {
    setIngesting(true)
    setIngestError(null)
    setIngestResult(null)
    setCompletedStages([])

    try {
      for (const stage of STAGES.slice(0, -1)) {
        await new Promise((r) => setTimeout(r, 250))
        setCompletedStages((prev) => [...prev, stage.key])
      }

      const res = await fetch(`${API_BASE}/api/ingest`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Ingestion failed')

      setCompletedStages(STAGES.map((s) => s.key))
      setIngestResult(data)
    } catch (err) {
      setIngestError(err.message)
    } finally {
      setIngesting(false)
    }
  }

  const runQuery = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    setQuerying(true)
    setQueryError(null)
    setQueryResult(null)

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 4 }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Query failed')
      setQueryResult(data)
    } catch (err) {
      setQueryError(err.message)
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>RAG Explorer</h1>
        <p className="subtitle">
          Restful Booker Test Plan &middot; PDF ingestion &rarr; chunking &rarr; Nomic embeddings &rarr; ChromaDB &rarr; Groq (gpt-oss-120b)
        </p>
      </header>

      <section className="panel">
        <h2>1. Ingestion Pipeline</h2>
        <div className="stages">
          {STAGES.map((stage) => (
            <div
              key={stage.key}
              className={`stage ${completedStages.includes(stage.key) ? 'done' : ''} ${ingesting && !completedStages.includes(stage.key) ? 'active' : ''}`}
            >
              {stage.label}
            </div>
          ))}
        </div>

        <button onClick={runIngest} disabled={ingesting} className="primary-btn">
          {ingesting ? 'Ingesting…' : 'Run Ingestion'}
        </button>

        {ingestError && <p className="error">{ingestError}</p>}

        {ingestResult && (
          <div className="ingest-result">
            <div className="stats-grid">
              <div className="stat">
                <span className="stat-label">Source</span>
                <span className="stat-value">{ingestResult.source_file}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Characters</span>
                <span className="stat-value">{ingestResult.total_characters}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Chunks</span>
                <span className="stat-value">{ingestResult.num_chunks}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Chunk size / overlap</span>
                <span className="stat-value">{ingestResult.chunk_size} / {ingestResult.chunk_overlap}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Embedding model</span>
                <span className="stat-value">{ingestResult.embedding_model}</span>
              </div>
            </div>

            <details className="chunks-preview">
              <summary>Preview {ingestResult.chunks_preview.length} chunks</summary>
              <ol>
                {ingestResult.chunks_preview.map((c) => (
                  <li key={c.id}>
                    <code>{c.id}</code> ({c.char_count} chars) — {c.preview}…
                  </li>
                ))}
              </ol>
            </details>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>2. Query Interface</h2>
        <form onSubmit={runQuery} className="query-form">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the Test Plan…"
          />
          <button type="submit" disabled={querying} className="primary-btn">
            {querying ? 'Thinking…' : 'Ask'}
          </button>
        </form>

        {queryError && <p className="error">{queryError}</p>}

        {queryResult && (
          <div className="query-result">
            <div className="chunks-block">
              <h3>Retrieved Chunks (top {queryResult.retrieved_chunks.length})</h3>
              {queryResult.retrieved_chunks.map((c) => (
                <div key={c.id} className="chunk-card">
                  <div className="chunk-meta">
                    <code>{c.id}</code>
                    <span className="similarity">similarity {c.similarity}</span>
                  </div>
                  <p>{c.text}</p>
                </div>
              ))}
            </div>

            <div className="answer-block">
              <h3>Answer (Groq · openai/gpt-oss-120b)</h3>
              <p className="answer-text">{queryResult.answer}</p>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
