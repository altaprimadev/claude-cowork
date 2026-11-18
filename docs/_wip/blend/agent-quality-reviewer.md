### quality-reviewer (agent)

Sources read: superpowers:skills/subagent-driven-development/task-reviewer-prompt.md@22f0b46, ECC:agents/code-reviewer.md@3f14a103, ECC:agents/security-reviewer.md@3f14a103, ECC:agents/typescript-reviewer.md@3f14a103, ECC:agents/react-reviewer.md@3f14a103, ECC:agents/database-reviewer.md@3f14a103, ECC:agents/e2e-runner.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Pre-report gate (exact line, failure mode, context, defensible severity) | ECC `agents/code-reviewer.md` @3f14a103 | take | Step 6. Fail any answer: downgrade or drop. |
| HIGH/CRITICAL require snippet, scenario, why guards miss it | ECC `agents/code-reviewer.md` @3f14a103 | take | Applied to critical findings. |
| Zero findings is valid; common false positives list | ECC `agents/code-reviewer.md` @3f14a103 | modify | Kept the principle; detailed false-positive list lives in `review-two-stage`. |
| Merge readiness: report failing/pending checks first | ECC `agents/typescript-reviewer.md` @3f14a103 | modify | Reported as a finding via `gh pr checks`; no re-runs. |
| Run eslint / prettier / npm audit | ECC `agents/typescript-reviewer.md` @3f14a103 | drop | Biome and CI own lint. Reviewer reads CI output instead of running tools. |
| OWASP Top 10 and security pattern table | ECC `agents/security-reviewer.md` @3f14a103 | modify | Security reviewed first; checklist sits in the skill and packs. |
| Alert owner and rotate secrets on critical | ECC `agents/security-reviewer.md` @3f14a103 | drop | Reviewer is read-only; orchestrator posts the critical finding and humans rotate. |
| React hooks, RSC boundary, a11y checks | ECC `agents/react-reviewer.md` @3f14a103 | modify | Moved to `stack-nextjs-ui` pack checklist, loaded only when listed in `packs`. |
| Index FKs, timestamptz, short transactions | ECC `agents/database-reviewer.md` @3f14a103 | modify | Moved to `stack-prisma-postgres`. RLS / `auth.uid()` dropped (Supabase-specific). |
| Wait for conditions, not time; flaky quarantine | ECC `agents/e2e-runner.md` @3f14a103 | modify | Moved to `stack-playwright-e2e` review checklist. |
| Do not re-run tests; one focused test only on specific doubt | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | No installs, builds, migrations, or full suite. |
| Read-only, no posting, no labels | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Enforced with `disallowedTools`; orchestrator posts findings and sets labels. |
