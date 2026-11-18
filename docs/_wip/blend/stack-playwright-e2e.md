### stack-playwright-e2e

Sources read: ECC:skills/e2e-testing/SKILL.md@3f14a10, ECC:agents/e2e-runner.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Activation for every E2E-capable repo | ECC `agents/e2e-runner.md` @3f14a10 ("use proactively") | modify | Gated on profile `test_types` including `e2e`. |
| Agent Browser as primary tool | ECC `agents/e2e-runner.md` @3f14a10 | drop | Not in stack target; global npm install in ephemeral containers. |
| `data-testid` > CSS > XPath locator priority | ECC `agents/e2e-runner.md`, `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Replaced with official role-first locators; testid as last resort. |
| Wait for conditions, never `waitForTimeout` | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Core flake prevention. |
| `waitForLoadState('networkidle')` as fix | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | Official docs discourage; use web-first assertions. |
| Test isolation, no shared state | ECC `agents/e2e-runner.md` @3f14a10 | take | Matches official guidance. |
| Page Object Model always | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Only when 2+ tests share a flow. |
| Config template (multi-browser, retries 2, reporters, `npm run dev` webServer) | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | Repo config is authority; versions follow repo. |
| Trace on first retry, screenshot/video on failure | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Traces on failure only. |
| Quarantine via `test.fixme`/`test.skip` by agent | ECC `skills/e2e-testing/SKILL.md`, `agents/e2e-runner.md` @3f14a10 | modify | Quarantine needs human (`ai:needs-human`); never skip to get green (integrity). |
| `--repeat-each=10` flake detection | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Evidence before claims. |
| `--headed`, `--debug`, `show-report` | ECC `agents/e2e-runner.md` @3f14a10 | drop | No display in cloud sessions. |
| GitHub Actions E2E workflow (setup-node, npm ci) | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | CI is repo-owned; Node/npm not in stack. |
| E2E test report template | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | evidence-report skill owns reporting. |
| Wallet/Web3 and financial flow examples | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Kept only "never run against production". |
| Success metrics (95% pass, <5% flaky) | ECC `agents/e2e-runner.md` @3f14a10 | drop | Global thresholds; any flake is reported. |
| Role locators, web-first assertions, auth via setup project, install only needed browsers | https://playwright.dev/docs/best-practices accessed 2026-11-18 | write from docs | Official guidance; `bunx` instead of `npx`. |
