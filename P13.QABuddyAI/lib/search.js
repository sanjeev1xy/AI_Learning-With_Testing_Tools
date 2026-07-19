// BM25 (Okapi) in-memory search over the compact knowledge base.
const kb = require('./kb.json');

const K1 = 1.5;
const B = 0.75;

function tokenize(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^a-z0-9_.-]+/g, ' ')
    .split(/\s+/)
    .filter((t) => t.length > 2);
}

let index = null;

function getIndex() {
  if (index) return index;
  const docs = kb.map((c) => tokenize(c.text + ' ' + c.label));
  const df = {};
  for (const tokens of docs) {
    for (const t of new Set(tokens)) df[t] = (df[t] || 0) + 1;
  }
  const avgdl = docs.reduce((s, d) => s + d.length, 0) / docs.length;
  const tfs = docs.map((tokens) => {
    const tf = {};
    for (const t of tokens) tf[t] = (tf[t] || 0) + 1;
    return tf;
  });
  index = { docs, df, avgdl, tfs, n: docs.length };
  return index;
}

function search(query, topK = 6, sourceFilter = null) {
  const { df, avgdl, tfs, docs, n } = getIndex();
  const qTokens = tokenize(query);
  const scores = kb.map((chunk, i) => {
    if (sourceFilter && sourceFilter.length && !sourceFilter.includes(chunk.source_type)) {
      return { chunk, score: -1 };
    }
    let score = 0;
    for (const t of qTokens) {
      const tf = tfs[i][t] || 0;
      if (!tf) continue;
      const idf = Math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5));
      score += idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + B * (docs[i].length / avgdl))));
    }
    return { chunk, score };
  });
  return scores
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

module.exports = { kb, search };
