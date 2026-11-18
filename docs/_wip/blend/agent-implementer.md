### implementer (agent)

Sources read: superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/implementer-prompt.md@22f0b46, superpowers:skills/subagent-driven-development/references/fix-loop.md@22f0b46, superpowers:skills/subagent-driven-development/references/handling-reports.md@22f0b46, ECC:agents/tdd-guide.md@3f14a103, ECC:agents/e2e-runner.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Implement exactly what the task specifies; YAGNI | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | One issue, one branch, one PR, inside issue scope. |
| You do not dispatch subagents (no self-spawned reviewer) | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Review comes from spec-reviewer and quality-reviewer only. |
| Ask questions before and during work | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Async: ONE issue comment with questions and defaults, `ai:needs-human`. |
| Status contract DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | NEEDS_CONTEXT became NEEDS_HUMAN with a GitHub label. |
| Report file with RED/GREEN evidence | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Evidence goes into the PR body template, not a local report file. Containers are ephemeral. |
| Self-review before reporting | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Step 6 checks criteria coverage, scope, and patterns. |
| Fix round: re-run covering tests, append fix evidence | SP `skills/subagent-driven-development/references/fix-loop.md` @22f0b46 | modify | Evidence appended to the PR. Cap = `max_fix_attempts` from policy, then `ai:blocked`. |
| Fix-loop model escalation at rounds 4-5 | SP `skills/subagent-driven-development/references/fix-loop.md` @22f0b46 | drop | Orchestrator does not pick models per round; the cap stops the loop. |
| Escalate on architectural decisions | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Return NEEDS_HUMAN with the options. |
| RED-GREEN-REFACTOR cycle | ECC `agents/tdd-guide.md` @3f14a103 | take | Owned by the `tdd` skill; agent preloads it. |
| npm test / 80% coverage | ECC `agents/tdd-guide.md` @3f14a103 | modify | Commands and coverage come from `.agent/profile.yml`. Bun replaces npm. |
| Agent Browser primary, Playwright fallback | ECC `agents/e2e-runner.md` @3f14a103 | drop | Playwright only, via the `stack-playwright-e2e` pack when listed. |
