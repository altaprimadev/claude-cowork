### designer (agent)

Sources read: ECC:agents/architect.md@3f14a103, ECC:agents/planner.md@3f14a103, ECC:agents/code-explorer.md@3f14a103, superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/implementer-prompt.md@22f0b46

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Trade-off analysis: pros, cons, alternatives, decision | ECC `agents/architect.md` @3f14a103 | take | Every decision in the design doc records alternatives and trade-offs. |
| ADR format | ECC `agents/architect.md` @3f14a103 | modify | Folded into one design doc at `docs/design/<YYYY-MM-DD>-<slug>.md`; the async-design skill owns the template. |
| Example architecture (Supabase, FastAPI, Vercel, Redis) | ECC `agents/architect.md` @3f14a103 | drop | Off-target stack. Stack packs from the profile supply conventions. |
| Scalability tiers (10K to 10M users) | ECC `agents/architect.md` @3f14a103 | drop | Generic. Non-functional targets come from the brief or become questions. |
| Read-only tools (Read, Grep, Glob) | ECC `agents/architect.md` @3f14a103 | modify | Needs Write/Edit for the doc, Bash for git/gh, Skill for packs. Write scope limited to the doc. |
| Analyze existing structure before proposing | ECC `agents/code-explorer.md` @3f14a103 | modify | Read only the code areas the design needs. |
| Escalate architectural decisions with several valid approaches | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Write the doc with a default, ONE comment with questions and defaults, `ai:needs-human`. |
| Model selection: most capable model for design | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | drop | Model is set by the cloud session and agent config, not per prompt. |
| Stack packs loaded on demand with file fallback | brief / CLAUDE.md | write from brief | Skill tool first, then `.claude/skills/<pack>/SKILL.md` in the claude-cowork clone. |
| Gate 1: human merges the design PR | brief | write from brief | Designer opens the PR only. Planning waits for the merge. |
