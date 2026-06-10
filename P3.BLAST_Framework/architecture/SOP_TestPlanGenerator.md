# SOP: Jira Test Plan Generator
## BLAST Phase 3 — Layer 1 (Architecture)

## Goal
Fetch a Jira ticket by ID and produce a structured, AI-generated test plan.

## Inputs
| Field | Source | Required |
|---|---|---|
| ticketId | UI input | ✓ |
| jiraBaseUrl | Settings / .env | ✓ |
| jiraEmail | Settings / .env | ✓ |
| jiraToken | Settings / .env | ✓ |
| groqKey | Settings / .env | ✓ |
| groqModel | Settings / .env | ✓ (default: openai/gpt-oss-120b) |

## Tool Execution Flow (Layer 3)

### Step 1 — Fetch Jira Ticket (server.js)
- Endpoint: `GET {jiraBaseUrl}/rest/api/3/issue/{ticketId}`
- Auth: `Basic base64(jiraEmail:jiraToken)`
- ADF → Plain text via recursive `adfToText()` traversal
- Fields extracted: summary, description, issueType, priority, status, assignee, reporter, labels

### Step 2 — Build Prompt (server.js)
- Inject all extracted fields into structured prompt
- Request specific JSON schema with typed fields
- Minimum 7 test cases: 3 Functional, 2 Negative, 1 Edge, 1 Integration/UI
- Temperature: 0.3 (deterministic output)

### Step 3 — GROQ Generation (server.js)
- Endpoint: `POST https://api.groq.com/openai/v1/chat/completions`
- Model: configurable, default `openai/gpt-oss-120b`
- Max tokens: 4096
- Fallback JSON extraction: regex `\{[\s\S]*\}` if response contains markdown fences

### Step 4 — Response to Frontend
- Returns `{ jiraTicket, testPlan }` JSON
- Frontend renders without further processing

## Output Shape (gemini.md canonical schema)
```json
{
  "jiraTicket": {
    "key": "KAN-4",
    "summary": "string",
    "description": "string (plain text)",
    "issueType": "Story|Bug|Task|...",
    "priority": "Critical|High|Medium|Low",
    "status": "string",
    "assignee": "string",
    "reporter": "string"
  },
  "testPlan": {
    "testPlan": {
      "ticketId": "KAN-4",
      "title": "string",
      "overview": "string",
      "scope": {
        "inScope": ["string"],
        "outOfScope": ["string"]
      },
      "testCases": [
        {
          "id": "TC-001",
          "title": "string",
          "type": "Functional|Negative|Edge|Integration|UI",
          "priority": "Critical|High|Medium|Low",
          "preconditions": "string",
          "steps": ["string"],
          "expectedResult": "string"
        }
      ]
    }
  }
}
```

## Edge Cases & Handling
| Scenario | Handling |
|---|---|
| Ticket not found | 404 from Jira → shown in error banner |
| GROQ rate limit | 429 → shown in error banner |
| GROQ returns markdown fences | Regex extraction fallback |
| Empty description field | Graceful fallback in prompt: "No description provided" |
| ADF nested content | Recursive `adfToText()` traversal |
| Missing credentials | Validate before API call, show settings prompt |

## Architectural Invariants
- LLM output is NOT trusted until JSON parsed — always validate
- Credentials NEVER logged or exposed in client-side JS console
- Jira API calls ONLY go through server.js (CORS boundary)
- Settings stored in localStorage — user owns their data
- .env is source of truth for defaults; UI overrides are ephemeral

## Do NOT
- Cache Jira responses
- Expose raw tokens in `/api/config` response to the browser (currently does expose for local tool — acceptable for local-only use)
- Hallucinate Jira fields not present in the API response
- Call Jira API directly from the browser (CORS restricted)
