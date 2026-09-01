from __future__ import annotations

from jira_qa_crew.services.playwright_parse import parse_playwright_markdown

_MD = """
Here is the automation.

tests/vwo-48.spec.ts
```ts
import { test, expect } from '@playwright/test';

test.describe('VWO-48', () => {
  // VWO-48-TC-001
  test('discounted total', async ({ page }) => {
    await page.goto(process.env.BASE_URL + '/cart');
    await expect(page.getByTestId('total')).not.toHaveText('$0.00');
  });
});
```

## Automation readiness
readiness: NEEDS_CONFIGURATION

## Missing information
- Confirmed selector for the order-summary total
- Discount code test data

## Setup notes
- Set BASE_URL env var

## Assumptions
- Pricing API is reachable from the test env
"""


def test_parses_spec_readiness_and_missing(sample_suite):
    bundle = parse_playwright_markdown(_MD, "VWO-48", sample_suite)
    assert len(bundle.files) == 1
    assert bundle.files[0].path == "tests/vwo-48.spec.ts"
    assert "@playwright/test" in bundle.files[0].content
    assert bundle.readiness.value == "NEEDS_CONFIGURATION"
    assert len(bundle.missing_information) == 2
    assert any(link.test_case_id == "VWO-48-TC-001" for link in bundle.automated_links)
    assert "page.waitForTimeout" not in bundle.files[0].content


def test_falls_back_to_scaffold_when_no_code(sample_suite):
    bundle = parse_playwright_markdown("no code here, sorry", "VWO-48", sample_suite)
    assert len(bundle.files) == 1
    assert "@playwright/test" in bundle.files[0].content
    assert bundle.readiness.value == "NEEDS_CONFIGURATION"


def test_scrubs_hardcoded_credentials(sample_suite):
    md = (
        "tests/vwo-48.spec.ts\n```ts\n"
        "import { test, expect } from '@playwright/test';\n"
        "const creds = { username: 'user1', password: 'Sup3rS3cret!123' };\n"
        "test('VWO-48-TC-001 login', async ({ page }) => { await expect(page).toHaveURL(/./); });\n"
        "```\n## Automation readiness\nreadiness: READY\n"
    )
    bundle = parse_playwright_markdown(md, "VWO-48", sample_suite)
    body = bundle.files[0].content
    assert "Sup3rS3cret!123" not in body
    assert "process.env.TEST_PASSWORD" in body
    assert bundle.readiness.value == "NEEDS_CONFIGURATION"
    assert any("process.env.TEST_" in x for x in bundle.missing_information)


def test_ready_only_without_scaffold_signals(sample_suite):
    md = (
        "tests/vwo-48.spec.ts\n```ts\n"
        "import { test, expect } from '@playwright/test';\n"
        "test('VWO-48-TC-001 x', async ({ page }) => {\n"
        "  await expect(page.getByRole('heading')).toBeVisible();\n"
        "});\n```\n"
        "## Automation readiness\nreadiness: READY\n"
        "## Missing information\n- none\n"
    )
    bundle = parse_playwright_markdown(md, "VWO-48", sample_suite)
    assert bundle.readiness.value == "READY"
    assert bundle.missing_information == []
