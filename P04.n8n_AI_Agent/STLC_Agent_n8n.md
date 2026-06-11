# STLC Agent — n8n AI-Powered Software Testing Life Cycle Automation

**Project:** P04 — n8n AI Agent
**Document:** STLC Agent Design + Implementation Guide
**Date:** 2026-06-11
**Author:** Sanjeev Kumar Thakur
**Stack:** n8n · GROQ (Llama-3.3-70b) · Jira · Google Sheets · Slack · Teams

---

## What Is the STLC Agent?

The **STLC Agent** is an n8n AI workflow that automates all 6 phases of the
Software Testing Life Cycle end-to-end. Given a Jira ticket ID (or a batch of
ticket IDs), it:

1. Analyses requirements
2. Generates a test plan
3. Writes test cases
4. Lists environment setup requirements
5. Tracks test execution status
6. Produces a test closure report

All output lands in **Google Sheets** (one tab per STLC phase) and optionally
posts a summary to **Slack** or **Microsoft Teams**.

---

## STLC — 6 Phases Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SOFTWARE TESTING LIFE CYCLE                       │
├──────────────────┬───────────────────────────────────────────────────┤
│ PHASE 1          │ Requirement Analysis                              │
│                  │ What can be tested? Ambiguities? Risks?           │
├──────────────────┼───────────────────────────────────────────────────┤
│ PHASE 2          │ Test Planning                                     │
│                  │ Scope · Approach · Tools · Effort · Timeline      │
├──────────────────┼───────────────────────────────────────────────────┤
│ PHASE 3          │ Test Case Development                             │
│                  │ Write test cases · Test data · Traceability       │
├──────────────────┼───────────────────────────────────────────────────┤
│ PHASE 4          │ Test Environment Setup                            │
│                  │ Infra · Config · Credentials · Entry criteria     │
├──────────────────┼───────────────────────────────────────────────────┤
│ PHASE 5          │ Test Execution                                    │
│                  │ Execute · Log results · File defects              │
├──────────────────┼───────────────────────────────────────────────────┤
│ PHASE 6          │ Test Cycle Closure                                │
│                  │ Metrics · Lessons learned · Sign-off report       │
└──────────────────┴───────────────────────────────────────────────────┘
```

---

## Architecture

```
                    TRIGGER LAYER
         ┌──────────┬──────────┬──────────┐
         │  Chat UI │  Slack   │  Teams   │
         │  Trigger │  Trigger │  Trigger │
         └────┬─────┴────┬─────┴────┬─────┘
              │          │          │
              └──────────┼──────────┘
                         ▼
              ┌─────────────────────┐
              │  INPUT ROUTER NODE  │
              │  (Switch/IF node)   │
              │  Extract Jira ID(s) │
              └────────┬────────────┘
                       │
              ┌────────▼────────────┐
              │  JIRA FETCH TOOL    │
              │  GET /issue/:key    │
              │  Returns: summary,  │
              │  description, AC,   │
              │  priority, type     │
              └────────┬────────────┘
                       │
         ┌─────────────▼──────────────────────────────┐
         │              STLC AI AGENT                  │
         │         (n8n AI Agent Node)                 │
         │  Brain: GROQ llama-3.3-70b-versatile        │
         │  Memory: Buffer Window (session context)    │
         │                                             │
         │  Tools available:                           │
         │   ├─ Jira Tool (fetch issue)                │
         │   ├─ Sheets Tool (write Phase 1 tab)        │
         │   ├─ Sheets Tool (write Phase 2 tab)        │
         │   ├─ Sheets Tool (write Phase 3 tab)        │
         │   ├─ Sheets Tool (write Phase 4 tab)        │
         │   ├─ Sheets Tool (write Phase 5 tab)        │
         │   └─ Sheets Tool (write Phase 6 tab)        │
         └─────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────────┐
              │  GOOGLE SHEETS      │
              │  One tab per phase  │
              │  Tab 1: Req Analysis│
              │  Tab 2: Test Plan   │
              │  Tab 3: Test Cases  │
              │  Tab 4: Env Setup   │
              │  Tab 5: Execution   │
              │  Tab 6: Closure     │
              └────────┬────────────┘
                       │
              ┌────────▼────────────┐
              │  NOTIFICATION NODE  │
              │  Slack / Teams post │
              │  STLC summary done  │
              └─────────────────────┘
```

---

## Google Sheets Structure

**Create one Google Sheet with 6 tabs:**

### Tab 1 — Requirement Analysis
| Column | Description |
|---|---|
| Jira ID | Ticket key (KAN-4) |
| Summary | Feature name |
| Requirement | Each requirement extracted |
| Testable? | Yes / No / Partially |
| Ambiguity / Risk | Any unclear or risky areas |
| Suggested Clarification | Question to raise with PO |
| Priority | High / Medium / Low |
| Created Date | Date AI ran |

### Tab 2 — Test Plan
| Column | Description |
|---|---|
| Jira ID | Ticket key |
| Plan Section | Scope / Objective / Approach / Out of Scope / Tools / Risks / Exit Criteria |
| Content | The AI-generated content for that section |
| Owner | QA Lead (editable) |
| Status | Draft / Reviewed / Approved |

### Tab 3 — Test Cases
| Column | Description |
|---|---|
| TC ID | TC-001 format |
| Jira ID | Linked ticket |
| Title | Short test case description |
| Type | Functional / Negative / Edge / Integration / UI |
| Priority | High / Medium / Low |
| Preconditions | What must be true before the test |
| Test Steps | Numbered steps |
| Expected Result | Expected outcome |
| Actual Result | Tester fills this |
| Status | Not Executed / Pass / Fail / Blocked |
| Assignee | Tester name |
| Execution Date | Execution date |
| Defect ID | Linked Jira defect if failed |
| Comments | Notes |

### Tab 4 — Environment Setup
| Column | Description |
|---|---|
| Jira ID | Ticket key |
| Env Layer | Browser / OS / DB / API / Auth / Data |
| Requirement | Specific setup requirement |
| Configuration | Steps or values needed |
| Status | Not Ready / In Progress / Ready |
| Owner | DevOps / QA |

### Tab 5 — Test Execution Tracker
| Column | Description |
|---|---|
| TC ID | From Tab 3 |
| Jira ID | Linked ticket |
| Execution Date | Date test run |
| Tester | Name |
| Environment | Where test was run |
| Status | Pass / Fail / Blocked / Not Executed |
| Defect ID | If Failed: linked Jira defect |
| Notes | Observations |

### Tab 6 — Test Closure Report
| Column | Description |
|---|---|
| Jira ID | Ticket key |
| Metric | e.g. Total TCs / Passed / Failed / Blocked |
| Value | Number or percentage |
| Observations | AI-generated comment |
| Recommendation | Go / No-Go / Conditional |
| Sign-Off Status | Pending / Approved |

---

## n8n Workflow — Complete Node List

### Workflow Name: `AI_3X_05_STLC_Agent`

```
Node 1:  Chat Trigger          — Primary: chat UI input
Node 2:  Slack Trigger         — Secondary: Slack channel message
Node 3:  Teams Trigger         — Secondary: MS Teams chat
Node 4:  Schedule Trigger      — Automated: hourly/daily run
Node 5:  Form Trigger          — Bulk: CSV upload of Jira IDs
Node 6:  Extract CSV           — Parse CSV file from Form
Node 7:  Loop (splitInBatches) — Iterate over each Jira ID
Node 8:  STLC AI Agent         — Core AI orchestrator (all 6 phases)
Node 9:  GROQ Brain            — llama-3.3-70b-versatile
Node 10: Memory Buffer         — Session context retention
Node 11: Jira Tool             — Fetch issue by key
Node 12: Sheets Tool — Phase 1 — Write Requirement Analysis tab
Node 13: Sheets Tool — Phase 2 — Write Test Plan tab
Node 14: Sheets Tool — Phase 3 — Write Test Cases tab
Node 15: Sheets Tool — Phase 4 — Write Env Setup tab
Node 16: Sheets Tool — Phase 5 — Write Execution Tracker tab
Node 17: Sheets Tool — Phase 6 — Write Closure Report tab
Node 18: Slack Node            — Post completion summary
```

---

## STLC AI Agent — System Prompt

This is the **System Message** for the n8n AI Agent node. Paste this verbatim into the
`Options > System Message` field:

```
You are the STLC Agent — an AI-powered Software Testing Life Cycle orchestrator
integrated with Jira and Google Sheets.

## Your Mission
When a user says "run stlc [JIRA-KEY]" or provides a Jira ticket ID with any STLC
intent, execute ALL 6 phases of the Software Testing Life Cycle for that ticket.
Do NOT skip phases. Do NOT ask for confirmation. Execute all 6 phases immediately.

---

## PHASE 1 — Requirement Analysis

Use the Jira tool to fetch the issue. Extract:
- Each requirement or acceptance criterion as a separate row
- Flag ambiguous, unclear, or missing requirements
- Flag high-risk areas (auth, payments, data mutation)

Write to Google Sheets Tab "Req Analysis":
Columns: Jira ID | Requirement | Testable (Yes/No/Partial) | Ambiguity/Risk | Clarification Needed | Priority

---

## PHASE 2 — Test Planning

Based on the Jira issue, generate a test plan with these sections:
1. Objective — What will be tested and why
2. Scope (In Scope) — Features and modules covered
3. Scope (Out of Scope) — What is excluded and why
4. Test Approach — Risk-based / Specification-based
5. Test Types — Functional, Regression, Smoke, API, UI
6. Tools — Playwright, Postman, GROQ, n8n
7. Entry Criteria — Conditions required before testing
8. Exit Criteria — Conditions required to declare testing complete
9. Risks — Top 3 risks and mitigations
10. Estimated Effort — Rough test case count and hours

Write each section as a separate row in Tab "Test Plan":
Columns: Jira ID | Plan Section | Content | Owner | Status

---

## PHASE 3 — Test Case Development

Generate comprehensive test cases. Cover ALL of these types:
- Functional (happy path) — minimum 3
- Negative (invalid inputs, errors) — minimum 2
- Edge Cases (boundaries, extremes) — minimum 2
- Integration (cross-module) — minimum 1
- UI/UX — minimum 1

For each test case:
- TC ID: TC-001, TC-002 (sequential, linked to Jira ID)
- Title: Short descriptive title
- Type: Functional / Negative / Edge / Integration / UI
- Priority: Critical / High / Medium / Low
- Preconditions: What must be true
- Test Steps: Numbered, specific, executable
- Expected Result: Exact expected outcome

Write to Tab "Test Cases":
Columns: TC ID | Jira ID | Title | Type | Priority | Preconditions | Test Steps | Expected Result | Actual Result | Status | Assignee | Execution Date | Defect ID | Comments

Set default: Actual Result = "" | Status = "Not Executed" | Assignee = "" | Execution Date = "" | Defect ID = ""

---

## PHASE 4 — Test Environment Setup

List all environment requirements to execute the test cases:
- Browser/Client: required browsers, versions
- OS: required operating systems
- Backend: APIs, services, endpoints needed
- Database: required data, seed scripts
- Authentication: test accounts needed (roles/permissions)
- Test Data: specific data sets
- External Integrations: Jira, Google Sheets, Slack, GROQ
- Network: special ports, VPN, localhost config
- Entry Criteria: checklist before QA can start

Write each requirement as a row in Tab "Env Setup":
Columns: Jira ID | Env Layer | Requirement | Configuration | Status | Owner

Set default: Status = "Not Ready" | Owner = "QA/DevOps"

---

## PHASE 5 — Test Execution Tracker Setup

Pre-populate the execution tracker with all TC IDs from Phase 3.
This gives the team a ready-to-fill tracker.

Write to Tab "Execution Tracker":
Columns: TC ID | Jira ID | Execution Date | Tester | Environment | Status | Defect ID | Notes

Set default: Status = "Not Executed" | all others = ""

---

## PHASE 6 — Test Closure Report

Generate a test closure report with these metrics (based on what was generated):
- Total Test Cases Created
- Functional TCs: count
- Negative TCs: count
- Edge Case TCs: count
- Integration TCs: count
- Estimated Pass Rate Target: 95%
- Defect Severity Distribution: (placeholder — to fill post-execution)
- Recommendation: "Ready for execution. Assign testers and set execution date."
- Go/No-Go: "Conditional — pending environment setup (Phase 4)"
- Lessons Learned: Any ambiguities found in Phase 1

Write each metric as a row in Tab "Closure Report":
Columns: Jira ID | Metric | Value | Observations | Recommendation | Sign-Off Status

Set default: Sign-Off Status = "Pending"

---

## Completion Message

After all 6 phases, reply to the user:

"✅ STLC Complete for [JIRA-KEY]

📋 Phase 1 — Requirement Analysis: [N] requirements extracted, [X] flagged for clarification
📝 Phase 2 — Test Plan: [N] sections written
🧪 Phase 3 — Test Cases: [N] test cases created ([F] Functional, [Neg] Negative, [E] Edge, [I] Integration, [U] UI)
🖥️ Phase 4 — Environment Setup: [N] requirements listed
▶️ Phase 5 — Execution Tracker: Pre-populated with [N] rows
📊 Phase 6 — Closure Report: Draft report written

All data written to Google Sheets. Status: READY FOR EXECUTION."

---

## Non-STLC Messages

If the message does NOT contain a Jira key or STLC intent, respond as a helpful
QA assistant. Answer questions about testing, STLC phases, best practices.
Do NOT run the STLC pipeline for non-STLC messages.

## STLC Trigger Phrases (case-insensitive, any of these activate the pipeline):
- "run stlc [KEY]"
- "stlc [KEY]"
- "full stlc for [KEY]"
- "run all phases [KEY]"
- "generate stlc [KEY]"
- Any message containing a Jira key pattern (e.g. KAN-4, PROJ-123) AND any of:
  stlc / test life cycle / all phases / full testing
```

---

## Individual Phase Commands

Users can also run individual phases on demand:

| Command | Action |
|---|---|
| `phase 1 KAN-4` | Run only Requirement Analysis |
| `phase 2 KAN-4` | Run only Test Planning |
| `phase 3 KAN-4` | Run only Test Case Development |
| `phase 4 KAN-4` | Run only Environment Setup |
| `phase 5 KAN-4` | Pre-populate Execution Tracker only |
| `phase 6 KAN-4` | Generate Closure Report only |
| `run stlc KAN-4` | Run ALL 6 phases |

Add this to the system prompt to support individual phase commands:

```
## Individual Phase Commands

If the message says "phase N [KEY]" (where N is 1–6), run ONLY that phase for
the given Jira key. Write only to that phase's Sheet tab. Confirm with:
"✅ Phase [N] complete for [KEY]. Written to [Tab Name]."
```

---

## n8n Workflow JSON (Import-Ready)

Save this as `AI_3X_05_STLC_Agent.json` and import into n8n via
**Workflows > Import from file**:

```json
{
  "name": "AI_3X_05_STLC_Agent",
  "nodes": [
    {
      "parameters": { "options": {} },
      "id": "stlc-chat-trigger",
      "name": "Chat Trigger",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "position": [240, 300]
    },
    {
      "parameters": {
        "trigger": ["message"],
        "channelId": { "__rl": true, "mode": "list", "value": "" },
        "options": {}
      },
      "id": "stlc-slack-trigger",
      "name": "Slack Trigger",
      "type": "n8n-nodes-base.slackTrigger",
      "position": [240, 460]
    },
    {
      "parameters": {
        "event": "newChatMessage",
        "chatId": { "__rl": true, "mode": "list", "value": "" }
      },
      "id": "stlc-teams-trigger",
      "name": "Teams Trigger",
      "type": "n8n-nodes-base.microsoftTeamsTrigger",
      "position": [240, 620]
    },
    {
      "parameters": {
        "rule": { "interval": [{ "field": "hours" }] }
      },
      "id": "stlc-schedule-trigger",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [240, 780]
    },
    {
      "parameters": {
        "formTitle": "STLC Agent — Bulk Jira Processing",
        "formDescription": "Upload a CSV with Jira IDs. The STLC Agent will run all 6 phases for each ticket.",
        "formFields": {
          "values": [{
            "fieldLabel": "CSV File with Jira IDs",
            "fieldType": "file",
            "fieldName": "csvFile",
            "multipleFiles": false,
            "acceptFileTypes": ".csv",
            "requiredField": true
          }]
        },
        "options": {
          "respondWithOptions": {
            "values": {
              "formSubmittedText": "STLC Agent received your CSV. Running all 6 STLC phases for each ticket..."
            }
          }
        }
      },
      "id": "stlc-form-trigger",
      "name": "Form Trigger — Bulk CSV",
      "type": "n8n-nodes-base.formTrigger",
      "position": [240, 940]
    },
    {
      "parameters": {
        "binaryPropertyName": "csvFile",
        "options": { "headerRow": true }
      },
      "id": "stlc-extract-csv",
      "name": "Extract CSV Data",
      "type": "n8n-nodes-base.extractFromFile",
      "position": [460, 940]
    },
    {
      "parameters": { "options": {} },
      "id": "stlc-loop",
      "name": "Loop Over Jira IDs",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [680, 940]
    },
    {
      "parameters": {
        "promptType": "define",
        "text": "=Run STLC for Jira ticket: {{ $json[\"Jira ID\"] }}",
        "options": {
          "systemMessage": "You are the STLC Agent... [PASTE FULL SYSTEM PROMPT FROM ABOVE]"
        }
      },
      "id": "stlc-ai-agent",
      "name": "STLC AI Agent",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "position": [900, 300]
    },
    {
      "parameters": {
        "model": "llama-3.3-70b-versatile",
        "options": {}
      },
      "id": "stlc-brain",
      "name": "GROQ Brain",
      "type": "@n8n/n8n-nodes-langchain.lmChatGroq",
      "position": [900, 120]
    },
    {
      "parameters": {
        "sessionIdType": "fromInput",
        "windowBuffer": 10
      },
      "id": "stlc-memory",
      "name": "Session Memory",
      "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
      "position": [1100, 120]
    },
    {
      "parameters": {
        "operation": "get",
        "issueKey": "={{ $fromAI('Issue_Key', '', 'string') }}",
        "additionalFields": {}
      },
      "id": "stlc-jira-tool",
      "name": "Fetch Jira Issue",
      "type": "n8n-nodes-base.jiraTool",
      "position": [1100, 300]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Req Analysis" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "Jira ID":               "={{ $fromAI('Jira_ID','','string') }}",
            "Requirement":           "={{ $fromAI('Requirement','','string') }}",
            "Testable":              "={{ $fromAI('Testable','','string') }}",
            "Ambiguity/Risk":        "={{ $fromAI('Ambiguity_Risk','','string') }}",
            "Clarification Needed":  "={{ $fromAI('Clarification_Needed','','string') }}",
            "Priority":              "={{ $fromAI('Priority','','string') }}"
          },
          "matchingColumns": ["Jira ID"]
        }
      },
      "id": "stlc-sheets-phase1",
      "name": "Sheets — Phase 1 Req Analysis",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 120]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Test Plan" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "Jira ID":       "={{ $fromAI('Jira_ID','','string') }}",
            "Plan Section":  "={{ $fromAI('Plan_Section','','string') }}",
            "Content":       "={{ $fromAI('Content','','string') }}",
            "Owner":         "={{ $fromAI('Owner','','string') }}",
            "Status":        "={{ $fromAI('Status','','string') }}"
          },
          "matchingColumns": ["Jira ID", "Plan Section"]
        }
      },
      "id": "stlc-sheets-phase2",
      "name": "Sheets — Phase 2 Test Plan",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 280]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Test Cases" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "TC ID":           "={{ $fromAI('TC_ID','','string') }}",
            "Jira ID":         "={{ $fromAI('Jira_ID','','string') }}",
            "Title":           "={{ $fromAI('Title','','string') }}",
            "Type":            "={{ $fromAI('Type','','string') }}",
            "Priority":        "={{ $fromAI('Priority','','string') }}",
            "Preconditions":   "={{ $fromAI('Preconditions','','string') }}",
            "Test Steps":      "={{ $fromAI('Test_Steps','','string') }}",
            "Expected Result": "={{ $fromAI('Expected_Result','','string') }}",
            "Actual Result":   "={{ $fromAI('Actual_Result','','string') }}",
            "Status":          "={{ $fromAI('Status','','string') }}",
            "Assignee":        "={{ $fromAI('Assignee','','string') }}",
            "Execution Date":  "={{ $fromAI('Execution_Date','','string') }}",
            "Defect ID":       "={{ $fromAI('Defect_ID','','string') }}",
            "Comments":        "={{ $fromAI('Comments','','string') }}"
          },
          "matchingColumns": ["TC ID"]
        }
      },
      "id": "stlc-sheets-phase3",
      "name": "Sheets — Phase 3 Test Cases",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 440]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Env Setup" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "Jira ID":       "={{ $fromAI('Jira_ID','','string') }}",
            "Env Layer":     "={{ $fromAI('Env_Layer','','string') }}",
            "Requirement":   "={{ $fromAI('Requirement','','string') }}",
            "Configuration": "={{ $fromAI('Configuration','','string') }}",
            "Status":        "={{ $fromAI('Status','','string') }}",
            "Owner":         "={{ $fromAI('Owner','','string') }}"
          },
          "matchingColumns": ["Jira ID", "Env Layer"]
        }
      },
      "id": "stlc-sheets-phase4",
      "name": "Sheets — Phase 4 Env Setup",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 600]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Execution Tracker" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "TC ID":           "={{ $fromAI('TC_ID','','string') }}",
            "Jira ID":         "={{ $fromAI('Jira_ID','','string') }}",
            "Execution Date":  "={{ $fromAI('Execution_Date','','string') }}",
            "Tester":          "={{ $fromAI('Tester','','string') }}",
            "Environment":     "={{ $fromAI('Environment','','string') }}",
            "Status":          "={{ $fromAI('Status','','string') }}",
            "Defect ID":       "={{ $fromAI('Defect_ID','','string') }}",
            "Notes":           "={{ $fromAI('Notes','','string') }}"
          },
          "matchingColumns": ["TC ID"]
        }
      },
      "id": "stlc-sheets-phase5",
      "name": "Sheets — Phase 5 Execution Tracker",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 760]
    },
    {
      "parameters": {
        "operation": "appendOrUpdate",
        "documentId": { "__rl": true, "mode": "list", "value": "YOUR_SHEET_ID" },
        "sheetName":  { "__rl": true, "mode": "list", "value": "Closure Report" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": {
            "Jira ID":         "={{ $fromAI('Jira_ID','','string') }}",
            "Metric":          "={{ $fromAI('Metric','','string') }}",
            "Value":           "={{ $fromAI('Value','','string') }}",
            "Observations":    "={{ $fromAI('Observations','','string') }}",
            "Recommendation":  "={{ $fromAI('Recommendation','','string') }}",
            "Sign-Off Status": "={{ $fromAI('Sign_Off_Status','','string') }}"
          },
          "matchingColumns": ["Jira ID", "Metric"]
        }
      },
      "id": "stlc-sheets-phase6",
      "name": "Sheets — Phase 6 Closure Report",
      "type": "n8n-nodes-base.googleSheetsTool",
      "position": [1300, 920]
    }
  ],
  "connections": {
    "Chat Trigger":              { "main": [[{ "node": "STLC AI Agent", "type": "main", "index": 0 }]] },
    "Slack Trigger":             { "main": [[{ "node": "STLC AI Agent", "type": "main", "index": 0 }]] },
    "Teams Trigger":             { "main": [[{ "node": "STLC AI Agent", "type": "main", "index": 0 }]] },
    "Schedule Trigger":          { "main": [[{ "node": "STLC AI Agent", "type": "main", "index": 0 }]] },
    "Form Trigger — Bulk CSV":   { "main": [[{ "node": "Extract CSV Data", "type": "main", "index": 0 }]] },
    "Extract CSV Data":          { "main": [[{ "node": "Loop Over Jira IDs", "type": "main", "index": 0 }]] },
    "Loop Over Jira IDs":        { "main": [[{ "node": "STLC AI Agent", "type": "main", "index": 0 }]] },
    "GROQ Brain":                { "ai_languageModel": [[{ "node": "STLC AI Agent", "type": "ai_languageModel", "index": 0 }]] },
    "Session Memory":            { "ai_memory": [[{ "node": "STLC AI Agent", "type": "ai_memory", "index": 0 }]] },
    "Fetch Jira Issue":          { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 0 }]] },
    "Sheets — Phase 1 Req Analysis":     { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 1 }]] },
    "Sheets — Phase 2 Test Plan":        { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 2 }]] },
    "Sheets — Phase 3 Test Cases":       { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 3 }]] },
    "Sheets — Phase 4 Env Setup":        { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 4 }]] },
    "Sheets — Phase 5 Execution Tracker":{ "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 5 }]] },
    "Sheets — Phase 6 Closure Report":   { "ai_tool": [[{ "node": "STLC AI Agent", "type": "ai_tool", "index": 6 }]] }
  },
  "meta": { "templateCredsSetupCompleted": false }
}
```

---

## Setup Steps

### Step 1 — Create Google Sheet

1. Go to Google Sheets → New spreadsheet
2. Rename it: `STLC Agent — QA Tracker`
3. Create 6 tabs (bottom tabs):
   - `Req Analysis`
   - `Test Plan`
   - `Test Cases`
   - `Env Setup`
   - `Execution Tracker`
   - `Closure Report`
4. Add header rows per schema above (Row 1 of each tab)
5. Copy the Sheet ID from the URL: `docs.google.com/spreadsheets/d/`**`YOUR_SHEET_ID`**`/edit`

### Step 2 — Import Workflow into n8n

1. Open n8n dashboard
2. Click **Workflows** → **Import from file** (or **Add workflow** → paste JSON)
3. Paste the JSON from above
4. Replace `"YOUR_SHEET_ID"` in all 6 Google Sheets nodes with your actual Sheet ID

### Step 3 — Configure Credentials

| Credential | Node | How to Set |
|---|---|---|
| Jira API | Fetch Jira Issue | Email + API Token (Jira → Account Settings → Security → API tokens) |
| GROQ API | GROQ Brain | API key from console.groq.com |
| Google Sheets | All 6 Sheets nodes | OAuth 2.0 — authorize via n8n credentials |
| Slack | Slack Trigger | OAuth — install n8n Slack app to workspace |
| Teams | Teams Trigger | OAuth — register app in Azure AD |

### Step 4 — Activate the Workflow

1. Click the **Active** toggle (top right of workflow canvas)
2. Confirm all nodes show green credential indicators
3. Test with a chat message: `run stlc KAN-4`

### Step 5 — Verify Output

After running for `KAN-4`:
- Tab `Req Analysis` → requirements listed, risks flagged
- Tab `Test Plan` → 10 plan sections filled
- Tab `Test Cases` → 9+ test cases written (all types covered)
- Tab `Env Setup` → environment checklist populated
- Tab `Execution Tracker` → pre-populated rows, Status = Not Executed
- Tab `Closure Report` → draft metrics and recommendation

---

## Chat Commands Reference

```
run stlc KAN-4              → Run all 6 STLC phases for KAN-4
stlc KAN-4                  → Same as above
phase 1 KAN-4               → Requirement Analysis only
phase 2 KAN-4               → Test Plan only
phase 3 KAN-4               → Test Cases only
phase 4 KAN-4               → Environment Setup only
phase 5 KAN-4               → Execution Tracker only
phase 6 KAN-4               → Closure Report only
What is STLC?               → QA assistant answers (no pipeline triggered)
Help me improve test cases  → QA assistant answers (no pipeline triggered)
```

---

## Example Output Per Phase

### Phase 1 Output — Requirement Analysis (KAN-4: VIVO V7)

| Jira ID | Requirement | Testable | Ambiguity/Risk | Clarification Needed | Priority |
|---|---|---|---|---|---|
| KAN-4 | User can view VIVO V7 product page | Yes | None | — | High |
| KAN-4 | Product image loads correctly | Yes | Low — depends on CDN | Is there a fallback image? | Medium |
| KAN-4 | Specifications table displays all fields | Yes | Low | Which fields are mandatory? | High |
| KAN-4 | Add to Cart button is functional | Yes | High — payment flow | What happens if cart service is down? | Critical |
| KAN-4 | Page loads within 3 seconds | Partially | Medium — no SLA stated | What is the target load time SLA? | High |

---

### Phase 2 Output — Test Plan (KAN-4: VIVO V7)

| Jira ID | Plan Section | Content |
|---|---|---|
| KAN-4 | Objective | Validate that the VIVO V7 product page renders correctly, all data loads from backend, and the add-to-cart flow works end-to-end |
| KAN-4 | Scope (In) | Product page UI, image loading, specs table, add-to-cart, page load performance |
| KAN-4 | Scope (Out) | Payment gateway, delivery estimation, inventory management |
| KAN-4 | Test Approach | Risk-based: prioritise add-to-cart (high risk) and page load (observable by users) |
| KAN-4 | Test Types | Functional, UI, Performance (smoke), Negative |
| KAN-4 | Tools | Playwright, Postman, Lighthouse (perf), STLC Agent |
| KAN-4 | Entry Criteria | Feature deployed to QA env; test data (VIVO V7 product) seeded |
| KAN-4 | Exit Criteria | 100% TC executed; 0 P1/P2 open defects; pass rate >= 95% |
| KAN-4 | Risks | Cart service dependency (mitigate: mock in QA); Image CDN availability; Missing product data |
| KAN-4 | Estimated Effort | 9 test cases; ~4 hours execution; ~2 hours automation |

---

### Phase 3 Output — Test Cases (KAN-4: VIVO V7)

| TC ID | Type | Priority | Title |
|---|---|---|---|
| TC-001 | Functional | High | Product page loads successfully for VIVO V7 |
| TC-002 | Functional | High | All product specifications displayed correctly |
| TC-003 | Functional | Critical | Add to Cart button adds VIVO V7 to cart |
| TC-004 | Negative | High | Page shows error gracefully when product not found |
| TC-005 | Negative | Medium | Add to Cart fails gracefully when cart service is down |
| TC-006 | Edge Case | Medium | Product page loads with very long product description |
| TC-007 | Edge Case | Low | Page renders correctly with zero stock (out of stock) |
| TC-008 | Integration | High | Product image loads from CDN without broken link |
| TC-009 | UI | Medium | Product page is responsive on mobile viewport 375px |

---

### Phase 4 Output — Environment Setup

| Jira ID | Env Layer | Requirement | Configuration |
|---|---|---|---|
| KAN-4 | Browser | Chrome v125+ | Latest stable Chrome installed |
| KAN-4 | Browser | Mobile Safari | iOS 17 device or BrowserStack |
| KAN-4 | OS | Windows 11 | Primary test machine |
| KAN-4 | Backend API | Product API running | GET /api/products/vivo-v7 returns 200 |
| KAN-4 | Backend API | Cart API running | POST /api/cart returns 200 |
| KAN-4 | Database | VIVO V7 product seeded | Product ID, images, specs populated |
| KAN-4 | Auth | Test user account | user@test.com / Password123 |
| KAN-4 | CDN | Product images accessible | https://cdn.example.com/vivo-v7/ |
| KAN-4 | Network | QA environment accessible | https://qa.app.com/products/vivo-v7 |

---

### Phase 6 Output — Closure Report

| Jira ID | Metric | Value | Recommendation |
|---|---|---|---|
| KAN-4 | Total Test Cases Created | 9 | — |
| KAN-4 | Functional TCs | 3 | — |
| KAN-4 | Negative TCs | 2 | — |
| KAN-4 | Edge Case TCs | 2 | — |
| KAN-4 | Integration TCs | 1 | — |
| KAN-4 | UI TCs | 1 | — |
| KAN-4 | Pass Rate Target | 95% | Minimum to release |
| KAN-4 | Environment Status | Not Ready | Complete Phase 4 before execution |
| KAN-4 | Overall Recommendation | Conditional | Environment setup required before execution |
| KAN-4 | Go/No-Go | Conditional | No-Go until Env Setup (Phase 4) completed |
| KAN-4 | Sign-Off Status | Pending | Awaiting QA Lead review |

---

## Comparison: Existing Workflows vs STLC Agent

| Feature | W3 (existing) | STLC Agent (W5) |
|---|---|---|
| Phases covered | Phase 3 only (test cases) | All 6 STLC phases |
| Sheets tabs | 1 (test cases) | 6 (one per phase) |
| Requirement analysis | ✗ | ✓ |
| Test planning | ✗ | ✓ |
| Environment setup | ✗ | ✓ |
| Execution tracker | ✗ | ✓ Auto-populated |
| Closure report | ✗ | ✓ |
| Individual phase trigger | ✗ | ✓ |
| Bulk CSV processing | ✓ (W4) | ✓ |
| Memory across messages | ✓ | ✓ |
| Defect tracking integration | ✗ | ✓ (Defect ID column) |

---

## n8n Required Packages / Node Types

All node types used in this workflow are **built into n8n** — no custom nodes needed:

| Node Type | Package |
|---|---|
| `@n8n/n8n-nodes-langchain.chatTrigger` | Built-in |
| `@n8n/n8n-nodes-langchain.agent` | Built-in |
| `@n8n/n8n-nodes-langchain.lmChatGroq` | Built-in |
| `@n8n/n8n-nodes-langchain.memoryBufferWindow` | Built-in |
| `n8n-nodes-base.jiraTool` | Built-in |
| `n8n-nodes-base.googleSheetsTool` | Built-in |
| `n8n-nodes-base.slackTrigger` | Built-in |
| `n8n-nodes-base.microsoftTeamsTrigger` | Built-in |
| `n8n-nodes-base.scheduleTrigger` | Built-in |
| `n8n-nodes-base.formTrigger` | Built-in |
| `n8n-nodes-base.extractFromFile` | Built-in |
| `n8n-nodes-base.splitInBatches` | Built-in |

---

## Environment Variables

```
# .env for STLC Agent
JIRA_BASE_URL=https://bugzzzzz.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_TOKEN=your_jira_api_token

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

STLC_SHEETS_ID=your_google_sheet_id

N8N_BASE_URL=http://localhost:5678
```

---

*STLC Agent is the evolution of W3 (test case generation) into a full 6-phase testing lifecycle automation.*
*Built on the same stack: n8n · GROQ · Jira · Google Sheets · Slack · Teams*
