# 🧪 Test Strategy Buddy
### Your Complete Guide to Understanding, Writing, and Executing a World-Class Test Strategy

> **Who is this for?** QA Engineers, SDETs, Test Leads, and Developers who want to deeply
> understand testing from first principles — and connect it to real-world tools like this
> BLAST Framework app (Jira + GROQ AI Test Plan Generator).

---

## Table of Contents

1. [What Is a Test Strategy?](#1-what-is-a-test-strategy)
2. [Test Strategy vs Test Plan vs Test Case](#2-test-strategy-vs-test-plan-vs-test-case)
3. [The 7 Core Components of a Test Strategy](#3-the-7-core-components-of-a-test-strategy)
4. [The 4 Levels of Testing](#4-the-4-levels-of-testing)
5. [Types of Testing — The Full Taxonomy](#5-types-of-testing--the-full-taxonomy)
6. [Test Design Techniques](#6-test-design-techniques)
7. [Risk-Based Testing (RBT)](#7-risk-based-testing-rbt)
8. [Test Environments and Data Strategy](#8-test-environments-and-data-strategy)
9. [Defect Management Lifecycle](#9-defect-management-lifecycle)
10. [Metrics and KPIs That Actually Matter](#10-metrics-and-kpis-that-actually-matter)
11. [How the BLAST Framework App Fits In](#11-how-the-blast-framework-app-fits-in)
12. [A Complete Test Strategy Template](#12-a-complete-test-strategy-template)
13. [Real-World Example — KAN-4 (VIVO V7)](#13-real-world-example--kan-4-vivo-v7)
14. [Common Mistakes and How to Avoid Them](#14-common-mistakes-and-how-to-avoid-them)
15. [Quick Reference Cheat Sheet](#15-quick-reference-cheat-sheet)

---

## 1. What Is a Test Strategy?

A **Test Strategy** is a high-level document that defines the **approach, principles, and
direction** for testing across an entire project or product.

Think of it this way:

```
Test Strategy  = The "WHY" and "HOW" at a 10,000-foot view
Test Plan      = The "WHAT" and "WHEN" for a specific release or sprint
Test Case      = The step-by-step "DO THIS" for one specific scenario
```

### A Simple Analogy

> Imagine you are building a house.
>
> - **Test Strategy** = "We will inspect every floor, every wall, every pipe before signing off.
>   We use licensed inspectors. We follow building code XYZ."
> - **Test Plan** = "For the ground floor, we will inspect by Friday. Inspector: John. Tools: Level,
>   thermal camera."
> - **Test Case** = "Step 1: Press the light switch. Step 2: Observe if the light turns on.
>   Expected: Light turns on within 1 second."

### Why Does a Test Strategy Matter?

Without a strategy, your testing becomes **random, inconsistent, and incomplete**. You miss
critical areas, duplicate effort, and cannot explain to stakeholders why something was or was
not tested.

A good test strategy:
- Gives the **entire team alignment** on quality expectations
- Enables **risk-based prioritization** (not everything needs to be tested equally)
- Creates **repeatability** — a new team member can pick it up and follow it
- Provides **audit trail** — you can prove what was tested and why
- Reduces **waste** — you test the right things, not everything

---

## 2. Test Strategy vs Test Plan vs Test Case

This is the most common source of confusion in QA. Here is a clear breakdown:

| Dimension | Test Strategy | Test Plan | Test Case |
|---|---|---|---|
| **Level** | Project / Product | Release / Sprint / Module | Individual Scenario |
| **Written by** | QA Lead / Test Manager | QA Lead / Senior Tester | QA Engineer / Tester |
| **When created** | Start of project | Start of each release | Before each sprint |
| **Scope** | Entire system | One specific scope | One specific behaviour |
| **Changes often?** | Rarely | Per release | Per story/bug |
| **Audience** | Stakeholders, Dev Lead, QA Team | QA Team, Dev Team | Tester executing the test |
| **Key question answered** | How will we test? | What will we test? | How do I test THIS thing? |
| **Contains** | Approach, tools, levels, risk policy | Scope, timelines, resources, exit criteria | Steps, data, expected results |

### Visual Hierarchy

```
┌─────────────────────────────────────────────┐
│              TEST STRATEGY                  │  ← One per project
│   "We test at unit, integration, E2E level" │
│   "We use automation for regression"        │
│   "Risk-based approach for prioritization"  │
├─────────────────────────────────────────────┤
│   TEST PLAN (Sprint 1)  │  TEST PLAN (v2.0) │  ← One per release
│   Scope: Login module   │  Scope: Payment   │
│   Duration: 5 days      │  Duration: 3 days │
├──────────────┬──────────┴───────────────────┤
│  TC-001      │  TC-002  │  TC-003  │ TC-004 │  ← Many per plan
│  Valid Login │ Invalid  │ Forgot   │ Logout │
└──────────────┴──────────┴──────────┴────────┘
```

---

## 3. The 7 Core Components of a Test Strategy

A complete test strategy document must address these 7 areas. Miss any one and your
strategy has a gap.

---

### Component 1: Scope and Objectives

**What it is:** Clearly define what IS and what IS NOT going to be tested.

**Why it matters:** Teams waste enormous time arguing over what is "in scope." This section
ends that debate.

**What to include:**
- Features and modules covered
- Features explicitly OUT of scope (and why)
- Testing objectives (e.g., "Ensure all login scenarios work correctly", "Validate API
  response times under 200ms")
- Success criteria

**Example:**

```
IN SCOPE:
- Login functionality (web and mobile)
- User registration
- Password reset flow
- API endpoints: /auth/login, /auth/logout, /auth/register

OUT OF SCOPE:
- Third-party payment gateway (handled by vendor SLA)
- Legacy browser support (IE11 — EOL)
- Performance testing for > 10,000 concurrent users (Phase 2)
```

---

### Component 2: Test Approach

**What it is:** How you will test — the methodology, philosophy, and overall strategy.

**Common approaches:**
- **Risk-Based Testing (RBT)** — focus testing effort on highest-risk areas first
- **Exploratory Testing** — testers actively explore without scripts to find unexpected bugs
- **Specification-Based Testing** — derive tests directly from requirements/acceptance criteria
- **Model-Based Testing** — use state machines or flow diagrams to generate tests
- **Shift-Left Testing** — test earlier in the development cycle (devs write tests)

**Example:**

```
Approach: Risk-Based + Specification-Based
- High-risk areas (auth, payments) → exhaustive testing with automation
- Medium-risk areas (profile management) → scripted testing + exploratory
- Low-risk areas (static pages, help text) → smoke test only
- All new features: derive test cases directly from acceptance criteria in Jira
```

---

### Component 3: Test Levels

Define which types of tests will be executed and by whom.

```
┌────────────────────────────────────────────────────────┐
│                     END-TO-END (E2E)                   │
│          "Does the whole user journey work?"           │
│          Owner: QA Team | Tool: Playwright, Cypress    │
├────────────────────────────────────────────────────────┤
│                   INTEGRATION TESTING                  │
│        "Do different modules work together?"           │
│        Owner: QA + Dev | Tool: Postman, Jest, JUnit    │
├────────────────────────────────────────────────────────┤
│                     UNIT TESTING                       │
│         "Does this single function work correctly?"    │
│         Owner: Developers | Tool: Jest, PyTest, JUnit  │
└────────────────────────────────────────────────────────┘
```

---

### Component 4: Test Types

Which categories of testing apply to this project.

| Test Type | Purpose | When |
|---|---|---|
| Functional | Does the feature work as specified? | Every sprint |
| Regression | Did new changes break old features? | Every release |
| Smoke | Do the critical paths work after deployment? | After every deploy |
| Sanity | Is a specific fix working? | After a hotfix |
| Performance | Does it handle load? | Before major releases |
| Security | Is it protected from attacks? | Quarterly / before release |
| Accessibility | Can people with disabilities use it? | Feature completion |
| Usability | Is it intuitive to use? | UX sign-off |
| Compatibility | Does it work on all required platforms? | Release gate |

---

### Component 5: Test Environment and Tools

**What environments exist:**

```
Local Dev → QA/Staging → Pre-Prod (UAT) → Production
   ↑                          ↑
   Developers test here       Business users test here (UAT)
```

**Tools to specify:**
- Test management: Jira, TestRail, Zephyr, qTest
- Automation: Playwright, Cypress, Selenium, Appium
- API testing: Postman, REST Assured, Karate
- Performance: JMeter, k6, Gatling
- CI/CD: GitHub Actions, Jenkins, CircleCI
- Defect tracking: Jira, GitHub Issues, Azure DevOps

---

### Component 6: Entry and Exit Criteria

**Entry Criteria** — conditions that must be true BEFORE testing begins:

```
✓ Feature code is merged to QA branch
✓ Unit tests pass (min 80% coverage)
✓ Build deployed to QA environment
✓ Test data is available
✓ Acceptance criteria are documented in Jira
```

**Exit Criteria** — conditions that must be true BEFORE releasing:

```
✓ 100% of critical test cases executed
✓ 0 open P1/P2 (Critical/High) defects
✓ ≤ 5 open P3 (Medium) defects with accepted risk
✓ Regression suite passed
✓ Test summary report signed off by QA Lead
```

---

### Component 7: Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Test environment unavailable | Medium | High | Maintain local Docker setup |
| Incomplete requirements | High | High | Test cases written with PO review |
| Automation flakiness | Medium | Medium | Quarantine flaky tests, fix within 1 sprint |
| Resource shortage | Low | High | Cross-train 2 team members |
| Late defect discovery | Medium | Critical | Shift-left: unit + integration tests in CI |

---

## 4. The 4 Levels of Testing

Testing happens at 4 distinct levels. Each level catches different types of defects.

### Level 1: Unit Testing

- **Who:** Developers
- **What:** Tests a single function, method, or class in isolation
- **Tools:** Jest (JS), PyTest (Python), JUnit (Java), NUnit (.NET)
- **When:** Written alongside the code (TDD) or immediately after
- **Coverage target:** 70–90% code coverage
- **Speed:** Very fast (milliseconds per test)
- **Feedback:** Immediate — runs in CI on every commit

**Example:**
```javascript
// Testing a single function
test('calculateDiscount returns 10% for premium users', () => {
  expect(calculateDiscount('premium', 100)).toBe(90);
});
```

---

### Level 2: Integration Testing

- **Who:** Developers + QA
- **What:** Tests how multiple modules/services work together
- **Tools:** Postman, REST Assured, Supertest, TestContainers
- **When:** After unit tests pass, before deployment to staging
- **What it catches:** Interface mismatches, data format issues, API contract violations

**Example:**
```
Test: User registration → Login → Profile fetch
Verify: Token returned from login is accepted by profile API
```

---

### Level 3: System Testing (End-to-End)

- **Who:** QA Team
- **What:** Tests the complete application flow from the user's perspective
- **Tools:** Playwright, Cypress, Selenium WebDriver
- **When:** On staging/pre-prod environment
- **What it catches:** Workflow breaks, UI defects, cross-module issues

**Example (Playwright):**
```javascript
test('User can complete checkout', async ({ page }) => {
  await page.goto('https://shop.example.com');
  await page.click('[data-testid="product-card"]');
  await page.click('[data-testid="add-to-cart"]');
  await page.click('[data-testid="checkout"]');
  await expect(page).toHaveURL(/.*confirmation/);
});
```

---

### Level 4: Acceptance Testing (UAT)

- **Who:** Business stakeholders, Product Owners, End Users
- **What:** Validates the system meets business requirements
- **When:** After system testing, before production release
- **What it catches:** Business logic gaps, requirement misunderstandings

```
UAT Scenario: "As a premium customer, I should see my loyalty points
              after every purchase."
Acceptance: Points displayed within 30 seconds of purchase confirmation.
```

---

## 5. Types of Testing — The Full Taxonomy

### 5.1 Functional Testing

Tests **what the system does** — the features and behaviour.

```
├── Smoke Testing     → Quick validation: "Is the app alive?"
├── Sanity Testing    → Narrow validation: "Is this specific fix working?"
├── Regression Testing→ Safety net: "Did we break anything?"
├── Exploratory Testing→ Creative discovery: "What can I break?"
└── User Acceptance   → Business validation: "Does this meet our needs?"
```

**Smoke vs Sanity — the most confused pair:**

| | Smoke | Sanity |
|---|---|---|
| **Scope** | Broad — entire application | Narrow — one specific area |
| **When** | After every build/deploy | After a fix/patch |
| **Goal** | "Is it worth testing further?" | "Is this specific change correct?" |
| **Done by** | QA Team | QA or Developer |
| **Duration** | 15-30 minutes | 5-15 minutes |

---

### 5.2 Non-Functional Testing

Tests **how the system performs** — quality attributes beyond features.

#### Performance Testing

```
Load Testing        → Normal expected load (100 users)
Stress Testing      → Beyond capacity (500 users) to find breaking point
Spike Testing       → Sudden burst (10 → 500 users instantly)
Endurance/Soak      → Sustained load over long period (24 hours)
Volume Testing      → Large amounts of data (1 million records)
```

**Key Metrics:**
- Response Time (P50, P90, P95, P99 percentiles)
- Throughput (requests per second)
- Error Rate (< 0.1% is typical SLA)
- Resource Utilisation (CPU, Memory, Network)

---

#### Security Testing

| Type | What it tests |
|---|---|
| OWASP Top 10 | SQL injection, XSS, CSRF, etc. |
| Penetration Testing | Simulated attack to find vulnerabilities |
| Authentication Testing | Login bypass, session hijacking |
| Authorization Testing | Privilege escalation, IDOR |
| Data Encryption | Are passwords hashed? Is data in transit encrypted? |
| API Security | Are endpoints authenticated? Rate limited? |

**OWASP Top 10 (2021):**
1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, NoSQL, Command)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Identification & Authentication Failures
8. Software & Data Integrity Failures
9. Security Logging & Monitoring Failures
10. Server-Side Request Forgery (SSRF)

---

#### Accessibility Testing (A11y)

```
WCAG 2.1 Levels:
  A   → Minimum (must-have for legal compliance)
  AA  → Standard (most organisations target this)
  AAA → Enhanced (optional, very strict)

Tools: Axe, WAVE, Lighthouse, Screen readers (NVDA, JAWS)

Key checks:
  ✓ Alt text on images
  ✓ Keyboard navigation works (Tab, Enter, Escape)
  ✓ Colour contrast ratio ≥ 4.5:1 (AA standard)
  ✓ Form labels properly associated
  ✓ ARIA roles correct
```

---

### 5.3 API Testing

Critical for modern microservices architectures.

```
What to test in every API:

1. Happy Path
   → Correct request → Correct response (200 OK, correct body)

2. Authentication
   → No token     → 401 Unauthorised
   → Invalid token → 401 Unauthorised
   → Expired token → 401 Unauthorised

3. Authorisation
   → User A accessing User B's data → 403 Forbidden
   → Standard user accessing admin endpoint → 403 Forbidden

4. Input Validation
   → Missing required field → 400 Bad Request
   → Invalid data type     → 400 Bad Request
   → Data too long         → 400 Bad Request

5. Business Logic
   → Logic-specific scenarios from requirements

6. Edge Cases
   → Boundary values (max/min)
   → Empty collections
   → Null values
   → Special characters in strings

7. Rate Limiting
   → Exceed rate limit → 429 Too Many Requests
```

---

## 6. Test Design Techniques

These are proven methods to **derive effective test cases** from requirements.

### 6.1 Equivalence Partitioning (EP)

Divide input data into groups (partitions) where all values in a group should behave
the same. Test one value from each partition.

**Example — Age field (18–65 valid):**
```
Partition 1: Below valid range  → e.g., 17   (invalid)
Partition 2: Valid range        → e.g., 30   (valid)
Partition 3: Above valid range  → e.g., 66   (invalid)

Test cases: 3 (one per partition) instead of testing every age
```

---

### 6.2 Boundary Value Analysis (BVA)

Test the values AT and just BEYOND the boundaries of valid ranges. Most defects live
at boundary conditions.

**Example — same Age field (18–65):**
```
Test: 17  → invalid (just below lower boundary)
Test: 18  → valid   (lower boundary)
Test: 19  → valid   (just above lower boundary)
Test: 64  → valid   (just below upper boundary)
Test: 65  → valid   (upper boundary)
Test: 66  → invalid (just above upper boundary)
```

---

### 6.3 Decision Table Testing

Used when multiple conditions combine to produce different outcomes.

**Example — Login with 2FA:**

| Username Valid | Password Valid | 2FA Correct | Result |
|---|---|---|---|
| ✓ | ✓ | ✓ | Login success |
| ✓ | ✓ | ✗ | 2FA failed |
| ✓ | ✗ | - | Password incorrect |
| ✗ | - | - | User not found |

Each row = one test case. Decision tables ensure you cover all combinations.

---

### 6.4 State Transition Testing

Used when the system has distinct states and transitions between them.

**Example — Order lifecycle:**
```
PENDING → CONFIRMED → SHIPPED → DELIVERED → CLOSED
          ↓                      ↓
        CANCELLED              RETURNED

Test: Valid transitions  → should work
Test: Invalid transitions → e.g., SHIPPED → PENDING should be rejected
```

---

### 6.5 Pairwise (All-Pairs) Testing

When you have many input variables, pairwise testing ensures every pair of values is
tested at least once — reduces the number of test cases dramatically while maintaining
good coverage.

**Without pairwise:** 3 variables × 3 values each = 27 test cases
**With pairwise:** 9 test cases covering all pairs

Tool recommendation: **PICT** (Microsoft Pairwise Independent Combinatorial Testing)

---

### 6.6 Exploratory Testing

Simultaneous test design and execution. The tester uses domain knowledge and creativity
to explore the system without pre-written scripts.

**Session-Based Exploratory Testing (SBET):**
```
Charter: "Explore the login functionality focusing on security"
Duration: 90 minutes
Tester: [Your name]
Focus areas:
  - What happens with special characters in password?
  - Can you bypass login by manipulating URL?
  - What happens with very long input values?
  - Does session expire correctly?
Notes: [Record findings during the session]
```

---

## 7. Risk-Based Testing (RBT)

When you have limited time, you cannot test everything equally. Risk-Based Testing
prioritises test effort based on the **likelihood** and **impact** of failure.

### The Risk Matrix

```
        │   HIGH IMPACT   │   LOW IMPACT
────────┼─────────────────┼─────────────────
HIGH    │   CRITICAL      │   HIGH RISK
LIKELI- │   (test first,  │   (test thoroughly
HOOD    │   automate)     │   when time allows)
────────┼─────────────────┼─────────────────
LOW     │   HIGH RISK     │   LOW RISK
LIKELI- │   (test         │   (smoke test
HOOD    │   thoroughly)   │   only)
```

### How to Apply RBT in Practice

**Step 1: List all features**
```
1. User Authentication
2. Payment Processing
3. Product Search
4. User Profile Update
5. Help Documentation
6. Footer Links
```

**Step 2: Rate each by risk**

| Feature | Failure Likelihood | Failure Impact | Risk Score | Priority |
|---|---|---|---|---|
| Payment Processing | Medium | Critical | HIGH | 1 |
| User Authentication | Medium | High | HIGH | 2 |
| Product Search | High | Medium | HIGH | 3 |
| User Profile Update | Low | Medium | MEDIUM | 4 |
| Help Documentation | Low | Low | LOW | 5 |
| Footer Links | Low | Low | LOW | 6 |

**Step 3: Allocate testing time proportionally**
```
HIGH risk features  → 60% of testing time
MEDIUM risk         → 30% of testing time
LOW risk            → 10% of testing time
```

---

## 8. Test Environments and Data Strategy

### 8.1 Environment Strategy

```
LOCAL           DEV              QA/STAGING         PROD
(Dev machine)   (Shared dev)     (Mirror of prod)   (Live users)

Developer       Developer        QA Team tests       Smoke tests
writes and      integration      here before         post-deployment
tests locally   testing          release
```

**Environment checklist:**
- [ ] Are all environments in sync with production configuration?
- [ ] Are environment variables properly set (no prod creds in QA)?
- [ ] Is there a process to refresh QA with prod-like data?
- [ ] Are external services mocked in non-prod environments?

---

### 8.2 Test Data Strategy

Test data is often the most overlooked part of testing. Bad test data = flaky tests.

**Categories of test data:**

| Category | Example | How to manage |
|---|---|---|
| Static reference data | Country list, currency codes | Version-controlled SQL scripts |
| User accounts | Admin, standard, premium, suspended | Seeded in CI database |
| Business scenarios | Orders in various states | Factory methods in test code |
| Edge case data | Long strings, special chars, nulls | Test data builder patterns |
| Production-like data | Anonymised prod snapshot | Data masking pipeline |

**Golden rules:**
1. **Never use real production data** in QA — GDPR/privacy risk
2. Test data should be **repeatable** — same data, same results
3. Tests should **clean up after themselves** — don't pollute shared data
4. Use **data factories/builders** in automation code

---

## 9. Defect Management Lifecycle

Understanding the full lifecycle of a defect ensures nothing falls through the cracks.

### The Defect Lifecycle

```
New → Assigned → In Progress → Fixed → Ready for Retest
                                             ↓
                              Retest Pass → Closed
                                             ↓
                              Retest Fail → Reopened → (back to In Progress)
                                             ↓
                              Won't Fix / Cannot Reproduce / Duplicate
```

### Defect Severity vs Priority — a critical distinction

| | Severity | Priority |
|---|---|---|
| **Definition** | Technical impact on system | Business urgency to fix |
| **Decided by** | QA / Developer | Product Owner / Business |
| **Scale** | Critical > High > Medium > Low | P1 > P2 > P3 > P4 |

**The confusing combinations:**

```
HIGH Severity + HIGH Priority: Crash on checkout page        → Fix immediately
HIGH Severity + LOW Priority:  Crash on archived admin page  → Fix in next sprint
LOW Severity + HIGH Priority:  CEO's name spelled wrong      → Fix today (embarrassing)
LOW Severity + LOW Priority:   Minor UI spacing issue        → Backlog
```

### A Good Defect Report Contains:

```
Title:        [Module] Brief description of the problem
ID:           BUG-1234
Severity:     High
Priority:     P2
Environment:  QA | Chrome 125 | Windows 11
Reporter:     Sanjeev Kumar Thakur
Date:         2026-06-10

Steps to Reproduce:
1. Navigate to https://app.example.com/login
2. Enter valid email: user@test.com
3. Enter valid password: Password123
4. Click "Log In"

Expected Result:
User is redirected to the dashboard (/home)

Actual Result:
User is redirected to a blank white page (/undefined)

Attachments:
- screenshot-bug-1234.png
- console-log.txt
- video-reproduction.webm

Root Cause (if known): URL router not handling edge case on first login
```

---

## 10. Metrics and KPIs That Actually Matter

Not all metrics are equal. Some look good but tell you nothing. These are the ones
that provide genuine insight.

### Metrics During Testing

| Metric | Formula | Target | Why it matters |
|---|---|---|---|
| Test Case Execution Rate | Executed / Total × 100 | 100% | Are we completing testing? |
| Defect Detection Rate | Defects found / TC executed | Higher = better | How effective are our tests? |
| Defect Rejection Rate | Rejected defects / Total filed | < 5% | Are we filing valid bugs? |
| Test Pass Rate | Passed / Executed × 100 | > 95% at release | Is the quality high enough? |
| Blocked Test Cases | Tests blocked / Total | < 5% | Are blockers being cleared? |

### Metrics for Automation

| Metric | Target | Warning Sign |
|---|---|---|
| Automation Coverage | 60–80% of regression suite | < 40% = too manual |
| Test Suite Execution Time | < 30 min for regression | > 60 min = need parallelism |
| Flaky Test Rate | < 2% | > 5% = erodes trust in CI |
| Automation ROI | Time saved vs time invested | Should be positive by sprint 3 |

### Metrics for Defects

| Metric | Meaning |
|---|---|
| Defect Density | Defects per feature / per 1000 lines of code |
| Defect Leakage | Defects found by users (in prod) that QA missed |
| Mean Time to Detect (MTTD) | Average time from defect introduction to discovery |
| Mean Time to Resolve (MTTR) | Average time from defect found to defect closed |
| Defect Age | How long defects stay open on average |

**The most important metric:** **Defect Leakage Rate**
```
Defect Leakage = (Bugs found by users in prod / Total bugs found) × 100

Target: < 5%
If > 10%: Your QA process is failing to catch bugs before release
```

---

## 11. How the BLAST Framework App Fits In

The BLAST Framework app you built (`smart-test-plan-buddy.vercel.app`) automates
one of the most time-consuming parts of the test strategy workflow.

### Where It Fits in the Testing Lifecycle

```
JIRA TICKET CREATED
        ↓
   KAN-4 "VIVO V7"  ←── This is the input
        ↓
  [BLAST FRAMEWORK APP]
  1. Fetches ticket via Jira API
  2. Extracts: summary, description, issue type, priority
  3. Sends to GROQ AI (openai/gpt-oss-120b)
  4. AI generates structured test plan
        ↓
   TEST PLAN OUTPUT:
   ├── Overview
   ├── Scope (In/Out)
   └── Test Cases (7+):
       ├── TC-001: Functional (Happy Path)
       ├── TC-002: Functional (Happy Path)
       ├── TC-003: Functional (Happy Path)
       ├── TC-004: Negative
       ├── TC-005: Negative
       ├── TC-006: Edge Case
       └── TC-007: Integration/UI
        ↓
   QA ENGINEER REVIEWS + ENHANCES
        ↓
   TESTS EXECUTED + DEFECTS FILED IN JIRA
```

### What the App Generates (Auto)

The tool auto-generates using the AI and covers:

1. **Test Plan Overview** — what is being tested and why
2. **Scope** — in/out of scope items
3. **Functional Test Cases** — happy path scenarios
4. **Negative Test Cases** — invalid inputs, error states
5. **Edge Cases** — boundary conditions, extreme values
6. **Integration Tests** — component interaction
7. **Downloadable .md file** — portable, version-controllable

### What the QA Engineer Adds (Manual)

The app is a starting point, not a replacement for a thinker. You still add:
- Performance test scenarios
- Security test cases
- Environment-specific details
- Data-specific edge cases
- Business domain nuances the AI doesn't know

---

## 12. A Complete Test Strategy Template

Copy this and fill it in for your project:

```markdown
# Test Strategy — [Project Name]
**Version:** 1.0
**Date:** [Date]
**Author:** [Name]
**Reviewed by:** [Names]

---

## 1. Project Overview
Brief description of the application and business purpose.

## 2. Scope
### In Scope
- [Feature 1]
- [Feature 2]

### Out of Scope
- [Item] — Reason: [why excluded]

## 3. Test Objectives
1. Verify all functional requirements specified in Jira are implemented correctly
2. Ensure system performance meets SLA of < 2s response time under 100 users
3. Validate security controls meet OWASP Top 10 compliance

## 4. Test Approach
**Primary approach:** Risk-Based Testing with Specification-Based test design
**Secondary approach:** Exploratory testing sessions (1 per sprint)

## 5. Test Levels
| Level | Owner | Tools | Coverage Target |
|---|---|---|---|
| Unit | Developers | Jest / PyTest | 80% |
| Integration | Dev + QA | Postman / REST Assured | All API endpoints |
| E2E | QA Team | Playwright | Critical user journeys |
| UAT | Product Owner | Manual | Acceptance criteria |

## 6. Test Types
| Type | Frequency | Owner |
|---|---|---|
| Functional | Every sprint | QA Team |
| Regression | Every release | QA Team (automated) |
| Smoke | Every deployment | CI/CD pipeline |
| Performance | Monthly + pre-release | QA Lead |
| Security | Quarterly | Security team |
| Accessibility | New features | QA Team |

## 7. Test Environment
| Environment | URL | Data | Owner |
|---|---|---|---|
| Local | localhost | Mock data | Developer |
| QA | qa.app.com | Test data | QA Team |
| Staging | staging.app.com | Anonymised prod | DevOps |

## 8. Test Data Strategy
- All test users seeded via setup scripts
- No real PII used in any non-prod environment
- Test data cleaned after each test run
- Edge case data: [list specific data sets]

## 9. Defect Management
- Tool: Jira
- Triage: Daily standup
- SLA: P1 fixed within 4h, P2 within 1 sprint, P3 in backlog

## 10. Entry/Exit Criteria
### Entry Criteria
- [ ] Feature deployed to QA environment
- [ ] Unit tests passing (>80% coverage)
- [ ] Acceptance criteria documented in Jira

### Exit Criteria
- [ ] 100% test cases executed
- [ ] Zero P1/P2 defects open
- [ ] Test summary report approved

## 11. Risk Register
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| [Risk 1] | High | Medium | [action] |

## 12. Tools and Automation
- Test management: Jira + Zephyr Scale
- Automation: Playwright (TypeScript)
- CI/CD: GitHub Actions
- AI-assisted test generation: BLAST Framework (smart-test-plan-buddy.vercel.app)
- Performance: k6
- API: Postman

## 13. Metrics and Reporting
- Weekly test execution report (every Monday)
- Defect trend report (per sprint)
- Automation coverage dashboard (Grafana)
- Release quality report before every prod deployment
```

---

## 13. Real-World Example — KAN-4 (VIVO V7)

Here is how the BLAST Framework app would generate test cases for the actual Jira
ticket from this project, and how you would extend it with strategy thinking.

### The Jira Ticket
```
Ticket ID:   KAN-4
Summary:     VIVO V7
Type:        Story
Priority:    Medium
Project:     KAN (bugzzzzz.atlassian.net)
```

### AI-Generated Test Cases (from the app)

The app produces structured output like this:

```
Test Plan: VIVO V7 Feature Validation

TC-001 | TYPE: Functional | PRIORITY: High
Title: Verify VIVO V7 feature loads successfully
Steps:
  1. Navigate to the VIVO V7 feature page
  2. Verify all page elements load within 3 seconds
  3. Verify content matches the product specification
Expected: Page loads with all required elements visible

TC-002 | TYPE: Functional | PRIORITY: High
Title: Verify primary user flow completes without error
Steps:
  1. Complete the primary user journey for VIVO V7
  2. Verify each step transitions correctly
Expected: Flow completes successfully, success message displayed

TC-003 | TYPE: Negative | PRIORITY: High
Title: Verify graceful handling of invalid input
Steps:
  1. Enter invalid/edge-case data
  2. Submit the form
Expected: Validation error shown, no system crash

TC-004 | TYPE: Negative | PRIORITY: Medium
Title: Verify unauthorised access is blocked
Steps:
  1. Attempt to access VIVO V7 feature without authentication
Expected: 401/redirect to login page

TC-005 | TYPE: Edge | PRIORITY: Medium
Title: Verify behaviour at data boundary limits
Steps:
  1. Test with maximum allowed data size
  2. Test with minimum allowed data size
Expected: System handles both boundary values gracefully

TC-006 | TYPE: Integration | PRIORITY: Medium
Title: Verify VIVO V7 integrates with dependent services
Steps:
  1. Trigger VIVO V7 feature
  2. Verify downstream service receives correct data
Expected: Integration data matches specification

TC-007 | TYPE: UI | PRIORITY: Low
Title: Verify responsive layout on mobile viewport
Steps:
  1. Open VIVO V7 on mobile viewport (375px)
  2. Verify all elements are visible and not overlapping
Expected: UI is responsive and usable on mobile
```

### What a QA Engineer Adds on Top

Using the strategy knowledge from this document:

```
Additional test cases you would add:

TC-008 | TYPE: Performance | PRIORITY: Medium
Verify VIVO V7 page loads in < 2s under 50 concurrent users
Tool: k6 | Measure: P90 response time

TC-009 | TYPE: Security | PRIORITY: High
Verify VIVO V7 endpoints are not vulnerable to SQL injection
Tool: OWASP ZAP | Method: Automated scan + manual probing

TC-010 | TYPE: Accessibility | PRIORITY: Medium
Verify VIVO V7 feature is navigable via keyboard only
Tool: Axe + manual keyboard testing | Standard: WCAG 2.1 AA

TC-011 | TYPE: Regression | PRIORITY: High
Verify VIVO V7 changes do not break existing features
Tool: Playwright automated regression suite | Scope: Full application
```

---

## 14. Common Mistakes and How to Avoid Them

### Mistake 1: Testing Too Late
❌ "We'll test it once development is done"
✅ Shift-left: review requirements, write test cases during development, test APIs
   before UI is ready

---

### Mistake 2: No Clear Exit Criteria
❌ "We'll release when we feel confident"
✅ Document specific, measurable exit criteria before testing begins

---

### Mistake 3: Ignoring Non-Functional Requirements
❌ "It works, ship it" — (it crashes under 20 users)
✅ Always test performance, security, accessibility as first-class citizens

---

### Mistake 4: 100% Automation Goal
❌ "We need to automate everything"
✅ Automate: regression, smoke, API testing (60-70% of tests)
   Manual: exploratory, UX, one-time tests, complex scenarios

---

### Mistake 5: Testing Only Happy Paths
❌ Testing only the scenarios that should work
✅ Test invalid inputs, error states, edge cases, security — that's where bugs live

---

### Mistake 6: Poor Defect Descriptions
❌ "Login doesn't work"
✅ Full reproduction steps, environment details, expected vs actual, screenshots, logs

---

### Mistake 7: No Test Data Strategy
❌ Sharing test accounts across the team, tests stepping on each other
✅ Isolated test data per test, seeded by scripts, cleaned up after execution

---

### Mistake 8: Ignoring Flaky Tests
❌ "It fails sometimes but mostly passes, ignore it"
✅ A flaky test is a broken test — quarantine and fix immediately or it erodes
   trust in the entire test suite

---

## 15. Quick Reference Cheat Sheet

```
╔══════════════════════════════════════════════════════════════╗
║                    TEST STRATEGY CHEAT SHEET                 ║
╠══════════════════════════════════════════════════════════════╣
║ HIERARCHY:  Strategy → Plan → Case                          ║
║ LEVELS:     Unit → Integration → System → UAT               ║
║ APPROACH:   Risk-Based = Likelihood × Impact                ║
╠══════════════════════════════════════════════════════════════╣
║ DESIGN TECHNIQUES                                            ║
║  EP     → One test per partition                            ║
║  BVA    → Test at/around boundaries                         ║
║  DT     → Every condition combination                       ║
║  ST     → Every state transition                            ║
╠══════════════════════════════════════════════════════════════╣
║ DEFECT SEVERITY vs PRIORITY                                  ║
║  Severity = Technical impact (QA decides)                   ║
║  Priority = Business urgency (PO decides)                   ║
╠══════════════════════════════════════════════════════════════╣
║ KEY METRICS                                                  ║
║  Defect Leakage Rate  < 5%  (bugs reaching prod)            ║
║  Test Pass Rate       > 95% (at release gate)               ║
║  Flaky Test Rate      < 2%  (in automation suite)           ║
║  Automation Coverage  60-80% (of regression)                ║
╠══════════════════════════════════════════════════════════════╣
║ API TEST CHECKLIST                                           ║
║  ✓ 200 Happy path                                           ║
║  ✓ 401 No/invalid auth                                      ║
║  ✓ 403 Unauthorised access                                  ║
║  ✓ 400 Invalid input                                        ║
║  ✓ 404 Not found                                            ║
║  ✓ 429 Rate limit                                           ║
║  ✓ 500 Server error (edge cases)                            ║
╠══════════════════════════════════════════════════════════════╣
║ BLAST APP WORKFLOW                                           ║
║  Jira Ticket → BLAST App → AI Test Plan → QA Review →      ║
║  Add Non-Functional → Execute → File Defects in Jira        ║
╚══════════════════════════════════════════════════════════════╝
```

---

*Document maintained as part of the BLAST Framework project.*
*App: https://smart-test-plan-buddy.vercel.app*
*Repo: https://github.com/sanjeev1xy/AI_Learning-With_Testing_Tools*
