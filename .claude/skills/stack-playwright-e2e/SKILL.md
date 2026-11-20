---
name: stack-playwright-e2e
description: Rules, commands, flaky-test policy, and review checklist for Playwright end-to-end tests run with Bun. Load only when the repo profile `packs` lists stack-playwright-e2e AND `test_types` includes `e2e`, and the task adds, fixes, or reviews E2E tests.
---
# Stack: Playwright E2E

## Purpose
Keep E2E tests deterministic, isolated, and cheap to debug in ephemeral cloud sessions.
The repo's `playwright.config.ts` and installed `@playwright/test` version are the authority.

## When to use / not use
- Use: `.agent/profile.yml` `test_types` includes `e2e` and the change affects a user journey.
- Do not use: `test_types` lacks `e2e`. Then add no E2E tests and no Playwright dependency, even if useful. Note the gap under Risks in the PR.
- Do not use for component or unit tests. Those follow stack-nextjs-ui / stack-typescript-bun.

## Inputs
- `.agent/profile.yml`: `test_types`, `commands.test`.
- `playwright.config.ts`: `testDir`, `baseURL`, `webServer`, `projects`, `retries`, `trace`.
- Acceptance criteria from the ready issue. One E2E test per critical journey, not per detail.

## Rules

### Locators and assertions
1. Use user-facing locators: `getByRole(role, { name })`, `getByLabel`, `getByText`. Use `getByTestId` only when no accessible locator exists.
2. Never use CSS or XPath tied to layout or generated class names.
3. Narrow with chaining and `filter({ hasText })` instead of `nth()` where possible.
4. Use web-first assertions: `await expect(locator).toBeVisible()`, `toHaveText`, `toHaveURL`. Never `expect(await locator.isVisible())`.
5. Act through locators (`locator.click()`), which auto-wait. Do not use deprecated `page.click(selector)`.

### Waiting
1. No fixed sleeps. `page.waitForTimeout()` is forbidden in committed tests.
2. Wait for a condition: a web-first assertion, `page.waitForResponse(...)`, or `toHaveURL`.
3. Do not rely on `networkidle`. Assert on the UI state the user sees.

### Isolation and data
1. Each test runs alone: own browser context, own data. No order dependence, no shared mutable state.
2. Create test data per test via API or fixtures. Clean up or use unique values.
3. Log in once with a setup project and `storageState`. Do not repeat UI login in every test.
4. Never run E2E against production. Use the local `webServer` or a staging/preview URL from `baseURL`.
5. Never put real credentials in tests or config. Read from env vars provided by the environment.

### Structure
1. Use page objects or fixtures only when two or more tests share a flow. Keep them thin.
2. Test files live where `testDir` points. Name by journey: `checkout.spec.ts`.
3. Cover the happy path and the most likely failure for each critical journey.

### Artifacts and debugging
1. Config keeps `trace: 'on-first-retry'` (or `retain-on-failure`). Never `trace: 'on'` in committed config.
2. `screenshot: 'only-on-failure'`. Video off or `retain-on-failure`.
3. Attach the failing test name, error, and trace path to the PR or issue comment as evidence.

### Flaky-test policy
1. A test that fails then passes on retry is flaky. Report it; do not call the run green without saying so.
2. Find the cause first: run `--repeat-each=10` on the test. Fix the race (locator, assertion, data).
3. Quarantine (`test.fixme`, `test.skip`, tag exclusion) needs a human decision. Do not post or label. Return `NEEDS_HUMAN` with one `escalations:` item: the proposed quarantine as the recommendation, the `--repeat-each` evidence under Checked. The orchestrator vets it.
4. Never skip, delete, or loosen a failing test to get a green run.
5. Never raise timeouts or retries as a fix without a stated cause.

## Commands (Bun)
Use `commands.test` from the profile when it includes E2E. Otherwise:

```bash
bunx playwright test                              # full suite per config
bunx playwright test tests/e2e/checkout.spec.ts   # one file
bunx playwright test -g "checkout succeeds"       # one test by title
bunx playwright test --project=chromium           # one browser project
bunx playwright test --repeat-each=10 <file>      # flakiness check
bunx playwright show-trace <trace.zip>            # inspect a trace
```

Browser install:
- First check whether Chromium is already present (cloud images may preinstall it, e.g. via `PLAYWRIGHT_BROWSERS_PATH`). Run the suite once before installing.
- If missing: `bunx playwright install --with-deps chromium`. Install only browsers the config uses.
- Do not change the Playwright version to match a preinstalled browser. Follow the lockfile.
- No `--headed`, `--debug`, `--ui`, or `show-report` server in cloud sessions; they need a display or block.

## Prefer / Avoid

| Prefer | Avoid |
|---|---|
| `getByRole('button', { name: 'Save' })` | `page.locator('.btn-primary')` |
| `await expect(loc).toHaveText('Done')` | `expect(await loc.textContent()).toBe('Done')` |
| `waitForResponse` or UI assertion | `waitForTimeout(5000)` |
| `storageState` from a setup project | UI login in every test |
| Fix root cause of flake | `test.skip`, higher retries, longer timeouts |
| `bunx playwright ...` | `npx playwright ...` |

## Outputs
- New or updated `*.spec.ts` files, and config changes only when the plan requires them.
- Command output proving the run (pass counts, flaky count) in the evidence report.

## Stop conditions
- `test_types` lacks `e2e`: write no E2E tests.
- Browser install fails or the app cannot start: post one comment with the error output, add `ai:blocked`, stop.
- A test needs quarantine: return `NEEDS_HUMAN` with an escalation (rule 3), stop.

## Review checklist (quality-reviewer)
- [ ] critical: test skipped, deleted, or weakened to pass; real credentials or production URL in tests.
- [ ] major: fixed sleeps; non-web-first assertions; CSS/XPath layout selectors; order-dependent tests.
- [ ] major: E2E tests added while `test_types` lacks `e2e`.
- [ ] major: flaky result reported as green.
- [ ] minor: `trace: 'on'` or always-on video; unneeded page objects; missing failure case for a critical journey.

## References
- Playwright best practices: https://playwright.dev/docs/best-practices (accessed 2026-11-18; page states no version, follow repo lockfile)
- Playwright locators: https://playwright.dev/docs/locators (not fetched; known from best-practices page)
- Playwright trace viewer: https://playwright.dev/docs/trace-viewer (not fetched)

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
