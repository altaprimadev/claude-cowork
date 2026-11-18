### CLAUDE.md (router)

Sources read: superpowers:skills/using-superpowers/SKILL.md@22f0b46, superpowers:hooks/session-start@22f0b46, superpowers:hooks/hooks.json@22f0b46

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Router: map task type to the skill that owns it | SP `skills/using-superpowers/SKILL.md` @22f0b46 | modify | Became a stage → agent → skill table keyed on GitHub labels, not conversation intent. |
| "1% chance a skill applies → you MUST invoke it" | SP `skills/using-superpowers/SKILL.md` @22f0b46 | drop | Brief requires dropping it. Over-triggering costs tokens; stage labels already pick the skill. |
| Red-flags table against skipping skills | SP `skills/using-superpowers/SKILL.md` @22f0b46 | drop | The orchestrator does not choose freely; labels decide. Guards live in the stage skills (e.g. `tdd`). |
| Skill priority (process skills before implementation skills) | SP `skills/using-superpowers/SKILL.md` @22f0b46 | modify | Expressed as stage order plus "stack packs load after the core skill". |
| `<SUBAGENT-STOP>`: subagents ignore the router | SP `skills/using-superpowers/SKILL.md` @22f0b46 | take | Subagents follow their agent file, not the orchestrator section. |
| User instructions take precedence over skills | SP `skills/using-superpowers/SKILL.md` @22f0b46 | modify | Replaced by explicit precedence: platform > hook > CLAUDE.md/skills. Approval stays with humans. |
| Platform adaptation references (Codex, Pi, Cursor, ...) | SP `skills/using-superpowers/SKILL.md` @22f0b46 | drop | Only Claude Code cloud sessions are in scope. |
| SessionStart hook injects the router | SP `hooks/session-start` @22f0b46 | drop | `CLAUDE.md` loads automatically in every session; no hook needed. Hooks also do not load in multi-repo cloud sessions. |
| Announce "Using [skill] to [purpose]" | SP `skills/using-superpowers/SKILL.md` @22f0b46 | modify | Replaced by GitHub comments + labels per stage, visible to humans. |
| Never approve/merge/deploy; async one-comment rule; autonomy; trivial exception; language policy | Brief §6.1, §6.2 | write from brief | System-specific global rules. Must load in every session. |
