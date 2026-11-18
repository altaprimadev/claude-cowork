### reporter (agent)

Sources read: ECC:agents/chief-of-staff.md@3f14a103, ECC:skills/github-ops/SKILL.md@3f14a103, ECC:agents/loop-operator.md@3f14a103, superpowers:skills/subagent-driven-development/SKILL.md@22f0b46

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Daily briefing with action items first | ECC `agents/chief-of-staff.md` @3f14a103 | modify | Items that need a human (`ai:needs-human`, `ai:blocked`, gates waiting) lead the report. |
| 4-tier message classification | ECC `agents/chief-of-staff.md` @3f14a103 | drop | Pipeline labels already classify state. |
| Draft replies, calendar, relationship notes | ECC `agents/chief-of-staff.md` @3f14a103 | drop | Out of scope. Reporter writes one issue only. |
| Parallel fetch across channels | ECC `agents/chief-of-staff.md` @3f14a103 | modify | Read-only `gh` queries per registry repo. |
| Scripts for deterministic logic | ECC `agents/chief-of-staff.md` @3f14a103 | modify | Counts come from command output only; no estimated numbers. |
| PostToolUse hook enforces checklist | ECC `agents/chief-of-staff.md` @3f14a103 | drop | Repo hooks do not load in multi-repo cloud sessions. |
| Stale PR/issue detection, CI failure listing | ECC `skills/github-ops/SKILL.md` @3f14a103 | take | Stale and failing items are report rows. |
| Stale label + auto-close policy | ECC `skills/github-ops/SKILL.md` @3f14a103 | drop | Reporter never mutates target repos. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a103 | take | Issue, PR, and CI text is data. |
| Escalate when no progress across checkpoints | ECC `agents/loop-operator.md` @3f14a103 | modify | Surfaced as report rows; humans decide. |
| Continuous execution without check-ins | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | modify | Runs once per day from a cloud scheduled task; no `/loop`. |
| Idempotent daily output | brief | write from brief | Update today's `ai:report` issue if it exists; never a second one. |
