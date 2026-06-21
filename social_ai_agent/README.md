# ContentForge

Local-first AI content pipeline. Generates LinkedIn posts, Medium articles, Instagram scripts, YouTube scripts, Dev.to articles, and cover images — all from a single topic — and tracks everything in a local Excel file.

## Stack

- **Next.js 14** (App Router) + React + Tailwind CSS
- **Groq** (`llama-3.3-70b-versatile`) — text generation
- **Google Imagen 3** (`imagen-3.0-generate-002`) — image generation via `@google/genai`
- **ExcelJS** — reads/writes `content_calendar.xlsx`
- **node-cron** — daily 09:00 trigger via `instrumentation.ts`

## Quick Start

### 1. Install

```bash
cd social_ai_agent
npm install
```

### 2. Add API keys

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
```

Get keys:
- Groq: https://console.groq.com/keys
- Gemini: https://aistudio.google.com/apikey

### 3. Run

```bash
npm run dev
```

Open **http://localhost:3000**

## Where things land

| Artifact | Location |
|---|---|
| Excel tracker | `content_calendar.xlsx` (project root) |
| Generated images | `public/images/` (served as `/images/…`) |
| Logs | Terminal / `npm run dev` output |

## How it works

1. **Agent 1** — Groq generates a unique topic from the keyword pool, appends a row to the Excel file with `Status=Pending`.
2. **Agent 2** — Groq writes LinkedIn post, Medium article, Instagram script, YouTube script, and Dev.to article into the row. Sets `Status=Imaging`.
3. **Agent 3** — Gemini Imagen generates 3 images (Medium 16:9, LinkedIn 16:9, Instagram 1:1), saves them to `public/images/`. Sets `Status=Done`.

Pipeline runs automatically at **09:00 local time** via `node-cron` (registered in `instrumentation.ts`). Click **"Run Pipeline Now"** in the dashboard to trigger manually.

## Dashboard tabs

- **Today's Content** — expandable sections for each platform, markdown-rendered for Medium/Dev.to, copy buttons, inline images.
- **Calendar** — full history table, newest first, colour-coded status.
- **Excel Log** — file metadata, per-row write history, download button.

## Recovering from errors

If a run fails mid-way, click **Run Pipeline Now** again. The pipeline skips agents whose work is already in the row (idempotent per day).

## Project structure

```
social_ai_agent/
├── instrumentation.ts      ← scheduler hook (runs once at startup)
├── content_calendar.xlsx   ← auto-created on first run
├── lib/
│   ├── types.ts            ← ContentRow interface, StatusType
│   ├── excelManager.ts     ← atomic read/write with mutex
│   ├── agents.ts           ← Agent 1-3 implementations
│   ├── pipeline.ts         ← orchestration + state
│   └── scheduler.ts        ← node-cron setup
├── app/
│   ├── page.tsx            ← dashboard with polling
│   ├── layout.tsx
│   ├── globals.css
│   └── api/
│       ├── run/            ← POST — trigger pipeline
│       ├── calendar/       ← GET — all rows
│       ├── today/          ← GET — today's row
│       ├── status/         ← GET — pipeline state + API health
│       └── download/       ← GET — serve .xlsx file
├── components/
│   ├── StatusCards.tsx
│   ├── ContentTabs.tsx
│   ├── CalendarTable.tsx
│   └── ExcelLog.tsx
└── public/images/          ← generated images (gitkeep placeholder)
```
