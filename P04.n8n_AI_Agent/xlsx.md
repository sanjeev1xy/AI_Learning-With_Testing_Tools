# Playwright + XLSX — Working Code

## Install

```bash
npm install xlsx
npm install --save-dev @playwright/test
npx playwright install
```

---

## Step 1 — xlsx Helper (`utils/readXlsx.ts`)

```typescript
import * as xlsx from 'xlsx';
import * as path from 'path';

export interface TestUser {
  email: string;
  password: string;
  validity: string;
}

export function readUsersFromXlsx(filePath: string): TestUser[] {
  const workbook = xlsx.readFile(filePath);
  const sheet = workbook.Sheets['Sheet1'];
  const raw: Record<string, string>[] = xlsx.utils.sheet_to_json(sheet);

  return raw.map((row) => ({
    email: String(row['email                             '] ?? '').trim(),
    password: String(row['password '] ?? '').trim(),
    validity: String(row['validity'] ?? '').trim(),
  }));
}
```

> **Note:** The xlsx column names in `testdata/data.xlsx` have trailing spaces.
> The helper trims them. If you ever re-export the file you can simplify to `row['email']`.

---

## Step 2 — Playwright Test (`tests/login.spec.ts`)

```typescript
import { test, expect } from '@playwright/test';
import * as path from 'path';
import { readUsersFromXlsx, TestUser } from '../utils/readXlsx';

const xlsxPath = path.resolve(__dirname, '../testdata/data.xlsx');
const users: TestUser[] = readUsersFromXlsx(xlsxPath);

for (const user of users) {
  test(`Login test — ${user.email} [${user.validity}]`, async ({ page }) => {
    await page.goto('https://example.com/login');   // <-- replace with your URL

    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.click('button[type="submit"]');

    if (user.validity === 'valid') {
      await expect(page).toHaveURL(/dashboard/);
      await expect(page.locator('.welcome')).toBeVisible();
    } else {
      await expect(page.locator('.error-message')).toBeVisible();
    }
  });
}
```

---

## Step 3 — `playwright.config.ts`

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: {
    headless: true,
    screenshot: 'only-on-failure',
  },
});
```

---

## Step 4 — Run

```bash
npx playwright test tests/login.spec.ts
```

---

## Data in `testdata/data.xlsx` (Sheet1)

| email | password | validity |
|---|---|---|
| laura.taylor1234@example.com | test123 | valid |
| … | … | valid/invalid |

---

## Quick Standalone Script (no Playwright, just verify xlsx read)

```typescript
// verify-xlsx.ts
import * as path from 'path';
import { readUsersFromXlsx } from './utils/readXlsx';

const users = readUsersFromXlsx(path.resolve(__dirname, 'testdata/data.xlsx'));
console.table(users);
```

Run with:

```bash
npx ts-node verify-xlsx.ts
```
