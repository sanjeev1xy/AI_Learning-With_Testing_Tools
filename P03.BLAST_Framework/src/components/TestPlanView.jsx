import { useState } from 'react';

const TYPE_COLOR = {
  Functional: '#0052CC', Negative: '#DE350B', Edge: '#FF8B00',
  'Edge Case': '#FF8B00', Integration: '#6554C0', UI: '#00875A', Performance: '#0065FF'
};
const PRI_COLOR = {
  Critical: '#BF2600', High: '#DE350B', Medium: '#FF8B00', Low: '#36B37E'
};

function Badge({ text, map }) {
  const c = map[text] || '#5E6C84';
  return (
    <span style={{
      background: c + '20', color: c, border: `1px solid ${c}40`,
      padding: '2px 9px', borderRadius: 12, fontSize: 11, fontWeight: 700
    }}>
      {text}
    </span>
  );
}

function toMarkdown(ticket, plan) {
  let md = `# Test Plan: ${ticket.key}\n\n`;
  md += `| Field | Value |\n|---|---|\n`;
  md += `| Ticket | ${ticket.key} |\n| Summary | ${ticket.summary} |\n`;
  md += `| Type | ${ticket.issueType} |\n| Priority | ${ticket.priority} |\n| Status | ${ticket.status} |\n\n`;
  md += `## Overview\n${plan.overview}\n\n`;
  if (plan.scope) {
    md += `## Scope\n### In Scope\n${plan.scope.inScope?.map(i => `- ${i}`).join('\n')}\n\n`;
    md += `### Out of Scope\n${plan.scope.outOfScope?.map(i => `- ${i}`).join('\n')}\n\n`;
  }
  md += `## Test Cases\n\n`;
  plan.testCases?.forEach(tc => {
    md += `### ${tc.id}: ${tc.title}\n`;
    md += `**Type:** ${tc.type} | **Priority:** ${tc.priority}\n\n`;
    md += `**Preconditions:** ${tc.preconditions}\n\n`;
    md += `**Steps:**\n${tc.steps?.map((s, i) => `${i + 1}. ${s}`).join('\n')}\n\n`;
    md += `**Expected Result:** ${tc.expectedResult}\n\n---\n\n`;
  });
  return md;
}

export default function TestPlanView({ jiraTicket, testPlan }) {
  const [expanded, setExpanded] = useState(null);
  const plan = testPlan?.testPlan || testPlan;
  if (!plan) return null;

  const tcs = plan.testCases || [];
  const counts = tcs.reduce((acc, tc) => {
    acc[tc.type] = (acc[tc.type] || 0) + 1;
    return acc;
  }, {});
  const highCount = tcs.filter(tc => ['High', 'Critical'].includes(tc.priority)).length;

  const download = () => {
    const blob = new Blob([toMarkdown(jiraTicket, plan)], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: `TestPlan_${jiraTicket.key}.md` });
    a.click(); URL.revokeObjectURL(url);
  };

  const copy = () => navigator.clipboard.writeText(toMarkdown(jiraTicket, plan));

  return (
    <div className="results">
      <div className="ticket-card">
        <div className="ticket-meta">
          <span className="ticket-key">{jiraTicket.key}</span>
          <Badge text={jiraTicket.issueType} map={TYPE_COLOR} />
          <Badge text={jiraTicket.priority} map={PRI_COLOR} />
          <span className="status-chip">{jiraTicket.status}</span>
          <span className="assignee-chip">👤 {jiraTicket.assignee}</span>
        </div>
        <h3 className="ticket-summary">{jiraTicket.summary}</h3>
        {jiraTicket.description && (
          <p className="ticket-desc">{jiraTicket.description.slice(0, 220)}{jiraTicket.description.length > 220 ? '…' : ''}</p>
        )}
      </div>

      <div className="plan-header">
        <div className="plan-title-block">
          <h2 className="plan-title">{plan.title}</h2>
          <p className="plan-overview">{plan.overview}</p>
        </div>
        <div className="plan-actions">
          <button className="btn-action" onClick={copy}>📋 Copy</button>
          <button className="btn-action btn-dl" onClick={download}>⬇ .md</button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat"><span className="sn">{tcs.length}</span><span className="sl">Total Cases</span></div>
        <div className="stat"><span className="sn">{counts.Functional || 0}</span><span className="sl">Functional</span></div>
        <div className="stat"><span className="sn">{counts.Negative || 0}</span><span className="sl">Negative</span></div>
        <div className="stat"><span className="sn">{highCount}</span><span className="sl">High Priority</span></div>
      </div>

      {plan.scope && (
        <div className="scope-grid">
          <div className="scope-box in">
            <div className="scope-title">✅ In Scope</div>
            <ul>{plan.scope.inScope?.map((x, i) => <li key={i}>{x}</li>)}</ul>
          </div>
          <div className="scope-box out">
            <div className="scope-title">❌ Out of Scope</div>
            <ul>{plan.scope.outOfScope?.map((x, i) => <li key={i}>{x}</li>)}</ul>
          </div>
        </div>
      )}

      <div className="tc-section-title">
        <h3>Test Cases</h3>
        <span className="tc-count">{tcs.length} cases</span>
      </div>
      {tcs.map(tc => (
        <div
          key={tc.id}
          className={`tc-card ${expanded === tc.id ? 'open' : ''}`}
          onClick={() => setExpanded(expanded === tc.id ? null : tc.id)}
        >
          <div className="tc-row">
            <span className="tc-id">{tc.id}</span>
            <span className="tc-title">{tc.title}</span>
            <div className="tc-tags">
              <Badge text={tc.type} map={TYPE_COLOR} />
              <Badge text={tc.priority} map={PRI_COLOR} />
            </div>
            <span className="tc-chevron">{expanded === tc.id ? '▲' : '▼'}</span>
          </div>

          {expanded === tc.id && (
            <div className="tc-body">
              <div className="tc-field">
                <span className="tc-label">PRECONDITIONS</span>
                <p>{tc.preconditions}</p>
              </div>
              <div className="tc-field">
                <span className="tc-label">TEST STEPS</span>
                <ol>{tc.steps?.map((s, i) => <li key={i}>{s}</li>)}</ol>
              </div>
              <div className="tc-field tc-expected">
                <span className="tc-label">EXPECTED RESULT</span>
                <p>{tc.expectedResult}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
