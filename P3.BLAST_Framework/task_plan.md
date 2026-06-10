# Task Plan — Jira Test Plan Generator

## Objective
Lightweight React app that fetches a Jira ticket (KAN-4) and auto-generates a structured
test plan using GROQ AI (openai/gpt-oss-120b).

## Phase Status
- [x] Phase 0: Initialization — COMPLETE
- [x] Phase 1 (B): Blueprint — COMPLETE
- [x] Phase 2 (L): Link — verify_connections.js built (run `npm run verify`)
- [x] Phase 3 (A): Architect — COMPLETE (3-layer build done)
- [ ] Phase 4 (S): Stylize — CSS designed; run app and confirm visual
- [ ] Phase 5 (T): Trigger — npm install + npm run dev

## Blueprint Checklist
- [x] Discovery questions answered (from Objective.md + .env)
- [x] Data schema defined in gemini.md
- [x] Blueprint approved (objective is clear)

## Architecture Decisions
| Decision | Choice | Reason |
|---|---|---|
| Frontend | React 18 + Vite | Lightweight, fast HMR |
| Backend | Express proxy | Jira API blocks browser CORS |
| GROQ calls | Via server | Single trusted path |
| State | localStorage | No backend DB needed |
| CSS | Vanilla CSS vars | Zero dependency, Jira-themed |

## File Map
```
P3.BLAST_Framework/
├── .env                         → Credentials (source of truth)
├── server.js                    → Layer 3: Express proxy (Jira + GROQ)
├── package.json
├── vite.config.js               → Proxy /api → localhost:3001
├── index.html
├── src/
│   ├── main.jsx
│   ├── App.jsx                  → State management + layout
│   ├── App.css                  → Full Jira-themed design system
│   ├── components/
│   │   ├── SettingsPanel.jsx    → Jira + GROQ config modal
│   │   ├── GeneratorPanel.jsx   → Ticket input + generate button
│   │   └── TestPlanView.jsx     → Rendered test plan + download
│   └── services/
│       └── apiService.js        → fetch wrappers
├── tools/
│   └── verify_connections.js   → Phase 2 link verification
└── architecture/
    └── SOP_TestPlanGenerator.md → Phase 3 Layer 1 spec
```

## Run Order
1. `npm install`
2. `npm run verify`     → Phase 2: verify Jira + GROQ connections
3. `npm run dev`        → Phase 4/5: launch app on localhost:5173
