/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    instrumentationHook: true,
  },
  transpilePackages: [
    'react-markdown',
    'remark-gfm',
    'remark-parse',
    'unified',
    'bail',
    'is-plain-obj',
    'trough',
    'vfile',
    'vfile-message',
    'unist-util-stringify-position',
    'mdast-util-from-markdown',
    'mdast-util-to-markdown',
    'mdast-util-gfm',
    'micromark',
    'micromark-util-combine-extensions',
    'micromark-extension-gfm',
    'decode-named-character-reference',
    'character-entities',
  ],
};

module.exports = nextConfig;
