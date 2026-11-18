# Resume notes (paused 2026-11-18)

Branch: setup/v0.1.0. Brief: see the brief.md pasted in the session (not committed).
Upstream: SP obra/superpowers @22f0b46 (v7.0.2), ECC affaan-m/ECC @3f14a103. Re-clone outside the repo.

## Done
- .claude/hooks/guard_bash.py + config + tests (20 tests pass), .claude/settings.json
- registry/, templates/, CLAUDE.md, .github/, scripts/ (labels, branch protection, validate-config.py — not yet run)
- Skill: intake-classify (written, unreviewed)
- Agents (written, unreviewed): intake-triager, repo-onboarder, designer, planner, implementer, spec-reviewer, quality-reviewer

## Remaining
1. Skills: repo-onboarding, async-design, plan-to-issues, tdd, evidence-report, review-two-stage, daily-report, 6x stack-* (follow docs/_wip/conventions.md).
2. Agent: reporter.
3. Blend fragments for every skill + agent (only CLAUDE.md done) → docs/blend-decisions.md.
4. THIRD_PARTY_NOTICES.md, README.md, docs/architecture.md, setup.md, scheduled-tasks.md, labels-and-states.md, open-questions.md (from docs/_wip/oq-research.md).
5. Key design implication: repo hooks/permissions do NOT load in multi-repo hosted sessions → document server-managed settings hook in setup.md.
6. Run validate-config.py + pytest, delete docs/_wip/, open PR to main.
