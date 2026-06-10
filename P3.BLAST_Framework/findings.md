# Findings

## Phase 2 — Link Discoveries

### Jira
- Base URL: `https://bugzzzzz.atlassian.net` (extracted from JIRA_URL in .env)
- Auth: Basic auth (email:token) — Jira API v3
- CORS: Jira blocks browser-direct requests → Express proxy required
- Ticket KAN-4 lives at: `https://bugzzzzz.atlassian.net/rest/api/3/issue/KAN-4`
- Description field uses Atlassian Document Format (ADF) — requires recursive text extraction

### GROQ
- API: OpenAI-compatible at `https://api.groq.com/openai/v1`
- Model specified by user: `openai/gpt-oss-120b` (free tier)
- Verify script tests with `llama-3.1-8b-instant` (known stable model)
- GROQ may return JSON with markdown fences → regex fallback needed

### Architecture Constraint
- Jira API CORS restriction forces a server-side proxy
- GROQ API was initially considered browser-direct but routed through server for consistency

## Key Constraints
- No external UI library (lightweight requirement)
- Settings must survive page refresh → localStorage
- .env credentials auto-populate settings on first load via `/api/config`

## Risks
| Risk | Mitigation |
|---|---|
| `openai/gpt-oss-120b` model unavailable on GROQ | Configurable in Settings — user can change |
| GROQ returns malformed JSON | Regex fallback + clear error display |
| Jira token expiry | Settings UI allows re-entry |
| ADF description with complex nested content | Recursive `adfToText()` handles all node types |
