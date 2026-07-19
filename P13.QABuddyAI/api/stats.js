const { kb } = require('../lib/search.js');

module.exports = (req, res) => {
  const by_source = {};
  for (const c of kb) by_source[c.source_type] = (by_source[c.source_type] || 0) + 1;
  res.status(200).json({
    total_chunks: kb.length,
    by_source,
    sources_active: Object.keys(by_source).length,
  });
};
