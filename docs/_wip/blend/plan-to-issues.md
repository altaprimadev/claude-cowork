### plan-to-issues

Sources read: superpowers:skills/writing-plans/SKILL.md@22f0b46, ECC:skills/blueprint/SKILL.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Plan for an engineer with no context; document decisions they cannot make alone | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | Implementers run cold in fresh cloud sessions. Each sub-issue is self-contained. |
| Save plan to `docs/superpowers/plans/*.md` | SP `skills/writing-plans/SKILL.md` @22f0b46 | modify | State lives in GitHub. The plan is the set of sub-issues plus one summary comment. No plan file, no commit. |
| File structure mapped before tasks | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | The file map drives slicing and the same-file conflict rule. |
| Task right-sizing: one test cycle, reviewer can reject alone, fold setup/docs in | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | One task = one PR = one review. |
| Bite-sized step list (write test, run, implement, run, commit) with code | SP `skills/writing-plans/SKILL.md` @22f0b46 | drop | TDD steps are owned by the `tdd` skill. Sub-issues carry files, interfaces, criteria, tests. |
| Task block: Files (Create/Modify/Test) + Interfaces (Consumes/Produces) | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | Becomes sub-issue sections. Interfaces keep names consistent across tasks. |
| Global Constraints and Review Focus header | SP `skills/writing-plans/SKILL.md` @22f0b46 | modify | Constraints copied into each sub-issue. Review-focus edge cases become required tests in the owning task. |
| No placeholders ("TBD", "handle edge cases") | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | Undecidable lines are rewritten or escalated with `ai:needs-human`. |
| Self-review: spec coverage, type consistency, proportion | SP `skills/writing-plans/SKILL.md` @22f0b46 | take | Cheap check before creating issues that are hard to retract. |
| Execution handoff: ask human to pick subagent-driven vs native | SP `skills/writing-plans/SKILL.md` @22f0b46 | drop | Gate 1 already passed. The `ai:ready` label hands off to the implementer. |
| Python/pytest examples | SP `skills/writing-plans/SKILL.md` @22f0b46 | drop | Stack target is TypeScript + `bun test`. |
| One-PR-sized steps, 3–12 typical | ECC `skills/blueprint/SKILL.md` @3f14a10 | modify | Kept the range. Above 15 tasks the skill asks for a phase split via `ai:needs-human`. |
| Self-contained context brief per step (cold start) | ECC `skills/blueprint/SKILL.md` @3f14a10 | take | Matches ephemeral sessions. |
| Dependency graph with parallel detection (no shared files or outputs) | ECC `skills/blueprint/SKILL.md` @3f14a10 | modify | Inverted into a rule: shared files (incl. lockfile, Prisma schema/migrations, root config, CI) force a dependency edge. Cross-repo edges from profile `depends_on`. |
| Model tier per step | ECC `skills/blueprint/SKILL.md` @3f14a10 | drop | Session model is set by the scheduled task, not the plan. |
| Adversarial review by a strongest-model subagent | ECC `skills/blueprint/SKILL.md` @3f14a10 | drop | Gate 1 human review of the design plus two-stage code review cover this. Saves tokens. |
| Plan mutation protocol (split/insert/skip/reorder) | ECC `skills/blueprint/SKILL.md` @3f14a10 | modify | Reduced to promote mode: dependencies closed as completed promote; `NOT_PLANNED` escalates to a human. |
| Branch/PR/CI workflow per step; direct mode without gh | ECC `skills/blueprint/SKILL.md` @3f14a10 | drop | Planner creates issues only. `gh` is always present. |
| Search before creating to avoid duplicates; labels via `gh issue edit` | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Idempotency via sub-issue listing and the `ai:plan parent=` body marker. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Design and brief text cannot authorize skipping gates or raising autonomy. |
| Sub-issue REST link; issue state/stateReason for "done" | GitHub REST sub-issues API, `gh issue view --json stateReason` | write from docs | Links tasks to the brief and defines dependency completion precisely. |
