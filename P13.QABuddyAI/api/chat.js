// POST /api/chat — BM25 retrieval + Groq cited generation.
const { search } = require('../lib/search.js');

const GENERATE_RE = /\b(generate|create|write|draft)\b/i;

const BADGES = {
  selenium: 'Selenium',
  playwright: 'Playwright',
  test_cases: 'Test case',
  jira: 'JIRA',
  docs: 'Docs',
  prd: 'PRD',
  transcripts: 'Meeting',
  lucid: 'Lucid',
  jenkins: 'Jenkins',
  glossary: 'Glossary',
};

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ detail: 'POST only' });
    return;
  }
  const body = req.body || {};
  const question = String(body.question || '').trim();
  if (!question) {
    res.status(400).json({ detail: 'Question must not be empty' });
    return;
  }
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    res.status(500).json({ detail: 'GROQ_API_KEY not configured on the deployment' });
    return;
  }

  const sourceFilter = Array.isArray(body.source_types) ? body.source_types : null;
  const mode = ['answer', 'generate'].includes(body.mode)
    ? body.mode
    : GENERATE_RE.test(question) ? 'generate' : 'answer';

  const hits = search(question, 6, sourceFilter);
  if (!hits.length) {
    res.status(200).json({
      answer: "I couldn't find this in the QA knowledge base. Try rephrasing or check the source directly.",
      mode, citations: [], model: 'bm25-only', total_tokens: 0,
    });
    return;
  }

  const context = hits
    .map((h, i) => `[${i + 1}] (${h.chunk.source_type} — ${h.chunk.label})\n${h.chunk.text}`)
    .join('\n\n---\n\n');

  const system =
    mode === 'generate'
      ? 'You are QA Buddy, a senior QA engineer. Generate structured test cases (id, title, priority, steps, expected) grounded ONLY in the provided context chunks. Cite sources inline using plain square-bracket numbers exactly like [1] or [2] — never any other citation format. If the context is insufficient, say so.'
      : 'You are QA Buddy, a senior QA engineer assistant. Answer ONLY from the provided context chunks. Cite every claim inline using plain square-bracket numbers exactly like [1] or [2], where the number is the chunk number — never use any other citation format. If the answer is not in the context, say you could not find it in the QA knowledge base.';

  const model = process.env.GROQ_MODEL || 'openai/gpt-oss-120b';
  const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      max_tokens: 1200,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: `Context chunks:\n\n${context}\n\nQuestion: ${question}` },
      ],
    }),
  });

  if (!groqRes.ok) {
    const errText = await groqRes.text();
    res.status(502).json({ detail: `Groq API error ${groqRes.status}: ${errText.slice(0, 300)}` });
    return;
  }

  const data = await groqRes.json();
  // gpt-oss models sometimes emit 【1†L0-L5】-style citations; normalize to [1]
  const answer = (data.choices?.[0]?.message?.content || '').replace(/【(\d+)†[^】]*】/g, '[$1]');
  res.status(200).json({
    answer,
    mode,
    model,
    total_tokens: data.usage?.total_tokens || 0,
    citations: hits.map((h, i) => ({
      n: i + 1,
      badge: BADGES[h.chunk.source_type] || h.chunk.source_type,
      citation: h.chunk.label,
      snippet: h.chunk.text.slice(0, 360),
      score: Math.round(h.score * 100) / 100,
    })),
  });
};
