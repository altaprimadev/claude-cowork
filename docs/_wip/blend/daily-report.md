### daily-report

Sources read: ECC:skills/cost-tracking/SKILL.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Read `~/.claude/metrics/costs.jsonl` written by the `stop:cost-tracker` hook | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Containers are ephemeral and the hook is not adopted. The file does not survive between sessions. |
| "If the log is missing, do not fabricate usage data" | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Usage/cost section shows real data with its source, or "not available". |
| Prefer precomputed cost; do not hard-code pricing or estimate from tokens | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Prevents misleading numbers. Extended: no estimates from session counts. |
| Latest row per session; do not sum cumulative rows | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Specific to the dropped log format. |
| Reporting guidance: today vs yesterday, totals, by model, 4-decimal formatting | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Only applies with a real data source; the source's own fields decide the breakdown. |
| `node -e` scripts | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Stack target forbids `node`; data comes from `gh` queries. |
| Do not recommend installing unreviewed hooks | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Integrity. The report never proposes hook installs. |
| PR management checklist: CI status, age, last activity | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Became the section classifier: awaiting approval, stuck, in progress, done. |
| Stale policy (14d issues, 7d PRs, add `stale`, auto-close) | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Threshold is 24h for `ai:in-progress`. The report only lists stale items; it never labels or closes them. |
| Flag PRs > 5 days without review | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Design PRs (Gate 1) and `ai:review-passed` PRs (Gate 2) are listed with age under "Needs you". |
| CI ops: `gh run list --status failure`, flaky vs real | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Used read-only to find recurring failures (2+ occurrences). No re-runs. |
| Release management, Dependabot/secret-scanning alerts, release checklist | ECC `skills/github-ops/SKILL.md` @3f14a10, `references/ecc-release-checklist.md` | drop | Out of scope for the pipeline report; releases and production are human-owned. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Titles are quoted as data. |
| Quality gate "all issues triaged have labels" | ECC `skills/github-ops/SKILL.md` @3f14a10 | drop | Other stages own labels. Reporting has no write scope outside `ai:report` issues. |
| One issue per date, `ai:report` label, idempotent edit; close superseded reports | Brief / `registry/policy.yml` `control_repo` | write from brief | GitHub is the state store; re-runs must not create duplicates. |
