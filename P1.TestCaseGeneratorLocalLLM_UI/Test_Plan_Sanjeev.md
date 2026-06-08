# Test Plan — AI Test Case Generator (Local LLM UI)

**Document Version:** 1.0  
**Prepared By:** Sanjeev  
**Date:** 2026-06-08  
**Project:** P1 — TestCaseGeneratorLocalLLM_UI  
**Status:** Draft  

---

## Table of Contents

1. [Objective](#1-objective)
2. [Scope](#2-scope)
3. [Inclusions](#3-inclusions)
4. [Exclusions](#4-exclusions)
5. [Test Environments](#5-test-environments)
6. [Defect Reporting Procedure](#6-defect-reporting-procedure)
7. [Test Strategy](#7-test-strategy)
8. [Test Schedule](#8-test-schedule)
9. [Test Deliverables](#9-test-deliverables)
10. [Entry and Exit Criteria](#10-entry-and-exit-criteria)
11. [Test Cases](#11-test-cases)
12. [Tools](#12-tools)
13. [Risks and Mitigations](#13-risks-and-mitigations)
14. [Approvals](#14-approvals)

---

## 1. Objective

The objective of this Test Plan is to formally verify the **AI Test Case Generator (Local LLM UI)** — a desktop/web application that accepts feature descriptions or requirements as input and uses a locally-hosted Large Language Model (LLM) to automatically generate structured software test cases.

Testing will validate:
- Correctness and completeness of the UI workflows
- Accuracy and relevance of LLM-generated test cases
- Reliability of integration between the UI and the local LLM endpoint
- Error handling when the LLM service is unavailable or responds with unexpected output
- Performance within acceptable response-time thresholds
- Usability and intuitiveness of the interface

Testing phases will include **Manual Functional Testing**, **Integration Testing**, **Negative/Edge Case Testing**, and **Exploratory Testing**.

---

## 2. Scope

### In Scope

| # | Area | Description |
|---|------|-------------|
| 1 | UI Functional Testing | All interactive elements: input forms, submit button, output panel, copy/export controls |
| 2 | LLM Integration Testing | Verify the UI correctly sends prompts to the local LLM and receives/parses responses |
| 3 | Test Case Quality Validation | Manually assess generated test cases for relevance, structure, and coverage |
| 4 | Input Validation | Boundary values, empty inputs, very long text, special characters |
| 5 | Error Handling | LLM offline, timeout, malformed response, network errors |
| 6 | Output Formatting | Correct rendering of test case format (title, steps, expected result) |
| 7 | Export Functionality | Copy to clipboard, download as .txt/.csv/.xlsx (if applicable) |
| 8 | Settings / Configuration UI | LLM model selection, endpoint URL, temperature/parameter settings |
| 9 | Performance Testing | Measure response time from input submission to output render |
| 10 | Usability Testing | Ease of use, clarity of labels, responsiveness of layout |
| 11 | Regression Testing | After bug fixes, verify previously working functionality is intact |

### Out of Scope

- Training or fine-tuning of the LLM model
- Testing the LLM model itself (e.g., Ollama, LM Studio internals)
- Backend infrastructure or server-side deployment
- Automated test execution (unless explicitly added in a future sprint)
- Third-party integrations not part of the current feature set

---

## 3. Inclusions

### 3.1 Input Module

- User can type/paste a feature description or user story into the input field
- UI accepts multiline text input
- Character limit (if any) is enforced with clear feedback
- "Generate" / "Submit" button is clearly visible and accessible
- Input field can be cleared or reset

### 3.2 LLM Prompt Construction

- Application correctly constructs a structured prompt from user input
- Prompt is sent to the configured local LLM endpoint (e.g., `localhost:11434` for Ollama)
- System prompt / instruction tuning is applied consistently

### 3.3 Output Module

- Generated test cases are rendered in a readable, structured format
- Each test case includes: **Test Case ID**, **Title**, **Preconditions**, **Steps**, **Expected Result**, **Priority**
- Output renders correctly for both short and long LLM responses
- User can copy individual or all test cases

### 3.4 Export Module (if applicable)

- Export to `.txt`, `.csv`, `.xlsx`, or clipboard
- Exported file format matches the rendered output structure
- File naming convention is clear

### 3.5 Settings / Configuration

- User can configure the LLM model name
- User can set the API endpoint URL
- User can adjust generation parameters (temperature, max tokens)
- Settings are persisted between sessions

### 3.6 Error States

- Clear error message when LLM is unreachable
- Graceful handling of LLM timeout (no infinite spinner)
- Handling of empty or gibberish LLM response

---

## 4. Exclusions

- Model accuracy benchmarking against industry standards
- Load testing with 100+ concurrent users
- Cross-browser compatibility (if this is a desktop Electron/Tauri app)
- Accessibility (WCAG) compliance audit (can be added in a later sprint)
- Security penetration testing of the LLM endpoint

---

## 5. Test Environments

### 5.1 Hardware

| Component | Specification |
|-----------|---------------|
| OS | Windows 11 Home (primary), Ubuntu 22.04 (secondary if applicable) |
| RAM | 16 GB minimum (required for local LLM) |
| GPU | NVIDIA GPU preferred for LLM inference speed |
| Processor | Intel i7 / AMD Ryzen 7 or higher |

### 5.2 Software

| Component | Details |
|-----------|---------|
| Local LLM Runtime | Ollama / LM Studio (configured and running locally) |
| LLM Model | e.g., `llama3`, `mistral`, `codellama` (as configured) |
| Browser (if web UI) | Chrome 124+, Edge 124+, Firefox 125+ |
| Application Version | v1.0.0 (build under test) |
| IDE / Editor | VS Code (for log inspection if needed) |

### 5.3 Environment Matrix

| Environment | Purpose |
|-------------|---------|
| DEV (localhost) | Primary testing environment |
| QA | Regression and integration testing |

### 5.4 Test Team

| Name | Role |
|------|------|
| Sanjeev | QA Lead / Test Engineer |

---

## 6. Defect Reporting Procedure

### 6.1 Defect Identification

A defect is logged when the application behavior deviates from:
- Requirements documented in the PRD
- Expected behavior defined in test cases
- General usability standards

### 6.2 Defect Logging Steps

1. Reproduce the defect at least **2 times** to confirm it is not intermittent
2. Capture **screenshots or screen recordings**
3. Log defect in the tracking tool with the following fields:

| Field | Description |
|-------|-------------|
| **Title** | Short, descriptive summary of the defect |
| **Environment** | OS, browser/app version, LLM model used |
| **Steps to Reproduce** | Numbered, clear steps |
| **Actual Result** | What the app did |
| **Expected Result** | What the app should have done |
| **Severity** | Critical / High / Medium / Low |
| **Priority** | P1 / P2 / P3 / P4 |
| **Attachments** | Screenshots, logs, video |

### 6.3 Defect Severity Levels

| Severity | Definition | Example |
|----------|-----------|---------|
| **Critical** | App crash, data loss, core feature broken | App freezes on generate click |
| **High** | Major feature does not work | LLM response not displayed |
| **Medium** | Feature works but with incorrect behavior | Test case format missing fields |
| **Low** | Minor UI/cosmetic issue | Button misaligned by 2px |

### 6.4 Defect Priorities

| Priority | SLA |
|----------|-----|
| P1 (Critical) | Fix within same day |
| P2 (High) | Fix within 2 business days |
| P3 (Medium) | Fix within current sprint |
| P4 (Low) | Fix in next sprint |

### 6.5 Defect Tracking Tool

**Tool:** GitHub Issues / JIRA (as configured for this project)

---

## 7. Test Strategy

### 7.1 Testing Approach

Testing will follow a **risk-based approach**, prioritizing the core LLM integration and test case generation output first, followed by UI and edge cases.

**Test Design Techniques Applied:**
- Equivalence Partitioning — valid vs. invalid input categories
- Boundary Value Analysis — min/max character input limits
- Decision Table Testing — settings combinations (model × temperature × token limit)
- State Transition Testing — UI states: idle → loading → success/error
- Error Guessing — common failure scenarios (LLM down, empty input, timeout)
- Exploratory Testing — session-based exploration of unscripted flows

### 7.2 Testing Phases

| Phase | Description |
|-------|-------------|
| **Smoke Testing** | Verify app launches, LLM connects, basic generation works |
| **Functional Testing** | Execute all documented test cases by module |
| **Integration Testing** | Verify full data flow: UI input → prompt → LLM → output → display |
| **Negative Testing** | Invalid inputs, LLM offline, malformed responses |
| **Exploratory Testing** | Unscripted discovery of edge cases and usability issues |
| **Regression Testing** | After each bug fix, re-run related test cases |

### 7.3 Shift-Left Testing

Test case design begins **during requirements review**, not after development, to catch ambiguities early.

---

## 8. Test Schedule

| Task | Duration | Target Date |
|------|----------|------------|
| Test Plan Creation | 1 day | 2026-06-08 |
| Test Case Design | 2 days | 2026-06-10 |
| Environment Setup & Smoke Test | 1 day | 2026-06-11 |
| Functional Test Execution | 3 days | 2026-06-12 to 2026-06-14 |
| Negative / Edge Case Testing | 1 day | 2026-06-15 |
| Exploratory Testing | 1 day | 2026-06-16 |
| Defect Reporting & Retesting | 2 days | 2026-06-17 to 2026-06-18 |
| Regression Testing | 1 day | 2026-06-19 |
| Test Summary Report | 1 day | 2026-06-20 |

**Total Estimated Duration:** 2 Sprints (2 weeks)

---

## 9. Test Deliverables

| Deliverable | Description | Target Date |
|-------------|-------------|------------|
| Test Plan | This document | 2026-06-08 |
| Test Cases | Excel/sheet with all test cases by module | 2026-06-10 |
| Defect Reports | JIRA/GitHub Issues with full details | Rolling |
| Daily Status Updates | Progress on test execution and open defects | Daily |
| Test Summary Report | Final pass/fail counts, defect stats, coverage | 2026-06-20 |

---

## 10. Entry and Exit Criteria

### 10.1 Test Planning

**Entry Criteria:**
- PRD / requirements document reviewed and understood
- Feature scope defined and agreed upon

**Exit Criteria:**
- Test Plan reviewed and signed off
- All test cases designed and reviewed

### 10.2 Test Execution

**Entry Criteria:**
- Application build deployed in test environment
- Local LLM service running and reachable
- Test cases signed off
- Test data prepared

**Exit Criteria:**
- All planned test cases executed (100%)
- All P1/P2 defects fixed and verified
- P3/P4 defects documented and accepted
- Test pass rate ≥ 90%

### 10.3 Test Closure

**Entry Criteria:**
- Test execution complete
- All critical defects resolved

**Exit Criteria:**
- Test Summary Report delivered
- Stakeholder sign-off received

---

## 11. Test Cases

### Module 1: Application Launch & Setup

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-001 | App launches successfully | App installed, LLM running | 1. Open application | App opens without errors, UI loads fully | P1 |
| TC-002 | LLM connection status shown | App open, LLM running | 1. Open app 2. Check connection indicator | Status shows "Connected" or equivalent | P1 |
| TC-003 | App launches with LLM offline | LLM service stopped | 1. Stop LLM 2. Open app | App shows clear "LLM Offline" or "Cannot connect" message, does not crash | P1 |
| TC-004 | Settings page opens | App open | 1. Click Settings icon | Settings panel/page opens with all config fields | P2 |
| TC-005 | Save LLM endpoint URL | Settings open | 1. Enter custom URL 2. Save | URL saved, persists on app restart | P2 |
| TC-006 | Change LLM model | Settings open, multiple models available | 1. Select different model 2. Save | Model change reflected in subsequent generations | P2 |

---

### Module 2: Input Module

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-007 | Valid feature description generates test cases | App open, LLM connected | 1. Enter: "User can log in with email and password" 2. Click Generate | Test cases generated and displayed | P1 |
| TC-008 | Empty input rejected | App open | 1. Leave input blank 2. Click Generate | Error message "Please enter a feature description" shown; no LLM call made | P1 |
| TC-009 | Input with only whitespace rejected | App open | 1. Enter spaces/tabs only 2. Click Generate | Treated as empty; validation error shown | P2 |
| TC-010 | Long input accepted (>1000 chars) | App open | 1. Paste 2000-character requirement 2. Click Generate | Input accepted; test cases generated successfully | P2 |
| TC-011 | Special characters in input | App open | 1. Enter text with `<>{}[]"'&` 2. Click Generate | Input sanitized; generation completes without error | P2 |
| TC-012 | Clear / Reset input field | App open, text entered | 1. Enter text 2. Click Clear/Reset | Input field cleared; output panel cleared | P2 |
| TC-013 | Input persists after failed generation | LLM offline | 1. Enter text 2. Click Generate 3. Error shown | User's input text is not lost after the error | P2 |
| TC-014 | Multiline input accepted | App open | 1. Enter text with multiple line breaks 2. Generate | Input accepted; generation completes | P3 |

---

### Module 3: LLM Integration

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-015 | Prompt sent to LLM on Generate click | App open, LLM running | 1. Enter feature description 2. Click Generate 3. Monitor LLM logs | Correct prompt constructed and sent to LLM endpoint | P1 |
| TC-016 | Loading indicator shown during generation | App open, LLM running | 1. Enter input 2. Click Generate | Loading spinner/indicator shown while waiting for response | P2 |
| TC-017 | LLM response parsed and displayed | App open, LLM running | 1. Generate test cases | Response rendered correctly in output panel | P1 |
| TC-018 | LLM timeout handled gracefully | App open, LLM set to slow/unresponsive | 1. Generate with slow LLM | After timeout threshold, error shown: "Request timed out. Try again." | P1 |
| TC-019 | LLM returns empty response | App open, LLM returns empty string | 1. Generate | Message shown: "No test cases generated. Try rephrasing your input." | P2 |
| TC-020 | LLM returns malformed/non-structured response | App open | 1. Generate | App handles gracefully; shows raw response or error; does not crash | P2 |
| TC-021 | Consecutive generations work correctly | App open, LLM running | 1. Generate once 2. Clear/edit input 3. Generate again | Second generation independent of first; no stale output | P1 |

---

### Module 4: Output Module

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-022 | Test cases rendered in structured format | Generation complete | 1. View output panel | Each test case shows: ID, Title, Steps, Expected Result | P1 |
| TC-023 | Multiple test cases displayed | Generation returns multiple TCs | 1. Enter broad feature 2. Generate | All generated test cases displayed; numbered/separated | P1 |
| TC-024 | Single test case displayed | Generation returns 1 TC | 1. Enter narrow input 2. Generate | Single TC rendered without formatting errors | P2 |
| TC-025 | Long output is scrollable | Generation returns many test cases | 1. Generate for large feature | Output area is scrollable; no overflow beyond viewport | P2 |
| TC-026 | Output panel empty before first generation | Fresh app launch | 1. Open app | Output panel shows placeholder text or is empty | P3 |
| TC-027 | Previous output replaced on new generation | Second generation | 1. Generate once 2. Generate again | Old output replaced; no duplicate stacking | P1 |

---

### Module 5: Copy / Export Module

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-028 | Copy All copies full output to clipboard | Generation complete | 1. Click "Copy All" | Clipboard contains all test cases in structured text | P2 |
| TC-029 | Copy individual test case | Generation complete, multiple TCs | 1. Click copy on one TC | Only that TC copied to clipboard | P3 |
| TC-030 | Export to .txt works | Generation complete | 1. Click Export > .txt | File downloaded with correct name, contains all test cases | P2 |
| TC-031 | Export to .csv works | Generation complete | 1. Click Export > .csv | CSV file with headers (ID, Title, Steps, Expected) downloaded | P2 |
| TC-032 | Export filename is meaningful | Export triggered | 1. Export | Filename includes date or feature keyword (not generic like "file.txt") | P3 |

---

### Module 6: Settings / Configuration

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-033 | Default model is set | Fresh install | 1. Open settings | A default LLM model is pre-selected | P2 |
| TC-034 | Temperature setting changes output style | Settings accessible | 1. Set temperature to 0 2. Generate 3. Set to 0.9 4. Generate same input | Outputs differ in creativity/determinism | P3 |
| TC-035 | Invalid endpoint URL shows error | Settings open | 1. Enter invalid URL (e.g., `not-a-url`) 2. Save 3. Generate | Clear validation error on save or connection error on generate | P2 |
| TC-036 | Settings persist after app restart | Settings saved | 1. Change and save settings 2. Restart app 3. Open settings | Previously saved values are loaded | P2 |

---

### Module 7: Negative / Edge Cases

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-037 | Generate clicked multiple times rapidly | App open, LLM connected | 1. Enter input 2. Click Generate 5 times fast | Only one generation executes; no duplicate requests | P1 |
| TC-038 | Input with only numbers | App open | 1. Enter "12345" 2. Generate | Either generates something or shows helpful message; does not crash | P3 |
| TC-039 | Input in non-English language | App open | 1. Enter feature in Spanish/French/etc. 2. Generate | Generation completes; output may be in same language; no crash | P3 |
| TC-040 | LLM goes offline mid-generation | Generation in progress | 1. Start generation 2. Stop LLM mid-way | Error shown gracefully; no infinite loader | P1 |
| TC-041 | Very short input (1-5 words) | App open | 1. Enter "Login" 2. Generate | Either generates basic TCs or prompts for more detail | P3 |
| TC-042 | SQL-injection-like input | App open | 1. Enter `'; DROP TABLE tests;--` 2. Generate | Input treated as plain text; passed to LLM safely; no error | P2 |

---

### Module 8: Performance

| TC ID | Test Case Title | Precondition | Steps | Expected Result | Priority |
|-------|----------------|--------------|-------|----------------|---------|
| TC-043 | Generation completes within 30 seconds | App open, LLM running on local hardware | 1. Enter standard feature description 2. Generate 3. Time the response | Response received and rendered within 30 seconds | P1 |
| TC-044 | UI remains responsive during generation | Generation in progress | 1. Click Generate 2. Interact with UI during loading | UI does not freeze; can scroll, navigate settings | P2 |
| TC-045 | App memory usage is stable after 10 generations | App open | 1. Generate 10 times in succession | Memory usage does not continuously increase (no memory leak) | P2 |

---

## 12. Tools

| Tool | Purpose |
|------|---------|
| **Ollama / LM Studio** | Local LLM runtime for generating responses |
| **GitHub Issues / JIRA** | Defect tracking and test case management |
| **Excel / Google Sheets** | Test case documentation |
| **Postman** | Validate LLM API endpoint directly (integration debugging) |
| **Browser DevTools** | Monitor network requests, console errors (if web UI) |
| **OBS / ShareX** | Screen recording for bug evidence |
| **Markdown / Word** | Test plan and report documentation |

---

## 13. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Local LLM is slow on test machine | High | Medium | Test on machine with adequate RAM/GPU; note performance as environmental variable |
| LLM model produces inconsistent output | High | High | Use fixed temperature=0 for deterministic functional tests; evaluate quality separately |
| LLM goes offline during testing | Medium | High | Use mock/stub LLM endpoint for offline testing of UI error handling |
| App build not stable for testing | Medium | High | Conduct smoke test before full execution; halt if >30% of smoke tests fail |
| Unclear requirements for generated output format | Medium | High | Agree on expected test case format with developer before execution |
| Test machine lacks sufficient resources | Low | High | Reserve machine with 16GB+ RAM; document hardware specs in test report |
| Scope creep adding new features mid-sprint | Low | Medium | Freeze scope at sprint start; new features queued for next sprint |

---

## 14. Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | Sanjeev | | 2026-06-08 |
| Developer | | | |
| Product Owner | | | |

---

*Test Plan will be reviewed and updated at the start of each sprint to reflect any scope or requirement changes.*
