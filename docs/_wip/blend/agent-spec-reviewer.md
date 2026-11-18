### spec-reviewer (agent)

Sources read: superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/task-reviewer-prompt.md@22f0b46, superpowers:skills/subagent-driven-development/re-review-prompt.md@22f0b46, superpowers:skills/subagent-driven-development/references/cannot-verify.md@22f0b46, ECC:agents/code-reviewer.md@3f14a103, ECC:agents/typescript-reviewer.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Spec compliance: missing / extra / misunderstood | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | Core of stage 1. Each criterion gets a verdict with file:line. |
| Do not trust the report | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | PR body is unverified claims; check against diff and evidence. |
| Cannot-verify items instead of crawling | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | Marked `cannot-verify` with what the orchestrator should check. |
| Combined spec + quality in one reviewer | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Split into two agents with fresh context each; stage 2 runs only after stage 1 PASS. |
| Read-only on the checkout | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Enforced with `disallowedTools: Write, Edit, NotebookEdit` plus a Bash allowlist. |
| No subagent dispatch | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | One review seat per stage. |
| Use actual PR base branch, never hard-code main | ECC `agents/typescript-reviewer.md` @3f14a103 | take | `gh pr view --json baseRefName`. |
| Approve / Warning / Block verdict | ECC `agents/code-reviewer.md` @3f14a103 | modify | PASS / FAIL returned to orchestrator. No GitHub approval; Gate 2 is human. |
| Severity Critical / Important / Minor | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Renamed critical / major / minor per shared contract. |
| Scoped re-review of fix rounds | SP `skills/subagent-driven-development/re-review-prompt.md` @22f0b46 | modify | Orchestrator re-runs stage 1 on the updated PR; scope stays the issue criteria. |
| Zero findings is valid | ECC `agents/code-reviewer.md` @3f14a103 | take | Prevents manufactured findings. |
