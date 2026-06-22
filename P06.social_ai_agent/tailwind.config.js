/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: '#6366f1',
      },
      typography: {
        DEFAULT: {
          css: {
            color: '#e5e7eb',
            a: { color: '#818cf8' },
            h1: { color: '#f9fafb' },
            h2: { color: '#f9fafb' },
            h3: { color: '#f3f4f6' },
            code: { color: '#a5b4fc', background: '#1f2937' },
            pre: { background: '#1f2937' },
            strong: { color: '#f9fafb' },
          },
        },
      },
    },
  },
  plugins: [],
};
