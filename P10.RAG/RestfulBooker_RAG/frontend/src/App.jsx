import { useRef, useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'

const STAGES = [
  { key: 'read', num: 1, label: 'Load', sub: 'read document' },
  { key: 'chunk', num: 2, label: 'Chunk', sub: 'split text' },
  { key: 'embed', num: 3, label: 'Embed', sub: 'Nomic vectors' },
  { key: 'store', num: 4, label: 'Store', sub: 'ChromaDB' },
  { key: 'retrieve', num: 5, label: 'Retrieve', sub: 'top-k' },
  { key: 'answer', num: 6, label: 'Answer', sub: 'Groq LLM' },
]

const SUGGESTED_QUESTIONS = [
  'What is the objective of this test plan?',
  'What test design techniques are used?',
  'What tools are used for defect tracking?',
  'What are the entry and exit criteria for test execution?',
]

function App() {
  const [ingesting, setIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState(null)
  const [ingestError, setIngestError] = useState(null)
  const [activeStages, setActiveStages] = useState([])

  const [uploading, setUploading] = useState(false)
  const [uploadedName, setUploadedName] = useState(null)
  const [uploadError, setUploadError] = useState(null)
  const fileInputRef = useRef(null)

  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryResult, setQueryResult] = useState(null)
  const [queryError, setQueryError] = useState(null)
  const [showPrompt, setShowPrompt] = useState(false)

  const ingested = !!ingestResult

  const runIngest = async () => {
    setIngesting(true)
    setIngestError(null)
    setIngestResult(null)
    setActiveStages([])

    try {
      for (const stage of STAGES.slice(0, 4)) {
        setActiveStages((prev) => [...prev, stage.key])
        await new Promise((r) => setTimeout(r, 200))
      }

      const res = await fetch(`${API_BASE}/api/ingest`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Ingestion failed')

      setIngestResult(data)
    } catch (err) {
      setIngestError(err.message)
      setActiveStages([])
    } finally {
      setIngesting(false)
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    e.target.value = ''
    if (!file) return

    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!['.pdf', '.txt'].includes(ext)) {
      setUploadError('Only .pdf and .txt files are supported')
      return
    }

    setUploading(true)
    setUploadError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      setUploadedName(data.filename)
      setIngestResult(null)
      setIngestError(null)
      setActiveStages([])
      setQueryResult(null)
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const runReset = async () => {
    await fetch(`${API_BASE}/api/reset`, { method: 'POST' })
    setIngestResult(null)
    setIngestError(null)
    setActiveStages([])
    setQueryResult(null)
    setQueryError(null)
    setUploadedName(null)
    setUploadError(null)
  }

  const runQuery = async (q) => {
    const finalQuestion = (q ?? question).trim()
    if (!finalQuestion) return

    setQuestion(finalQuestion)
    setQuerying(true)
    setQueryError(null)
    setQueryResult(null)
    setShowPrompt(false)
    setActiveStages((prev) => [...prev.slice(0, 4), 'retrieve'])

    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: finalQuestion, top_k: 4 }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Query failed')
      setActiveStages((prev) => [...prev, 'answer'])
      setQueryResult(data)
    } catch (err) {
      setQueryError(err.message)
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">◆</span>
          <div>
            <h1>RAG Explorer</h1>
            <p className="subtitle">Upload &rarr; chunk &rarr; Nomic embed &rarr; ChromaDB &rarr; retrieve top-4 &rarr; Groq answer</p>
          </div>
        </div>
        <div className="badges">
          <span className="badge"><i className="dot" />ChromaDB</span>
          <span className="badge"><i className="dot" />nomic-embed-text</span>
          <span className="badge"><i className="dot" />openai/gpt-oss-120b</span>
        </div>
      </header>

      <div className="stepper">
        {STAGES.map((stage, idx) => (
          <div className="step-wrap" key={stage.key}>
            <div className={`step ${activeStages.includes(stage.key) ? 'done' : ''}`}>
              <span className="step-num">{stage.num}</span>
              <div>
                <div className="step-label">{stage.label}</div>
                <div className="step-sub">{stage.sub}</div>
              </div>
            </div>
            {idx < STAGES.length - 1 && <span className="step-arrow">&rarr;</span>}
          </div>
        ))}
      </div>

      <div className="columns">
        <section className="panel">
          <div className="panel-head">
            <h2>1 &middot; Ingestion</h2>
            <div className="panel-actions">
              <input
                type="file"
                accept=".pdf,.txt"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <button
                onClick={() => fileInputRef.current.click()}
                disabled={uploading || ingesting}
                className="ghost-btn"
              >
                {uploading ? 'Uploading…' : 'Upload File'}
              </button>
              <button onClick={runIngest} disabled={ingesting} className="primary-btn">
                {ingesting ? 'Ingesting…' : 'Ingest Document'}
              </button>
              <button onClick={runReset} disabled={ingesting} className="ghost-btn">
                Reset
              </button>
            </div>
          </div>

          {uploadedName && !ingestResult && (
            <p className="source-line">
              <span className="file-icon">📎</span> Uploaded <strong>{uploadedName}</strong> — click "Ingest Document" to process it.
            </p>
          )}
          {uploadError && <p className="error">{uploadError}</p>}
          {ingestError && <p className="error">{ingestError}</p>}

          {ingestResult && (
            <>
              <p className="source-line">
                <span className="muted">Source folder:</span> <code>{ingestResult.source_folder}</code>
              </p>
              <p className="source-line">
                <span className="file-icon">📄</span> {ingestResult.source_file}
              </p>

              <div className="stats-grid">
                <div className="stat">
                  <span className="stat-value">{ingestResult.num_pages}</span>
                  <span className="stat-label">Pages</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{ingestResult.num_chunks}</span>
                  <span className="stat-label">Chunks</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{ingestResult.embedding_dims}</span>
                  <span className="stat-label">Embed dims</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{ingestResult.num_chunks}</span>
                  <span className="stat-label">Stored</span>
                </div>
              </div>

              <p className="section-label">Sample embedding (first {ingestResult.sample_embedding.length} of {ingestResult.embedding_dims}):</p>
              <pre className="vector-preview">[{ingestResult.sample_embedding.join(', ')}, …]</pre>

              <p className="section-label">Chunk preview:</p>
              <div className="chunk-list">
                {ingestResult.chunks_preview.slice(0, 6).map((c) => (
                  <div key={c.id} className="chunk-card">
                    <div className="chunk-meta">
                      <span className="chunk-tag">chunk {c.id.replace('chunk-', '')}</span>
                      <span className="muted">{c.char_count} chars</span>
                    </div>
                    <p>{c.preview}…</p>
                  </div>
                ))}
              </div>
            </>
          )}

          {!ingestResult && !ingestError && !uploadedName && (
            <p className="empty-hint">Upload a .pdf or .txt file, then click "Ingest Document" to read, chunk, embed, and store it.</p>
          )}
        </section>

        <section className="panel">
          <h2>2 &middot; Ask the document</h2>

          <textarea
            className="question-box"
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What is the goal of this test plan?"
          />
          <div className="ask-row">
            <button onClick={() => runQuery()} disabled={querying || !ingested} className="primary-btn">
              {querying ? 'Thinking…' : 'Ask'}
            </button>
          </div>
          {!ingested && <p className="empty-hint">Ingest a document first.</p>}

          <div className="chips">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button key={q} className="chip" onClick={() => runQuery(q)} disabled={querying || !ingested}>
                {q}
              </button>
            ))}
          </div>

          {queryError && <p className="error">{queryError}</p>}

          {queryResult && (
            <>
              <div className="answer-head">
                <h3>Answer</h3>
                <span className="answer-meta">{queryResult.model} &middot; {queryResult.total_tokens} tok</span>
              </div>
              <div className="answer-block">
                <p className="answer-text">{queryResult.answer}</p>
              </div>

              <button className="link-btn" onClick={() => setShowPrompt((v) => !v)}>
                {showPrompt ? 'Hide' : 'Show'} the augmented prompt sent to Groq
              </button>
              {showPrompt && <pre className="prompt-preview">{queryResult.augmented_prompt}</pre>}

              <h3 className="context-title">Retrieved context &middot; top {queryResult.retrieved_chunks.length}</h3>
              {queryResult.retrieved_chunks.map((c, idx) => {
                const pct = Math.max(0, Math.min(100, Math.round(c.similarity * 100)))
                return (
                  <div key={c.id} className="context-card">
                    <div className="context-head">
                      <span>#{idx + 1} {c.metadata.source} &middot; chunk {c.metadata.chunk_index}</span>
                      <span className="match-pct">{pct}% match</span>
                    </div>
                    <div className="match-bar">
                      <div className="match-fill" style={{ width: `${pct}%` }} />
                    </div>
                    <p>{c.text}</p>
                  </div>
                )
              })}
            </>
          )}
        </section>
      </div>
    </div>
  )
}

export default App
