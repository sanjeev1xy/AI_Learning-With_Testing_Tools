# Project Constitution — Jira Test Plan Generator
## BLAST gemini.md (authoritative schema + rules)

---

## Data Schema (canonical)

### API Request: POST /api/generate
```json
{
  "ticketId":    "string  — e.g. KAN-4",
  "jiraBaseUrl": "string  — e.g. https://bugzzzzz.atlassian.net",
  "jiraEmail":   "string  — Atlassian account email",
  "jiraToken":   "string  — Atlassian API token",
  "groqKey":     "string  — gsk_...",
  "groqModel":   "string  — default: openai/gpt-oss-120b"
}
```

### API Response: POST /api/generate
```json
{
  "jiraTicket": {
    "key":         "string",
    "summary":     "string",
    "description": "string (ADF extracted to plain text)",
    "issueType":   "Story | Bug | Task | Epic | Sub-task",
    "priority":    "Critical | High | Medium | Low",
    "status":      "string",
    "assignee":    "string",
    "reporter":    "string",
    "labels":      ["string"]
  },
  "testPlan": {
    "testPlan": {
      "ticketId": "string",
      "title":    "string",
      "overview": "string",
      "scope": {
        "inScope":    ["string"],
        "outOfScope": ["string"]
      },
      "testCases": [
        {
          "id":             "TC-001",
          "title":          "string",
          "type":           "Functional | Negative | Edge | Integration | UI",
          "priority":       "Critical | High | Medium | Low",
          "preconditions":  "string",
          "steps":          ["string"],
          "expectedResult": "string"
        }
      ]
    }
  }
}
```

### Settings (localStorage schema)
```json
{
  "jiraBaseUrl": "string",
  "jiraEmail":   "string",
  "jiraToken":   "string",
  "groqKey":     "string",
  "groqModel":   "string"
}
```

---

## Behavioral Rules

1. **Jira-only source of truth**: Test plan must be grounded in ticket fields.
   Never invent features, acceptance criteria, or behaviors not stated in the ticket.

2. **Minimum 7 test cases**: Always include 3 Functional + 2 Negative + 1 Edge + 1 Integration/UI.

3. **Deterministic output**: Temperature 0.3. Same ticket → same test plan structure.

4. **JSON fallback**: If GROQ wraps response in markdown fences, strip and re-parse.

5. **Credential safety**: Tokens are stored in localStorage only. Never console.log credentials.

6. **CORS boundary**: All Jira API traffic goes through server.js. No browser-to-Jira calls.

7. **Graceful degradation**: Missing description → prompt still works with "No description provided".

---

## Architectural Invariants

- Layer 1 (architecture/): SOP documents change BEFORE code changes
- Layer 2 (Navigation): server.js orchestrates flow between Jira and GROQ
- Layer 3 (tools/): verify_connections.js is atomic and testable independently
- `.env` is never committed to git
- Settings overrides in UI are ephemeral (localStorage, not .env mutations)

---

## Environment Variables (.env)
| Key | Description |
|---|---|
| `GROQ_KEY` | GROQ API key (gsk_...) |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_TOKEN` | Atlassian API token |
| `JIRA_URL` | Full Jira browse URL (base extracted by splitting on /browse) |

---

## Maintenance Log
| Date | Change | Author |
|---|---|---|
| 2026-06-10 | Initial build — all phases 0-3 complete | Claude Sonnet 4.6 |
