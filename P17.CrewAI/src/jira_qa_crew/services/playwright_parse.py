"""Deterministically parse the Playwright agent's markdown into a PlaywrightBundle.

The Playwright stage emits free-form markdown (fenced ``ts`` code blocks plus
notes). Parsing it here keeps that stage robust on small models / strict-schema
providers, and keeps traceability + readiness under Python control.
"""

from __future__ import annotations

import re

from ..models import (
    AutomatedTestLink,
    AutomationReadiness,
    PlaywrightBundle,
    PlaywrightFile,
    TestCaseSuite,
)

_FENCE_RE = re.compile(
    r"```(?:ts|typescript|tsx|javascript|js)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
# Hard-coded credential literals -> env vars, so generated specs never ship a secret.
_CRED_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|api[_-]?key|apikey|secret|token|bearer|auth[_-]?token)\b"
    r"(\s*[:=]\s*)(['\"])(?!.*(?:process\.env|PLACEHOLDER|YOUR_|EXAMPLE|CHANGEME))([^'\"]{6,})\3"
)


def _scrub_secrets(content: str) -> tuple[str, bool]:
    changed = False

    def _repl(m: re.Match) -> str:
        nonlocal changed
        changed = True
        name = re.sub(r"[^A-Za-z0-9]+", "_", m.group(1)).upper().strip("_")
        return f"{m.group(1)}{m.group(2)}process.env.TEST_{name} ?? ''"

    return _CRED_RE.sub(_repl, content), changed
_PATH_HINT_RE = re.compile(r"(?:^|\n)[`*#\s]*((?:tests|pages|fixtures)/[\w./-]+\.tsx?)", re.IGNORECASE)
_SECTION_RE = re.compile(r"(?im)^#{1,6}\s*(missing information|missing info|assumptions|setup notes|coverage)\b")


def _bullets_after(text: str, heading_pattern: str) -> list[str]:
    m = re.search(rf"(?im)^#{{1,6}}\s*{heading_pattern}\b.*?$", text)
    if not m:
        return []
    tail = text[m.end() :]
    stop = re.search(r"(?m)^#{1,6}\s", tail)
    block = tail[: stop.start()] if stop else tail
    out = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ", "• ")):
            item = line[2:].strip()
            if item and item.lower() not in {"none", "n/a", "none.", "_none._"}:
                out.append(item)
    return out


def parse_playwright_markdown(raw: str, ticket_key: str, suite: TestCaseSuite) -> PlaywrightBundle:
    raw = raw or ""
    blocks = _FENCE_RE.findall(raw)
    ts_blocks = [b.strip() for b in blocks if "test(" in b or "@playwright/test" in b or "test.describe" in b]
    if not ts_blocks and blocks:
        ts_blocks = [blocks[0].strip()]

    files: list[PlaywrightFile] = []
    scrubbed_any = False
    lower = ticket_key.lower()
    path_hints = _PATH_HINT_RE.findall(raw)
    for i, content in enumerate(ts_blocks):
        path = path_hints[i] if i < len(path_hints) else f"tests/{lower}.spec.ts"
        if not path.endswith((".ts", ".tsx")):
            path += ".ts"
        content, scrubbed = _scrub_secrets(content)
        scrubbed_any = scrubbed_any or scrubbed
        files.append(PlaywrightFile(path=path, content=content))

    if not files:
        files = [
            PlaywrightFile(
                path=f"tests/{lower}.spec.ts",
                content=(
                    "import { test, expect } from '@playwright/test';\n\n"
                    f"// SCAFFOLD for {ticket_key} — the automation agent did not return usable code.\n"
                    "// Configure selectors / baseURL, then implement the cases below.\n"
                    f"test.describe('{ticket_key}', () => {{\n"
                    "  test.skip('needs configuration', async ({ page }) => {});\n"
                    "});\n"
                ),
            )
        ]

    all_ts = "\n".join(f.content for f in files)

    automatable = [tc for tc in suite.test_cases if tc.automation_candidate.value in {"Yes", "Partial"}]
    links: list[AutomatedTestLink] = []
    for tc in automatable:
        if tc.id in all_ts or tc.id.lower() in all_ts.lower():
            links.append(
                AutomatedTestLink(
                    spec_title=tc.title,
                    test_case_id=tc.id,
                    jira_key=tc.jira_key,
                    requirement_ids=tc.requirement_ids,
                    acceptance_criteria_ids=tc.acceptance_criteria_ids,
                )
            )
    if not links and automatable:
        # Code exists but did not name the ids — still record the intended mapping.
        for tc in automatable:
            links.append(
                AutomatedTestLink(
                    spec_title=tc.title,
                    test_case_id=tc.id,
                    jira_key=tc.jira_key,
                    requirement_ids=tc.requirement_ids,
                    acceptance_criteria_ids=tc.acceptance_criteria_ids,
                )
            )

    missing = _bullets_after(raw, r"missing info(?:rmation)?") or _bullets_after(raw, r"missing")
    assumptions = _bullets_after(raw, r"assumptions?")

    text_l = raw.lower()
    scaffold_signals = (
        "needs_configuration" in text_l
        or "needs configuration" in text_l
        or "placeholder" in text_l
        or "scaffold" in text_l
        or "todo" in text_l
        or bool(missing)
    )
    ready_signal = re.search(r"readiness[:\s*]+`?ready`?", text_l) and not scaffold_signals and not scrubbed_any
    readiness = AutomationReadiness.READY if ready_signal else AutomationReadiness.NEEDS_CONFIGURATION

    setup = _bullets_after(raw, r"setup notes?")
    coverage = _bullets_after(raw, r"coverage")

    if scrubbed_any:
        missing = list(missing) + [
            "Credential literals in the generated spec were replaced with process.env.TEST_* — "
            "supply real test credentials via environment variables."
        ]

    return PlaywrightBundle(
        ticket_key=ticket_key,
        files=files,
        automated_links=links,
        setup_notes="; ".join(setup),
        coverage_notes="; ".join(coverage),
        assumptions=assumptions,
        missing_information=missing
        or (["Confirmed selectors, base URL and test data are not available from the ticket."]
            if readiness == AutomationReadiness.NEEDS_CONFIGURATION else []),
        readiness=readiness,
    )
