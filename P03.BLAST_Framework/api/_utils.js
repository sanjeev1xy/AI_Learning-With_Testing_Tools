function adfToText(node) {
  if (!node) return '';
  if (node.type === 'text') return node.text || '';
  if (node.type === 'hardBreak') return '\n';
  if (Array.isArray(node.content)) return node.content.map(adfToText).join(' ');
  return '';
}

module.exports = { adfToText };
