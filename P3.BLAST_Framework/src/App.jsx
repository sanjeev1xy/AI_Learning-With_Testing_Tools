import { useState, useEffect } from 'react';
import SettingsPanel from './components/SettingsPanel';
import GeneratorPanel from './components/GeneratorPanel';
import TestPlanView from './components/TestPlanView';
import { generateTestPlan, loadConfig } from './services/apiService';

const STORAGE_KEY = 'jira-tpg-settings';

const DEFAULT_SETTINGS = {
  jiraBaseUrl: '',
  jiraEmail: '',
  jiraToken: '',
  groqKey: '',
  groqModel: 'openai/gpt-oss-120b'
};

export default function App() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [showSettings, setShowSettings] = useState(false);
  const [ticketId, setTicketId] = useState('KAN-4');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setSettings(JSON.parse(stored));
    } else {
      loadConfig()
        .then(config => {
          setSettings(config);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
        })
        .catch(() => {});
    }
  }, []);

  const saveSettings = (next) => {
    setSettings(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setShowSettings(false);
  };

  const handleGenerate = async () => {
    if (!ticketId.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await generateTestPlan(ticketId.trim(), settings);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isConfigured = !!(
    settings.jiraBaseUrl && settings.jiraEmail && settings.jiraToken && settings.groqKey
  );

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <span className="logo">⚡</span>
            <div>
              <h1>Jira Test Plan Generator</h1>
              <span className="header-sub">Powered by GROQ AI</span>
            </div>
          </div>
          <div className="header-right">
            {isConfigured && (
              <span className="config-badge">
                ✓ Connected to {settings.jiraBaseUrl.replace('https://', '')}
              </span>
            )}
            <button className="settings-btn" onClick={() => setShowSettings(true)}>
              ⚙ Settings
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        <GeneratorPanel
          ticketId={ticketId}
          setTicketId={setTicketId}
          onGenerate={handleGenerate}
          loading={loading}
          error={error}
          isConfigured={isConfigured}
          onOpenSettings={() => setShowSettings(true)}
        />

        {result && (
          <TestPlanView
            jiraTicket={result.jiraTicket}
            testPlan={result.testPlan}
          />
        )}
      </main>

      {showSettings && (
        <SettingsPanel
          settings={settings}
          onSave={saveSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}
