module.exports = async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ message: 'Method not allowed' });

  const jiraBase = process.env.JIRA_URL?.split('/browse')[0] || '';
  res.json({
    jiraBaseUrl: jiraBase,
    jiraEmail:   process.env.JIRA_EMAIL  || '',
    jiraToken:   process.env.JIRA_TOKEN  || '',
    groqKey:     process.env.GROQ_KEY    || '',
    groqModel:   process.env.GROQ_MODEL  || 'openai/gpt-oss-120b'
  });
};
