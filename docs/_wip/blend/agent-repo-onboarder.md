### repo-onboarder (agent)

Sources read: ECC:skills/codebase-onboarding/SKILL.md@3f14a103, ECC:agents/code-explorer.md@3f14a103, ECC:agents/doc-updater.md@3f14a103, ECC:agents/architect.md@3f14a103, superpowers:skills/subagent-driven-development/SKILL.md@22f0b46

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Reconnaissance: manifests, framework fingerprints, tests, CI, Docker | ECC `skills/codebase-onboarding/SKILL.md` @3f14a103 | modify | Narrowed to signals that fill `.agent/profile.yml` fields and pick packs. Non-target languages ignored. |
| Generate a starter CLAUDE.md | ECC `skills/codebase-onboarding/SKILL.md` @3f14a103 | modify | Output is `AGENTS.md` from `templates/AGENTS.md`. Target repos get no CLAUDE.md from us. |
| Entry points, execution paths, layer map | ECC `agents/code-explorer.md` @3f14a103 | modify | Kept only as the repo map sections in `AGENTS.md`. No deep feature tracing. |
| Codemap generation under docs/CODEMAPS | ECC `agents/doc-updater.md` @3f14a103 | drop | One map file (`AGENTS.md`) is enough. Extra docs cost tokens to maintain. |
| Current state analysis / tech debt list | ECC `agents/architect.md` @3f14a103 | drop | Onboarding records facts, not recommendations. Debt belongs in briefs. |
| Run detected commands to prove they exist | evidence rule (CLAUDE.md) | write from brief | Evidence before claims. Each command gets pass/fail/absent from real output. |
| Fresh subagent with constructed context | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | take | Orchestrator passes repo name, clone path, and registry entry only. |
| Escalate when uncertain instead of guessing | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Undetectable values become `""`/`null` plus a question with default in the PR, `ai:needs-human`. |
| Start at autonomy 0; never edit registry | brief | write from brief | Humans raise autonomy. Registry changes are proposed in the PR body. |
| Write scope: profile and map only | ECC `agents/doc-updater.md` @3f14a103 | modify | Write/Edit kept, but limited to `.agent/profile.yml` and `AGENTS.md`. |
