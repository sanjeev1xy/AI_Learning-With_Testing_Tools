import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function StatCard({ label, value, colorClass }) {
  return (
    <div className={`stat-card ${colorClass}`}>
      <div className="stat-value">{value ?? '-'}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function FileDropZone({ label, file, onChange, id }) {
  return (
    <div className={`drop-zone ${file ? 'drop-zone--filled' : ''}`}>
      <div className="drop-badge">{label}</div>
      <label htmlFor={id} className="drop-label">
        <span className="drop-icon">{file ? '✅' : '📂'}</span>
        <span className="drop-filename">
          {file ? file.name : 'Click to select JSON file'}
        </span>
        <span className="drop-hint">
          {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Build result .json'}
        </span>
      </label>
      <input id={id} type="file" accept=".json,application/json" onChange={onChange} className="hidden-input" />
    </div>
  );
}

function parseStats(text) {
  const get = (pattern) => {
    const m = text.match(pattern);
    return m ? m[1] : '—';
  };
  return {
    flaky: get(/\*\s*FLAKY:\s*(\d+)/i),
    consistent: get(/\*\s*CONSISTENT_FAILURES:\s*(\d+)/i),
    passes: get(/\*\s*PASSES:\s*(\d+)/i),
    failures: get(/\*\s*FAILURES:\s*(\d+)/i),
  };
}

export default function App() {
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const canAnalyze = file1 && file2 && !loading;

  const analyze = async () => {
    if (!canAnalyze) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const form = new FormData();
    form.append('build1', file1);
    form.append('build2', file2);

    try {
      const res = await fetch('/analyze', { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Analysis failed');

      const output = data?.outputs?.[0]?.outputs?.[0];
      const text = output?.results?.message?.text;
      const usage = output?.results?.message?.data?.properties?.usage;
      const timestamp = output?.results?.message?.data?.timestamp;

      setResult({ text, usage, timestamp });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const stats = result?.text ? parseStats(result.text) : null;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🔍</span>
            <div>
              <h1 className="logo-title">Flaky Test Analyzer</h1>
              <p className="logo-sub">AI-powered test flakiness detection · Langflow + Groq</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        <section className="card upload-card">
          <h2 className="section-title">
            <span className="section-num">01</span> Select Build Reports
          </h2>
          <div className="upload-row">
            <FileDropZone label="Build 1" file={file1} onChange={e => setFile1(e.target.files[0])} id="f1" />
            <div className="vs-pill">VS</div>
            <FileDropZone label="Build 2" file={file2} onChange={e => setFile2(e.target.files[0])} id="f2" />
          </div>

          <button className="analyze-btn" onClick={analyze} disabled={!canAnalyze}>
            {loading ? (
              <>
                <span className="spinner" />
                Analyzing with AI…
              </>
            ) : (
              <>
                <span>⚡</span> Analyze for Flaky Tests
              </>
            )}
          </button>
        </section>

        {error && (
          <div className="alert alert-error">
            <span className="alert-icon">⚠️</span>
            <div>
              <strong>Error</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-state">
            <div className="loading-bar" />
            <p>Sending files to Langflow · running Groq analysis…</p>
          </div>
        )}

        {result && (
          <div className="results-section">
            <section className="stats-row">
              <StatCard label="Flaky Tests" value={stats.flaky} colorClass="stat-orange" />
              <StatCard label="Consistent Failures" value={stats.consistent} colorClass="stat-red" />
              <StatCard label="Passes" value={stats.passes} colorClass="stat-green" />
              <StatCard label="Failures" value={stats.failures} colorClass="stat-amber" />
            </section>

            <section className="card report-card">
              <div className="report-header">
                <div>
                  <h2 className="section-title" style={{ marginBottom: 0 }}>
                    <span className="section-num">02</span> AI Analysis Report
                  </h2>
                  {result.timestamp && (
                    <p className="report-ts">{result.timestamp}</p>
                  )}
                </div>
                {result.usage && (
                  <div className="token-info">
                    <span className="token-chip">↑ {result.usage.input_tokens} in</span>
                    <span className="token-chip">↓ {result.usage.output_tokens} out</span>
                    <span className="token-chip total">{result.usage.total_tokens} total</span>
                  </div>
                )}
              </div>
              <div className="report-body">
                <ReactMarkdown>{result.text}</ReactMarkdown>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
