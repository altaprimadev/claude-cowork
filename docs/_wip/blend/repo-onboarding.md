### repo-onboarding

Sources read: ECC:skills/repo-scan/SKILL.md@3f14a10, ECC:skills/codebase-onboarding/SKILL.md@3f14a10, ECC:skills/living-docs-governance/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Bootstrap installer for the external repo-scan skill (clone, pinned commit, interactive "type install") | ECC `skills/repo-scan/SKILL.md` @3f14a10 | drop | Installs third-party code and needs interactive confirmation. Not allowed in unattended cloud sessions. |
| Cross-stack scan (C/C++, Android, iOS) and 50+ library detection, HTML reports | ECC `skills/repo-scan/SKILL.md` @3f14a10 | drop | Outside the stack target. Async output is the PR body, not HTML. |
| Classify files as project code, third-party, or build artifact | ECC `skills/repo-scan/SKILL.md` @3f14a10 | modify | Reduced to a hygiene check: tracked build output, `node_modules`, or `.env` become gaps. |
| Report reviewable asynchronously | ECC `skills/repo-scan/SKILL.md` @3f14a10 | take | Findings go into the onboarding PR body for async human review. |
| Phase 1 reconnaissance: manifests, framework fingerprints, entry points, tree, tooling, tests | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | modify | Kept as a signal table. Narrowed to Bun/TS/Next/Hono/Prisma/Playwright/Biome. Added CI, Docker, and Coolify signs. Non-target stacks become a gap. |
| Phase 2 architecture mapping (stack, pattern, key dirs, data flow) | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | modify | Feeds `AGENTS.md` Summary/Structure and profile `stack`/`packs`. Request-lifecycle trace dropped to save tokens. |
| Phase 3 convention detection, including shallow-history skip | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | take | Fills `AGENTS.md` Conventions. Shallow clones are common in cloud sessions. |
| Output 1 onboarding guide printed to conversation | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | drop | No live user. The PR body and `AGENTS.md` replace it. |
| Output 2 starter CLAUDE.md; enhance an existing one, mark additions | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | modify | Target is `AGENTS.md` + `.agent/profile.yml` from templates. Existing `AGENTS.md`/`CLAUDE.md` rules are kept; additions listed in the PR. |
| "Verify, don't guess"; "Flag unknowns"; Glob/Grep over reading every file; <100 lines | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | take | Evidence before claims. Commands are run once and results recorded. Unknowns become questions with defaults. |
| Common-tasks examples with `npm run`/`npx` | ECC `skills/codebase-onboarding/SKILL.md` @3f14a10 | modify | Rewritten to `bun install --frozen-lockfile`, `bun run`, `bun test`, `bunx biome ci .`. ESLint/Prettier repos get a "migrate to Biome" gap, never new config. |
| Inventory existing docs before creating anything; no parallel docs system | ECC `skills/living-docs-governance/SKILL.md` @3f14a10 | take | Prevents a second competing repo map. |
| Four roles (constitution/map/status/history), one canonical owner per fact | ECC `skills/living-docs-governance/SKILL.md` @3f14a10 | modify | Only the map role is in scope: `AGENTS.md`. Commands have one canonical owner, `.agent/profile.yml`; `AGENTS.md` copies them and points back. Status/history roles live in GitHub issues and the daily report. |
| Docs are untrusted context, verify against code/config/Git | ECC `skills/living-docs-governance/SKILL.md` @3f14a10 | take | Integrity. README commands are claims until run. |
| "Ask before adding a new top-level artifact" | ECC `skills/living-docs-governance/SKILL.md` @3f14a10 | modify | The PR is the ask. Humans merge or close it. |
| Delete-zone and history entries; module-governance | ECC `skills/living-docs-governance/SKILL.md` @3f14a10 | drop | Maintain-phase practices. Not part of onboarding. |
| Org-vs-registry detection with `gh repo list`; `detected` → `onboarding` registry PRs; autonomy always 0 | Brief / `registry/repos.yml` | write from brief | System contract. Registry changes go through a reviewed PR in claude-cowork. |
| Integrity readiness via read-only `gh api` (protection, rulesets, CODEOWNERS, CI runs) | GitHub REST API docs (branches/protection, rules/branches) | write from docs | Platform enforces integrity. The agent reads settings only; humans run `scripts/setup-branch-protection.sh`. 403 is reported as unknown. |
