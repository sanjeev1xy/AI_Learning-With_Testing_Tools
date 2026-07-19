const { kb } = require('../lib/search.js');

module.exports = (req, res) => {
  const sources = [...new Set(kb.map((c) => c.source_type))];
  res.status(200).json({
    ok: true,
    status: 'ok',
    groq_key_set: Boolean(process.env.GROQ_API_KEY),
    llm: process.env.GROQ_MODEL || 'openai/gpt-oss-120b',
    search: 'BM25 hybrid',
    kb_chunks: kb.length,
    sources,
    timestamp: new Date().toISOString(),
  });
};
