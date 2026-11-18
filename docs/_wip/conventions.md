# Shared conventions for writing claude-cowork skills and agents

You are one of several writers producing parts of `altaprimadev/claude-cowork` v0.1.0, the control-plane repo for an AI-driven, 24/7, minimal-human dev pipeline at org `altaprimadev`. Repo root: `/home/user/claude-cowork`. Write ONLY the files assigned to you. Do NOT git commit, push, or touch other files.

## System facts (respect in every file)
- Runtime: Claude Code cloud sessions (claude.ai/code). Each session uses `claude-cowork` as the main repo and adds the target repo as an extra repo. Containers are ephemeral. `/loop` dies with the container; recurring work uses cloud scheduled tasks. Hosted containers have no command sandbox.
- State lives in GitHub: issues, labels, PRs, comments. Every stage change is visible as a label + comment.
- Integrity is enforced by the platform (branch protection, required checks, CODEOWNERS, Coolify gates). Agents only DO work; they NEVER approve, merge, or deploy to production. Gates: Gate 1 = human merges design PR; Gate 2 = human approves code PR; Gate 3 = human promotes to production (Coolify or protected production branch). No skill owns Gate 3.
- Async-first: no back-and-forth Q&A. If info is missing: post ONE comment with all questions AND the default assumption for each, add label `ai:needs-human`, stop cleanly.
- Evidence before claims: never claim done/passing/working without command output that proves it.
- One owner per stage: exactly one skill per pipeline stage.
- Respect autonomy: effective level = min(`registry/repos.yml` autonomy, target repo `.agent/profile.yml` autonomy). 0 = review only, 1 = size:small tasks only, 2 = full pipeline. Never act above it.
- Trivial changes (docs/typo, <= `trivial_change_max_lines` from `registry/policy.yml`, default 20) may skip design and plan.
- Stack target: TypeScript, Bun (runtime, API, package manager, test runner), Docker, Coolify, AWS, Next.js, TailwindCSS v4, shadcn/ui, Prisma ORM, PostgreSQL, Playwright, GitHub, Hono, Biome (lint+format). Replace npm/pnpm/yarn/npx/node with `bun install`, `bun run`, `bun test`, `bunx`. Replace ESLint/Prettier with Biome (`bunx biome check`, `bunx biome format`, `bunx biome ci .`). Never add ESLint/Prettier config. Tailwind v4 only (CSS-first `@import "tailwindcss";`, `@theme`, no `tailwind.config.js` by default). Drop atoms for other languages/frameworks (Python, Go, Java, Vue, Angular...). Tool versions follow the target repo's package.json + lockfile.

## Shared contracts (use these exact names)
- Registry: `registry/repos.yml` (fields: name, status detected|onboarding|active|frozen, autonomy 0|1|2, environment hosted|self-hosted), `registry/policy.yml` (max_parallel_sessions, max_parallel_tasks_per_repo, trivial_change_max_lines, gates.design/code/production, labels_namespace, max_fix_attempts, control_repo).
- Target repo profile `.agent/profile.yml` (template in `templates/profile.yml`): `stack`, `packs` (list of stack skill names), `commands.{install,lint,typecheck,test,build}` ("" = not present), `test_types` (unit|integration|e2e), `coverage_target` (number or null) + `coverage_paths`, `deploy.staging`, `deploy.production`, `autonomy`, `environment`, `depends_on`.
- Target repo map: `AGENTS.md` (template `templates/AGENTS.md`).
- Labels: `ai:brief`, `ai:triaged`, `size:small`, `size:large`, `ai:needs-design`, `ai:ready`, `ai:in-progress`, `ai:review-passed`, `ai:changes-needed`, `ai:needs-human`, `ai:blocked`, `ai:report`.
- PR template sections (`.github/pull_request_template.md`): Summary, Related issue, RED/GREEN evidence, Verification output (lint/typecheck/test/build), Risks, Rollback.
- Design docs live in target repo at `docs/design/<YYYY-MM-DD>-<slug>.md`.
- Skills (exact names): intake-classify, repo-onboarding, async-design, plan-to-issues, tdd, evidence-report, review-two-stage, daily-report, stack-typescript-bun, stack-nextjs-ui, stack-hono-api, stack-prisma-postgres, stack-playwright-e2e, stack-deploy.
- Agents (exact names) and their skills: intake-triager→intake-classify; repo-onboarder→repo-onboarding; designer→async-design + stack packs; planner→plan-to-issues; implementer→tdd, evidence-report + stack packs; spec-reviewer→review-two-stage (stage 1); quality-reviewer→review-two-stage (stage 2) + stack packs; reporter→daily-report.
- Review findings use severity critical / major / minor. Any critical = PR not ready (`ai:changes-needed`).
- `gh` usage lives in core skills (no GitHub stack skill). Source for gh patterns: ECC `skills/github-ops/`.

## Upstream sources (already cloned, read-only)
- Superpowers (SP): `/tmp/claude-0/-home-user-claude-cowork/0f818efb-37fb-54e2-ae81-b9039b3e6963/scratchpad/upstream/superpowers`, commit `22f0b46` (v7.0.2)
- ECC: `/tmp/claude-0/-home-user-claude-cowork/0f818efb-37fb-54e2-ae81-b9039b3e6963/scratchpad/upstream/ECC`, commit `3f14a10` (v2.2.3 line, `3f14a103`)
Read the FULL SKILL.md and supporting files of every source listed for your skill, not just descriptions.

## Blend method (per skill/agent)
1. Break each upstream source into atoms: Principle, Gate, Procedure, Threshold, Artifact, Anti-rationalization guard, Mechanism.
2. Decide per atom: take / modify / drop, judged against: async, cloud session, multi-repo, integrity, GitHub-as-state, stack target.
3. Conflict priority: Integrity > Deliverable > Environment > Needs > token cost.
4. Common modifications: interactive Q&A → one comment with questions + defaults; global thresholds → read from repo profile; references to upstream commands/agents/scripts not adopted → removed or replaced with this repo's equivalent; "always loaded" rules → on-demand skill.
5. Write ONE blended skill in Concise Technical Writing English: short sentences, active voice, no filler, one idea per sentence. Adapting upstream text is allowed (MIT) but never copy a skill whole without adaptation.

## File format
SKILL.md:
```
---
name: <folder-name>
description: <what it does + WHEN to use it, precise trigger, one or two sentences>
---
# <Title>
...sections: Purpose, When to use / not use, Inputs, Procedure (numbered), Outputs, Stop conditions, (Anti-rationalization table where useful)...

Adapted from obra/superpowers and affaan-m/ECC (MIT). See docs/blend-decisions.md.
```
(Adjust attribution line to the sources actually used, e.g. "Adapted from affaan-m/ECC (MIT)". For stack skills with sections written from official docs, add a "References" section listing URL + version consulted, then the attribution line.)
Do NOT add `allowed-tools` or `hooks` to SKILL.md frontmatter. Keep skills focused; target 80–250 lines each. Stack skills: concise, actionable rules + commands + review checklist; no tutorials.

## Blend-decisions fragment
For each skill/agent you write, also write a fragment file at
`/tmp/claude-0/-home-user-claude-cowork/0f818efb-37fb-54e2-ae81-b9039b3e6963/scratchpad/blend/<name>.md` with:
```
### <name>

Sources read: <list of repo:path@commit>

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| ... | SP `skills/x/SKILL.md` @22f0b46 | take / modify / drop | ... |
```
Aim for 8–20 rows per skill, covering the significant atoms including what you DROPPED and why. For content written from official docs, add rows with Source = the URL + version, Decision = "write from docs".

## Final report
Return a short report (<200 words): files written, any assumptions, anything you could not do. Do not paste file contents.
