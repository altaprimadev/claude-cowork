### planner (agent)

Sources read: ECC:agents/planner.md@3f14a103, superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/references/batching.md@22f0b46, ECC:skills/github-ops/SKILL.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Step breakdown with file paths, dependencies, risk | ECC `agents/planner.md` @3f14a103 | modify | Each step becomes a GitHub sub-issue with acceptance criteria and dependency links. |
| Implementation order by dependency | ECC `agents/planner.md` @3f14a103 | take | Sub-issues are ordered; dependents start only after their prerequisites close. |
| Independently mergeable phases | ECC `agents/planner.md` @3f14a103 | take | One sub-issue = one PR that stands alone. |
| Testing strategy per plan | ECC `agents/planner.md` @3f14a103 | modify | Test expectations per sub-issue, limited to profile `test_types`. |
| "All tests pass with 80%+ coverage" success criterion | ECC `agents/planner.md` @3f14a103 | modify | Coverage target read from `.agent/profile.yml`, never a global number. |
| Ask clarifying questions | ECC `agents/planner.md` @3f14a103 | modify | Async: ONE comment on the parent with questions and defaults, `ai:needs-human`. |
| Stripe worked example | ECC `agents/planner.md` @3f14a103 | drop | Token cost. The skill holds the sub-issue template. |
| Plan file + task briefs extracted per task | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | modify | GitHub issues replace the plan file; each issue body is the task brief. |
| Spec is the binding authority over the plan | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | take | Merged design doc wins over planner judgment. |
| Search before creating to avoid duplicates | ECC `skills/github-ops/SKILL.md` @3f14a103 | take | Check existing sub-issues before creating any. |
| Read-only tools | ECC `agents/planner.md` @3f14a103 | modify | Bash added for `gh issue create`; no Write/Edit, no branches or PRs. |
