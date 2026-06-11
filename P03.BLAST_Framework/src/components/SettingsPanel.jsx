import { useState } from 'react';

export default function SettingsPanel({ settings, onSave, onClose }) {
  const [form, setForm] = useState({ ...settings });

  const set = (key, val) => setForm(prev => ({ ...prev, [key]: val }));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>⚙ Settings</h2>
            <p className="modal-sub">Config loaded from .env — override as needed</p>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="settings-section">
            <div className="section-label">JIRA CONFIGURATION</div>
            <div className="field">
              <label>Base URL</label>
              <input
                type="text"
                placeholder="https://yourcompany.atlassian.net"
                value={form.jiraBaseUrl}
                onChange={e => set('jiraBaseUrl', e.target.value)}
              />
              <span className="field-hint">Your Atlassian domain — no /browse suffix</span>
            </div>
            <div className="field">
              <label>Email</label>
              <input
                type="email"
                placeholder="you@company.com"
                value={form.jiraEmail}
                onChange={e => set('jiraEmail', e.target.value)}
              />
            </div>
            <div className="field">
              <label>API Token</label>
              <input
                type="password"
                placeholder="ATATT3x..."
                value={form.jiraToken}
                onChange={e => set('jiraToken', e.target.value)}
              />
              <span className="field-hint">
                Generate at{' '}
                <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noreferrer">
                  id.atlassian.com
                </a>
              </span>
            </div>
          </div>

          <div className="settings-section">
            <div className="section-label">GROQ AI CONFIGURATION</div>
            <div className="field">
              <label>API Key</label>
              <input
                type="password"
                placeholder="gsk_..."
                value={form.groqKey}
                onChange={e => set('groqKey', e.target.value)}
              />
              <span className="field-hint">
                Get a free key at{' '}
                <a href="https://console.groq.com" target="_blank" rel="noreferrer">
                  console.groq.com
                </a>
              </span>
            </div>
            <div className="field">
              <label>Model</label>
              <input
                type="text"
                placeholder="openai/gpt-oss-120b"
                value={form.groqModel}
                onChange={e => set('groqModel', e.target.value)}
              />
              <span className="field-hint">Default: openai/gpt-oss-120b (free tier)</span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={() => onSave(form)}>Save Settings</button>
        </div>
      </div>
    </div>
  );
}
