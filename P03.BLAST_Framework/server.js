require('dotenv').config();
const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

const ENV = {
  jiraBaseUrl: process.env.JIRA_URL?.split('/browse')[0] || '',
  jiraEmail: process.env.JIRA_EMAIL || '',
  jiraToken: process.env.JIRA_TOKEN || '',
  groqKey: process.env.GROQ_KEY || '',
  groqModel: process.env.GROQ_MODEL || 'openai/gpt-oss-120b'
};

function adfToText(node) {
  if (!node) return '';
  if (node.type === 'text') return node.text || '';
  if (node.type === 'hardBreak') return '\n';
  if (Array.isArray(node.content)) return node.content.map(adfToText).join(' ');
  return '';
}

app.get('/api/config', (req, res) => {
  res.json({
    jiraBaseUrl: ENV.jiraBaseUrl,
    jiraEmail: ENV.jiraEmail,
    jiraToken: ENV.jiraToken,
    groqKey: ENV.groqKey,
    groqModel: ENV.groqModel
  });
});

app.post('/api/generate', async (req, res) => {
  const {
    ticketId,
    jiraBaseUrl = ENV.jiraBaseUrl,
    jiraEmail = ENV.jiraEmail,
    jiraToken = ENV.jiraToken,
    groqKey = ENV.groqKey,
    groqModel = ENV.groqModel
  } = req.body;

  if (!ticketId) return res.status(400).json({ message: 'ticketId is required' });
  if (!jiraBaseUrl || !jiraEmail || !jiraToken)
    return res.status(400).json({ message: 'Jira credentials missing. Open Settings to configure.' });
  if (!groqKey)
    return res.status(400).json({ message: 'GROQ API key missing. Open Settings to configure.' });

  let jiraTicket;
  try {
    const auth = Buffer.from(`${jiraEmail}:${jiraToken}`).toString('base64');
    const { data } = await axios.get(
      `${jiraBaseUrl}/rest/api/3/issue/${ticketId}`,
      { headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' } }
    );
    const f = data.fields;
    jiraTicket = {
      key: data.key,
      summary: f.summary || '',
      description: adfToText(f.description),
      issueType: f.issuetype?.name || 'Story',
      priority: f.priority?.name || 'Medium',
      status: f.status?.name || 'To Do',
      assignee: f.assignee?.displayName || 'Unassigned',
      reporter: f.reporter?.displayName || 'Unknown',
      labels: f.labels || [],
      acceptanceCriteria: adfToText(f.customfield_10016) || ''
    };
  } catch (err) {
    const msg = err.response?.data?.errorMessages?.[0] || err.message;
    return res.status(err.response?.status || 500).json({ message: `Jira fetch failed: ${msg}` });
  }

  const prompt = `You are a senior QA engineer. Generate a comprehensive test plan for the Jira ticket below.

TICKET ID: ${jiraTicket.key}
SUMMARY: ${jiraTicket.summary}
ISSUE TYPE: ${jiraTicket.issueType}
PRIORITY: ${jiraTicket.priority}
DESCRIPTION: ${jiraTicket.description || 'No description provided'}
ACCEPTANCE CRITERIA: ${jiraTicket.acceptanceCriteria || 'Not specified'}

Return ONLY valid JSON with NO markdown fences or extra text. Use this exact shape:
{
  "testPlan": {
    "ticketId": "${jiraTicket.key}",
    "title": "Test Plan: <summary>",
    "overview": "<2-3 sentence overview of what is being tested>",
    "scope": {
      "inScope": ["<item>", "<item>"],
      "outOfScope": ["<item>"]
    },
    "testCases": [
      {
        "id": "TC-001",
        "title": "<descriptive title>",
        "type": "Functional",
        "priority": "High",
        "preconditions": "<what must be true before this test>",
        "steps": ["Step 1: <action>", "Step 2: <action>"],
        "expectedResult": "<what should happen>"
      }
    ]
  }
}

Generate minimum 7 test cases:
- 3 Functional (happy path)
- 2 Negative (invalid inputs, error states)
- 1 Edge (boundary conditions)
- 1 Integration or UI test

Types must be one of: Functional, Negative, Edge, Integration, UI
Priorities must be one of: High, Medium, Low, Critical

Return only the JSON object. No explanation. No markdown.`;

  try {
    const groqRes = await axios.post(
      'https://api.groq.com/openai/v1/chat/completions',
      {
        model: groqModel,
        messages: [
          { role: 'system', content: 'You are a QA expert. Output only valid JSON test plans with no markdown.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.3,
        max_tokens: 4096
      },
      { headers: { Authorization: `Bearer ${groqKey}`, 'Content-Type': 'application/json' } }
    );

    const content = groqRes.data.choices[0].message.content.trim();
    let testPlan;
    try {
      testPlan = JSON.parse(content);
    } catch {
      const match = content.match(/\{[\s\S]*\}/);
      if (!match) throw new Error('GROQ returned unparseable response');
      testPlan = JSON.parse(match[0]);
    }

    res.json({ jiraTicket, testPlan });
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.message;
    res.status(err.response?.status || 500).json({ message: `GROQ generation failed: ${msg}` });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`\n⚡ Jira Test Plan Generator — Server`);
  console.log(`   API proxy  : http://localhost:${PORT}`);
  console.log(`   Jira URL   : ${ENV.jiraBaseUrl || '(not set)'}`);
  console.log(`   GROQ key   : ${ENV.groqKey ? '✓ configured' : '✗ missing'}\n`);
});
