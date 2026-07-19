# QA Buddy — QA Knowledge System

One question, one **cited** answer, grounded in your team's real QA knowledge: Selenium & Playwright frameworks, test cases, JIRA history, PRDs, meeting notes, Lucid flows and Jenkins logs.

**Live:** https://qabuddyai.vercel.app/

## How it works

1. **Understand** — your question is classified (answer / generate)
2. **Search** — BM25 keyword scoring across the sources you selected
3. **Rank & select** — only the 6 most relevant chunks are kept as context
4. **Cited answer** — Groq (`openai/gpt-oss-120b`) answers only from those chunks, citing `[n]`

## Project structure

```
api/            Vercel serverless functions
  chat.js       POST /api/chat  — BM25 retrieval + Groq cited generation
  health.js     GET  /api/health
  stats.js      GET  /api/stats — chunk counts per source
lib/
  kb.json       Knowledge base (29 chunks, 10 source types)
  search.js     BM25 (Okapi) in-memory search engine
public/
  index.html    Chat UI
  docs.html     Technical documentation
  architecture.html  System architecture diagram
data/           Raw QA source content (frameworks, test cases, tickets, logs)
```

No build step, no framework — plain static files + Node serverless functions.

## Deploy

```bash
npm i -g vercel
vercel login
vercel deploy --prod
```

Set the environment variable in Vercel → Project → Settings → Environment Variables:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | From console.groq.com (free tier available) |
| `GROQ_MODEL` | Optional, default `openai/gpt-oss-120b` |

## Pages

- `/` — chat with source filters, mode select (auto / answer / generate), cited answers
- `/docs.html` — technical documentation
- `/architecture.html` — system architecture diagram

---

Adapted from `chapter_08_QABuddyAI` in [PramodDutta/AITesterBlueprint3x](https://github.com/PramodDutta/AITesterBlueprint3x).
