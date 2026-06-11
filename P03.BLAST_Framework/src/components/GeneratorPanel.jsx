import { useState, useEffect } from 'react';

const STEPS = [
  '📥 Fetching Jira ticket...',
  '🤖 Generating test plan with AI...'
];

export default function GeneratorPanel({
  ticketId, setTicketId, onGenerate, loading, error, isConfigured, onOpenSettings
}) {
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    if (!loading) { setStepIdx(0); return; }
    setStepIdx(0);
    const t = setTimeout(() => setStepIdx(1), 2800);
    return () => clearTimeout(t);
  }, [loading]);

  return (
    <div className="generator-card">
      <div className="generator-header">
        <h2>Generate Test Plan from Jira</h2>
        <p>Enter a Jira ticket ID — AI will fetch the ticket and produce a full test plan automatically</p>
      </div>

      {!isConfigured && (
        <div className="warning-banner">
          ⚠ Jira or GROQ credentials not configured.{' '}
          <button className="link-btn" onClick={onOpenSettings}>Open Settings →</button>
        </div>
      )}

      <div className="input-row">
        <div className="ticket-input-wrapper">
          <span className="input-prefix">TICKET</span>
          <input
            className="ticket-input"
            type="text"
            placeholder="KAN-4"
            value={ticketId}
            onChange={e => setTicketId(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && !loading && isConfigured && onGenerate()}
            disabled={loading}
          />
        </div>
        <button
          className="btn-generate"
          onClick={onGenerate}
          disabled={loading || !isConfigured || !ticketId.trim()}
        >
          {loading ? (
            <><span className="spinner" />{STEPS[stepIdx]}</>
          ) : (
            '⚡ Fetch & Generate Test Plan'
          )}
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <strong>❌ Error</strong>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
