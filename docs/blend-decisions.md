# Blend decisions

How each skill, agent, and `CLAUDE.md` was built from upstream sources.
Use this file to review the PR and to resync when upstream releases a new version.

## Sources

| Repo | Commit | Version |
|---|---|---|
| SP = https://github.com/obra/superpowers | `22f0b463e7a5e579904dd6211a520321035526f7` | v7.0.2 |
| ECC = https://github.com/affaan-m/ECC | `3f14a103a8694e51c1df9a806217a6d0b5f7a6f7` | v2.2.3 line |

## Method

1. Read every listed upstream `SKILL.md` and its supporting files.
2. Split each source into atoms: principle, gate, procedure, threshold, artifact, anti-rationalization guard, mechanism.
3. Decide per atom: **take**, **modify**, or **drop**. Judge each atom against six constraints:
   - async: no human answers in real time,
   - cloud session: short-lived containers,
   - multi-repo: settings differ per repo,
   - integrity: humans approve, the platform enforces gates,
   - GitHub as state: progress shows in issues and PRs,
   - stack target.
4. Resolve conflicts by priority: Integrity > Deliverable > Environment > Needs > token cost.
5. Write one blended skill per stage in Concise Technical Writing English.

Common modifications:
- Interactive Q&A became one comment with questions and default assumptions.
- Global thresholds became values read from `.agent/profile.yml`.
- References to upstream commands and agents that were not adopted were removed.
- npm, npx, and node became Bun. ESLint and Prettier became Biome. Tailwind v3 became v4.

Decision values:
- **write from docs:** the content comes from official documentation, not from upstream.
- **write from brief** and **write from policy:** the content comes from this project's brief or policy.

## Router

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

## Stage skills

### intake-classify

Sources read: ECC:skills/orch-pipeline/SKILL.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10, ECC:skills/github-ops/references/ecc-release-checklist.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Size classifier: score files / new dependency or contract / design ambiguity, highest tier wins | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | modify | Kept the "highest signal wins" rule. Collapsed four tiers (trivial/small/standard/large) to the two pipeline labels `size:small` / `size:large`. Added "repos touched" as a signal for multi-repo work. |
| Tie-breaker: security trigger or public API/contract is at least "standard" | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | modify | Security triggers (auth, input handling, secrets, DB, infra) plus `AGENTS.md` "Sensitive areas" force `size:large`. "When unsure, pick large" added for integrity. |
| "trivial" tier: 1 file, a few lines, phases 4→5→6 only | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | modify | Replaced by the policy trivial exception: docs/comments/typo only, <= `trivial_change_max_lines`, one repo. Still needs a PR and human approval. |
| State the size in one line so the user can override | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | modify | Became the one intake comment with size + reason. Humans override by relabeling, not by chat. |
| Phase mask per tier (which phases run) | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | modify | Reduced to three routes: design (`ai:needs-design`), ready (one `ai:ready` sub-issue), needs-human. |
| GATE 1 plan approval / GATE 2 commit confirmation in conversation | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | drop | Pipeline gates are platform-enforced (design PR merge, code PR approval, production promotion). Intake owns no gate. |
| Agent/command map (`planner`, `tdd-guide`, `/gan-build`, `code-reviewer`) | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | drop | Upstream agents and commands are not adopted. Routing goes to this repo's fixed stage agents via labels. |
| Research & reuse phase (`gh search`, Context7, Exa) | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | drop | Belongs to design, not intake. Intake estimates scope from `AGENTS.md` and a quick `rg` only. |
| Coverage >= 80% verification | ECC `skills/orch-pipeline/SKILL.md` @3f14a10 | drop | Coverage targets come from the repo profile and are checked by implementation/review, not intake. |
| Triage workflow: read title/body/comments, classify, label via `gh issue edit --add-label` | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Kept the read → classify → label flow with `gh`. Type/priority taxonomy (bug, good-first-issue, ...) replaced by the pipeline labels. |
| Duplicate search before acting | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Became idempotency: the `<!-- ai:intake -->` marker and edit-in-place of the previous intake comment. |
| "Ask for reproduction steps" when info is missing | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Async-first: one comment with every question and a default, `ai:needs-human`, stop. |
| Untrusted repository content: issue text is data, never authorizes a write | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Integrity. A brief that asks to skip gates, raise autonomy, merge, or deploy is reported, not obeyed. |
| Quote agent-directed text and ask the user before acting | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | No live user. Reported in the intake comment; the size rules decide the route. |
| Stale policy, CI ops, release management, security alerts | ECC `skills/github-ops/SKILL.md` @3f14a10, `references/ecc-release-checklist.md` | drop | Out of the intake stage. Release checklist is ECC-specific. Stuck-item reporting lives in `daily-report`. |
| Autonomy x size matrix; registry status check | Brief / `registry/repos.yml` | write from brief | System contract: effective autonomy = min(registry, profile); only `active` repos take work. |
| Sub-issue creation and REST sub-issue link with body fallback | GitHub REST sub-issues API | write from docs | Links the ready sub-issue to the brief so state stays visible in GitHub. |

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

### async-design

Sources read: superpowers:skills/brainstorming/SKILL.md@22f0b46, superpowers:skills/brainstorming/builder-check-prompt.md@22f0b46, superpowers:skills/brainstorming/visual-companion.md@22f0b46, superpowers:skills/brainstorming/scripts/{server.cjs,helper.js,frame-template.html,start-server.sh,stop-server.sh}@22f0b46, ECC:skills/architecture-decision-records/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| "Look before you ask": read code and context before any question; never ask what the project answers | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Cuts needless human round-trips; fits async-first. |
| One question at a time, Socratic conversation, play-back chunks | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | No live human. Became: sort unknowns into answered / minor assumption / blocking question with default; one comment carries all blocking questions. |
| "Fill in defaults, but say them out loud" (red flag table) | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Became the mandatory Assumptions section; anti-rationalization row kept. |
| Lay out 2-3 approaches with trade-offs, recommend one | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | Human no longer picks in chat; designer picks and records rejected alternatives (>=2) in the doc; human overrides via PR review. |
| Written design: intent, goals/non-goals/anti-goals, constraints, approaches, left to builder | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Core of the doc template; anti-goals folded into Non-goals. |
| Doc path `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | Shared contract: `docs/design/<YYYY-MM-DD>-<slug>.md` in the target repo, on branch `design/<issue>-<slug>`. |
| Size the work (short vs full doc) | SP `skills/brainstorming/SKILL.md` @22f0b46 | drop | Intake already sized it; this skill only runs for size:large. |
| Builder check via fresh subagent, sort questions into answered/minor/theirs | SP `skills/brainstorming/builder-check-prompt.md` @22f0b46 | modify | Designer agent has no subagent tool; uses SP's fallback (read as the builder yourself), once. The three piles map to answered/assumption/open question. |
| HARD-GATE: nothing built until the human approves the doc | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | Approval = human merge of the design PR (Gate 1). Chat approval does not count. |
| After approval invoke writing-plans | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | Replaced by `plan-to-issues`, triggered by the merge, not by this skill. |
| Spike to feel things out | SP `skills/brainstorming/SKILL.md` @22f0b46 | drop | Code before Gate 1 violates integrity; uncertainty goes into Risks or Open questions. |
| Visual companion (browser server, mockups, scripts) | SP `skills/brainstorming/visual-companion.md`, `scripts/*` @22f0b46 | drop | Cloud containers have no user browser; async review happens on GitHub. Mermaid in the doc covers diagrams. |
| "Offer to just dive in" opt-out | SP `skills/brainstorming/SKILL.md` @22f0b46 | drop | Route is decided by size labels, not by the requester. |
| ADR format: context, decision, alternatives (pros/cons/why not), consequences, risks | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | take | Gives the Decision/Alternatives/Consequences sections their ADR shape. |
| Status lifecycle proposed -> accepted | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | modify | Doc starts `proposed`; merge makes it accepted. No separate status edits by agents. |
| Numbered `docs/adr/NNNN` files + README index | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | drop | Shared contract fixes date-based `docs/design/` paths; existing ADRs are read as input. |
| Ask user consent before creating files / writing ADR | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | modify | Consent = the PR itself; human merges or closes. |
| "Keep it short, context <= 10 lines, be specific" | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | take | Keeps the doc reviewable asynchronously. |
| Decision detection signals in conversation | ECC `skills/architecture-decision-records/SKILL.md` @3f14a10 | drop | Trigger is the `ai:needs-design` label, not chat phrases. |
| Test strategy per profile `test_types`, coverage only for `coverage_paths` | Brief / `templates/profile.yml` | write from brief | System contract; keeps design and tdd consistent. |

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

### tdd

Sources read: superpowers:skills/test-driven-development/SKILL.md@22f0b46, superpowers:skills/test-driven-development/writing-good-tests.md@22f0b46 (this version's replacement for testing-anti-patterns.md; no file of that name exists at 22f0b46), ECC:skills/tdd-workflow/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Iron law: no production code without a failing test first | SP `skills/test-driven-development/SKILL.md` @22f0b46 | take | Core guarantee; "for the right reason" made explicit. |
| Code written before the test: delete it, no "reference" | SP `skills/test-driven-development/SKILL.md` @22f0b46 | take | Brief requires it; mapped to `git restore` / delete. |
| Verify RED: fails, not errors, for the expected reason | SP `skills/test-driven-development/SKILL.md` @22f0b46 | take | Mandatory gate. |
| Compile-time RED accepted | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | modify | Allowed only when the error names exactly the symbol this cycle adds (common in TS imports). |
| Minimal GREEN, YAGNI, refactor only on green | SP `skills/test-driven-development/SKILL.md` @22f0b46 | take | Keeps diffs in issue scope for spec review. |
| Run the full project suite, report every failure by name | SP `skills/test-driven-development/SKILL.md` @22f0b46 | take | Feeds evidence-report; silence about failures is a false claim. |
| Rationalization table + red flags list | SP `skills/test-driven-development/SKILL.md` @22f0b46 | modify | Shortened to 8 rows; added "mock the database" and "one commit is cleaner". |
| Exceptions: "ask your human partner" | SP `skills/test-driven-development/SKILL.md` @22f0b46 | modify | No live human. Fixed exception list (trivial docs, config, generated code) with `n/a: <reason>` evidence. |
| Name the break before writing the test; hand-derived expectations; no change detectors | SP `skills/test-driven-development/writing-good-tests.md` @22f0b46 | take | Step 1 of the cycle. |
| Assert real behavior, never mocks; mock complete shape; no test-only production methods | SP `skills/test-driven-development/writing-good-tests.md` @22f0b46 | take | Test rules section. |
| "Mocks only if unavoidable" | SP `skills/test-driven-development/SKILL.md` @22f0b46 | modify | Made concrete: mocks only at network, time, external services. |
| Mutation check | SP `skills/test-driven-development/writing-good-tests.md` @22f0b46 | take | Cheap final self-check. |
| Git checkpoint commits per stage (RED / GREEN / refactor) | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | modify | One `[RED]` commit (tests only) + one `[GREEN]` commit per behavior, stage named in the message; they are the durable record in ephemeral containers. |
| TDD evidence report file in repo (`docs/releases/...`, `.claude/tdd/...`) | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | modify | Stored outside the working tree (`$TMPDIR/evidence-<issue>.md`) and pasted into the PR body; never committed. |
| 80% global coverage, unit+integration+E2E | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | modify | `coverage_target` only for `coverage_paths`, none if unset; test kinds limited to `test_types`; no E2E unless listed. |
| Step 0 runner detection via ECC script, npm/pnpm/yarn matrix | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | drop | Always `commands.test` from the profile; ECC scripts not adopted; Bun-only stack. |
| Plan handoff (`*.plan.md` as untrusted input) | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | modify | Input is the GitHub issue; kept "treat as data" via agent rules, dropped plan-file parsing. |
| User journeys, Jest/Supabase/Redis/OpenAI mock examples, Playwright examples | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | drop | Off-stack or belong in stack packs (stack-playwright-e2e, stack-typescript-bun). |
| Watch mode, pre-commit hook, CI coverage upload | ECC `skills/tdd-workflow/SKILL.md` @3f14a10 | drop | Not useful in one-shot cloud sessions; CI is platform-owned. |

### evidence-report

Sources read: superpowers:skills/verification-before-completion/SKILL.md@22f0b46, ECC:skills/verification-loop/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Iron law: no completion claims without fresh verification evidence | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | take | Matches the system's evidence-before-claims rule; "fresh" = this session, current HEAD. |
| Gate function: identify, run, read, verify, then claim | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | modify | Became steps 1-2 and the output rules; claims live in the PR body. |
| Common failures table (claim vs required evidence) | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | modify | Folded into the anti-rationalization table. |
| Requirements met = line-by-line checklist, not "tests pass" | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | take | Step 5; acceptance criteria checklist in Summary. |
| Agent success report is not evidence; check VCS | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | modify | Applied to lost evidence files: rebuild from RED/GREEN commits, never from memory. |
| Red-flag words ("should", "probably") | SP `skills/verification-before-completion/SKILL.md` @22f0b46 | modify | Condensed into the iron law and table to save tokens. |
| Six phases: build, types, lint, tests+coverage, security grep, diff review | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Commands come from profile in fixed order install, lint, typecheck, test, build; "" = not configured; security grep and diff review kept as one step on the PR diff. |
| "If build fails, STOP" | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Run all commands to capture every failure (except after install failure), then fix loop capped at `max_fix_attempts`, then `ai:blocked`. |
| `set -o pipefail` and output limiting (`tail`, `sed -n`) | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Kept pipefail; full log to file, then truncation rules: passing = summary tail, failing = all errors. |
| 80% coverage target | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Only `coverage_target` over `coverage_paths`; none if unset. |
| npm/pnpm/pyright/ruff command examples | ECC `skills/verification-loop/SKILL.md` @3f14a10 | drop | Bun + Biome stack; commands come from the profile. |
| console.log grep | ECC `skills/verification-loop/SKILL.md` @3f14a10 | drop | Biome lint and stage 2 review cover it. |
| VERIFICATION REPORT text block | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Replaced by PR template sections (Summary, Related issue, RED/GREEN, Verification output, Risks, Rollback) — GitHub is the state. |
| Target acceptance (staging/prod verification reported separately) | ECC `skills/verification-loop/SKILL.md` @3f14a10 | modify | Agents never deploy to production (Gate 3); staging check out of scope, reported as "not performed". |
| Continuous mode every 15 min, hook integration | ECC `skills/verification-loop/SKILL.md` @3f14a10 | drop | One-shot cloud sessions; hooks do not load in multi-repo sessions. |

### review-two-stage

Sources read: superpowers:skills/requesting-code-review/SKILL.md@22f0b46, superpowers:skills/requesting-code-review/code-reviewer.md@22f0b46, superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/{implementer-prompt.md,task-reviewer-prompt.md,re-review-prompt.md}@22f0b46, superpowers:skills/subagent-driven-development/references/{fix-loop.md,cannot-verify.md,handling-reports.md,final-review.md,batching.md,preflight.md,resuming.md}@22f0b46, superpowers:skills/subagent-driven-development/scripts/review-package@22f0b46, ECC:agents/code-reviewer.md@3f14a10, ECC:skills/security-review/SKILL.md@3f14a10, ECC:skills/security-review/cloud-infrastructure-security.md@3f14a10, ECC:agents/security-reviewer.md@3f14a10, ECC:agents/typescript-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Reviewer gets crafted context, never the session history; fresh subagent | SP `skills/requesting-code-review/SKILL.md` @22f0b46 | take | Orchestrator passes only PR, issue, design, round, prior findings. |
| Spec compliance (missing / extra / misunderstood) then code quality | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Split into two agents and two stages; stage 2 runs only after stage 1 passes. |
| "Do not trust the report"; rationales never downgrade severity | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | PR body treated as claims; stage 1 verifies RED/GREEN commits and output are real. |
| Read-only reviewer; reviewers never dispatch subagents | SP `skills/requesting-code-review/code-reviewer.md` @22f0b46 | take | Reviewers return findings; orchestrator alone posts and labels. |
| Don't pre-judge findings in the dispatch prompt | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | take | Orchestrator rule in step 3. |
| "Cannot verify from diff" items resolved by controller | SP `skills/subagent-driven-development/references/cannot-verify.md` @22f0b46 | take | Confirmed gap = critical stage 1 finding. |
| Fix loop: resume implementer, scoped re-review (ADDRESSED / NOT ADDRESSED + fix-diff breakage) | SP `skills/subagent-driven-development/references/fix-loop.md`, `re-review-prompt.md` @22f0b46 | modify | Re-review uses fresh reviewers with FIX_BASE = last reviewed head from the comment marker; cap = `max_fix_attempts` (not 5), then `ai:needs-human` instead of controller adjudication. |
| Controller rulings / parking at the cap, "rulings not stalls" | SP `skills/subagent-driven-development/SKILL.md`, `references/fix-loop.md` @22f0b46 | drop | Integrity: decisions on disputed findings go to the human at Gate 2, not the orchestrator. |
| Ledger file in `.superpowers/sdd/`, resuming, review-package scripts | SP `skills/subagent-driven-development/SKILL.md`, `references/resuming.md`, `scripts/*` @22f0b46 | modify | Containers are ephemeral; state lives in PR comments with `<!-- ai:review round=N head=sha -->` marker and labels. Scripts not adopted; `gh pr diff` / `git diff` instead. |
| Model selection tiers, batching, preflight scan, final whole-branch review | SP `skills/subagent-driven-development/SKILL.md`, `references/*` @22f0b46 | drop | One PR = one issue; no multi-task plan in this stage; agent files fix the models. |
| Implementer status contract (DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT) | SP `skills/subagent-driven-development/implementer-prompt.md`, `references/handling-reports.md` @22f0b46 | modify | Lives in the implementer agent; review starts on DONE; fix rounds pass findings verbatim. |
| Severity Critical / Important / Minor; "Ready to merge?" verdict | SP `skills/requesting-code-review/code-reviewer.md` @22f0b46 | modify | Shared contract critical/major/minor; no merge verdict — labels `ai:review-passed` / `ai:changes-needed`; never approve. |
| Confidence filtering, pre-report gate, HIGH/CRITICAL need proof, zero findings valid | ECC `agents/code-reviewer.md` @3f14a10 | take | Shared rules "Proof" and "Zero findings is valid". |
| Common false positives list | ECC `agents/code-reviewer.md`, `agents/security-reviewer.md` @3f14a10 | modify | Condensed to one line in stage 2. |
| Checklist: security, quality, React/Next.js, backend, performance | ECC `agents/code-reviewer.md` @3f14a10 | modify | Reordered and trimmed to stack target; Biome-enforced style skipped; file-size thresholds dropped. |
| OWASP Top 10 / code pattern table | ECC `agents/security-reviewer.md`, `skills/security-review/SKILL.md` @3f14a10 | modify | Condensed into the stage 2 security bullet, mapped to Hono, Prisma (`$queryRawUnsafe`), Next.js Server Actions. |
| `npm audit`, `eslint-plugin-security`, Supabase RLS, Solana checks | ECC `skills/security-review/SKILL.md`, `agents/security-reviewer.md` @3f14a10 | drop | Off-stack (ESLint, Supabase, Solana) or needs install/network that read-only reviewers do not run; new-dependency check kept. |
| Cloud infra checklist (IAM, VPC, Cloudflare, backups) | ECC `skills/security-review/cloud-infrastructure-security.md` @3f14a10 | drop | Belongs to `stack-deploy` pack; only "CI or deploy config weakened" kept. |
| TS checks: any, `!`, `as`, floating promises, async forEach, hook deps | ECC `agents/typescript-reviewer.md` @3f14a10 | take | Applied only when the diff has .ts/.tsx. |
| Merge-readiness check (CI state) before review | ECC `agents/typescript-reviewer.md` @3f14a10 | modify | `gh pr checks` failures reported as a finding instead of stopping. |
| Approve / Warning / Block criteria | ECC `agents/code-reviewer.md` @3f14a10 | modify | Any critical or stage 1 failure -> `ai:changes-needed`; else `ai:review-passed`. Never `--approve`. |

### daily-report

Sources read: ECC:skills/cost-tracking/SKILL.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Read `~/.claude/metrics/costs.jsonl` written by the `stop:cost-tracker` hook | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Containers are ephemeral and the hook is not adopted. The file does not survive between sessions. |
| "If the log is missing, do not fabricate usage data" | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Usage/cost section shows real data with its source, or "not available". |
| Prefer precomputed cost; do not hard-code pricing or estimate from tokens | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Prevents misleading numbers. Extended: no estimates from session counts. |
| Latest row per session; do not sum cumulative rows | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Specific to the dropped log format. |
| Reporting guidance: today vs yesterday, totals, by model, 4-decimal formatting | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Only applies with a real data source; the source's own fields decide the breakdown. |
| `node -e` scripts | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | drop | Stack target forbids `node`; data comes from `gh` queries. |
| Do not recommend installing unreviewed hooks | ECC `skills/cost-tracking/SKILL.md` @3f14a10 | take | Integrity. The report never proposes hook installs. |
| PR management checklist: CI status, age, last activity | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Became the section classifier: awaiting approval, stuck, in progress, done. |
| Stale policy (14d issues, 7d PRs, add `stale`, auto-close) | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Threshold is 24h for `ai:in-progress`. The report only lists stale items; it never labels or closes them. |
| Flag PRs > 5 days without review | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Design PRs (Gate 1) and `ai:review-passed` PRs (Gate 2) are listed with age under "Needs you". |
| CI ops: `gh run list --status failure`, flaky vs real | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Used read-only to find recurring failures (2+ occurrences). No re-runs. |
| Release management, Dependabot/secret-scanning alerts, release checklist | ECC `skills/github-ops/SKILL.md` @3f14a10, `references/ecc-release-checklist.md` | drop | Out of scope for the pipeline report; releases and production are human-owned. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Titles are quoted as data. |
| Quality gate "all issues triaged have labels" | ECC `skills/github-ops/SKILL.md` @3f14a10 | drop | Other stages own labels. Reporting has no write scope outside `ai:report` issues. |
| One issue per date, `ai:report` label, idempotent edit; close superseded reports | Brief / `registry/policy.yml` `control_repo` | write from brief | GitHub is the state store; re-runs must not create duplicates. |

### draft-brief

Sources read: superpowers:skills/brainstorming/SKILL.md@22f0b46, ECC:skills/github-ops/SKILL.md@3f14a10

Human-invoked skill. It is the only skill that runs a live conversation, because a human starts it and answers in the same session. It does not own a pipeline stage; it writes the input that intake reads.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Look before you ask: read the project before the first question | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Registry, `AGENTS.md`, and code answer many questions. Never ask what they already answer. |
| Ask only when the answer changes what gets built; one question at a time | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Keeps the chat shorter than the form. |
| Open questions until the why is known; then named options with a pick | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | The Goal field needs the why. |
| State defaults out loud as proposals | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Defaults go into the draft as assumptions the human can reject. |
| Play back in chunks; only what they said counts as theirs | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | One playback of the full draft in issue format, with a list of filled-in items. |
| Several independent projects: split and order | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | One brief per outcome, matching the form rule. |
| Hard gate: nothing is built before approval | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | No issue is created until the human types the fixed phrase `post now`. General approval words do not count. |
| Lay out approaches; size the work; written design doc; builder check | SP `skills/brainstorming/SKILL.md` @22f0b46 | drop | Design belongs to `async-design`, sizing to `intake-classify`. A brief states outcomes, not approaches. |
| Visual companion, spikes, writing-plans handoff | SP `skills/brainstorming/SKILL.md` @22f0b46 | drop | Out of scope for writing an issue. |
| Search before creating to avoid duplicates | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Open `ai:brief` issues are checked first. |
| Untrusted content: no gate-skipping instructions | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Removed from the draft with a note to the human, since intake would ignore them anyway. |
| Body in issue-form output format; MCP, `gh`, or prefilled form link | brief / `.github/ISSUE_TEMPLATE/ai-brief.yml` | write from brief | Intake parses chat-made and form-made briefs the same way. Works with or without an authenticated `gh`. |

### inbox

Sources read: ECC:agents/chief-of-staff.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10

Human-invoked, read-only. It is the on-demand version of the "Needs you" part of `daily-report`.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Briefing with action items first | ECC `agents/chief-of-staff.md` @3f14a10 | modify | Groups ordered by what the human must do: questions, blocked, Gate 1, Gate 2, onboarding. |
| 4-tier message classification | ECC `agents/chief-of-staff.md` @3f14a10 | modify | Pipeline labels decide the group; first matching group wins. |
| Parallel fetch across channels | ECC `agents/chief-of-staff.md` @3f14a10 | modify | Read-only `gh` or MCP calls per registry repo. |
| Flag PRs waiting for review, with age | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Gate 1 and Gate 2 items show their age. |
| Stale label and auto-close | ECC `skills/github-ops/SKILL.md` @3f14a10 | drop | Inbox never writes. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Item text is summarized as data. |
| Mark blockers that a comment cannot fix | brief / CLAUDE.md | write from brief | Autonomy, registry, and protection blockers need a PR or platform change. |

### usage-reminder

Sources read: ECC:agents/chief-of-staff.md@3f14a10 (through `inbox`)

Human-invoked. Original to claude-cowork. It reuses `usage-status` for the reset time and the `inbox` grouping idea for task status.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| One-shot reminder chain, rescheduled at each five-hour reset | brief | write from brief | The window starts at the first request after a reset, so a fixed cron cannot follow it. |
| Fall back to now + 5h when usage data is missing | brief | write from brief | One failed read must not end the chain. |
| Task status grouped by state, needs-human first | ECC `agents/chief-of-staff.md` @3f14a10 | modify | Same first-match grouping as `inbox`, extended with in-flight and queued work. |
| No quiet hours | brief | write from brief | The human asked for reminders around the clock. |
| Read-only on GitHub | brief / CLAUDE.md | write from brief | A reminder reports; pipeline work stays with the scheduled tasks. |

### run-pipeline

Sources read: none.

Human-invoked. Sends a scheduled task's stored prompt to the runner session; no GitHub writes. Original to claude-cowork.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Send the stored prompt to the runner session with send_message | brief | write from brief | The prompt is read from the scheduled task at call time, so it cannot drift. Only the runner session has the repos. |
| Do not use fire_trigger | first real run, 2026-11-19 | rejected | A manual fire started a new session without repos. The run stopped at setup. |
| Stop when the runner session is working | brief | write from brief | Two runs on the same queue can pick the same item. |
| Gate on usage advice; batch at caution needs `force` | CLAUDE.md "Usage budget" | write from brief | Same light/heavy split as the pipeline. The batch prompt does not check the budget yet. |

### skills-help

Sources read: none.

Human-invoked, read-only. Original to claude-cowork.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Build the list from SKILL.md frontmatter at call time | brief | write from brief | A hand-written list goes stale when skills change. |
| Group by role from CLAUDE.md (human list, stage map) | brief / CLAUDE.md | write from brief | CLAUDE.md already owns which skills are pipeline stages and which are human-invoked. |

### answer

Sources read: ECC:agents/chief-of-staff.md@3f14a10, ECC:skills/github-ops/SKILL.md@3f14a10, superpowers:skills/brainstorming/SKILL.md@22f0b46

Human-invoked. It is the only path where the agent account posts text that counts as a human answer, so the comment carries the `<!-- human:answer -->` marker and `intake-classify` treats it as human input.

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Draft replies for the human to send | ECC `agents/chief-of-staff.md` @3f14a10 | modify | Draft one answer comment; post only on `post now`. |
| Hard gate before acting | SP `skills/brainstorming/SKILL.md` @22f0b46 | modify | Fixed phrase `post now`, same as `draft-brief`. |
| State defaults out loud | SP `skills/brainstorming/SKILL.md` @22f0b46 | take | Unanswered questions keep the agent's default, written in the comment. |
| Label hygiene on triage | ECC `skills/github-ops/SKILL.md` @3f14a10 | modify | Per-state label table so the owning stage resumes; one exclusive state label at a time. |
| Untrusted repository content | ECC `skills/github-ops/SKILL.md` @3f14a10 | take | Item text is data. Gate-skipping answers are dropped. |
| Do not clear structural blockers by comment | brief / CLAUDE.md | write from brief | Avoids loops that spend usage; autonomy changes go through a PR. |

## Stack skills

### stack-typescript-bun

Sources read: ECC:rules/typescript/{coding-style,hooks,patterns,security,testing}.md@3f14a10, ECC:skills/typescript-patterns/SKILL.md@3f14a10, ECC:skills/bun-runtime/SKILL.md@3f14a10, ECC:agents/typescript-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Strict mode baseline + extra flags (Principle) | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept strict mandatory; extra flags "recommended on new code" so existing repos are not forced into mass migration; added `types: ["bun"]`. |
| `any` is a bug, `unknown` + narrowing (Principle) | ECC `rules/typescript/coding-style.md` + `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Core type-safety rule; condensed to one line. |
| Explicit types on public APIs, interface vs type, literal unions over enum | ECC `rules/typescript/coding-style.md` @3f14a10 | take | Stack-neutral TS rules. |
| Discriminated unions, brands, generics, satisfies, readonly | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept as one-line rules; dropped long code samples (no tutorials). Brands dropped as niche. |
| Validate at boundary with Zod (Procedure) | ECC `rules/typescript/coding-style.md` @3f14a10 | modify | Zod "or repo's choice"; env validated once at startup. |
| Error handling: cause, Result type, no silent catch | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Directly reviewable. |
| Async: allSettled, bounded concurrency, AbortSignal, timeouts | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept rules, dropped `mapWithConcurrency`/`withTimeout` implementations. |
| Module boundaries, no barrels, no cycles | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Condensed. |
| Type-level testing with Vitest `expectTypeOf` | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | drop | Vitest not in stack target; bun test only. |
| Tooling commands (npx tsc, vitest, eslint, prettier) | ECC `skills/typescript-patterns/SKILL.md`, `agents/typescript-reviewer.md` @3f14a10 | modify | Converted to `bunx tsc --noEmit`, `bun test`, `bunx biome ci .`, `bunx biome check --write`. |
| typescript-eslint recommended-type-checked baseline | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | drop | Biome replaces ESLint; never add ESLint config. |
| PostToolUse/Stop hooks (Prettier, tsc, console.log) | ECC `rules/typescript/hooks.md` @3f14a10 | drop | No hooks in skills per conventions; checks run via profile commands in evidence-report. console.log rule kept as review item. |
| Repository pattern, ApiResponse, React custom hooks | ECC `rules/typescript/patterns.md` @3f14a10 | drop | API shape belongs to stack-hono-api; React to stack-nextjs-ui. |
| Secret management via env | ECC `rules/typescript/security.md` @3f14a10 | modify | Uses `Bun.env`/validated env module; added `.env` never committed (Bun auto-loads .env). |
| Playwright E2E / e2e-runner agent reference | ECC `rules/typescript/testing.md` @3f14a10 | drop | Owned by stack-playwright-e2e; agent not adopted. |
| Bun as runtime/pm/test, lockfile, migration-from-Node notes, built-in APIs | ECC `skills/bun-runtime/SKILL.md` @3f14a10 | modify | Bun is mandatory, so "Bun vs Node" choice dropped; kept bun.lock, built-ins, compat caveat, `bun audit` vs `audit fix`. |
| Vercel bunVersion config | ECC `skills/bun-runtime/SKILL.md` @3f14a10 | drop | Deploy target is Docker/Coolify/AWS. |
| Reviewer priorities (security/type/async/error/idioms) | ECC `agents/typescript-reviewer.md` @3f14a10 | modify | Mapped CRITICAL/HIGH/MEDIUM to critical/major/minor checklist; React items dropped (stack-nextjs-ui). |
| Reviewer merge-readiness check + approve/block criteria | ECC `agents/typescript-reviewer.md` @3f14a10 | drop | Owned by review-two-stage; agents never approve. |
| Prompt defense baseline | ECC `agents/typescript-reviewer.md` @3f14a10 | drop | Not a stack concern; covered at agent level. |
| bun test flags, file patterns, bun:test imports, 5000 ms timeout | https://bun.sh/docs/cli/test Bun v1.4.4 | write from docs | Commands and testing section. |
| Biome check/ci/--write/--unsafe/--changed --since | https://biomejs.dev/reference/cli/ Biome v2.x | write from docs | Commands and lint rules. |

### stack-nextjs-ui

Sources read: ECC:rules/react/{coding-style,hooks,patterns,security,testing}.md@3f14a10, ECC:rules/web/{coding-style,design-quality,hooks,patterns,performance,security,testing}.md@3f14a10, ECC:skills/nextjs-turbopack/SKILL.md@3f14a10, ECC:skills/react-patterns/SKILL.md@3f14a10, ECC:skills/frontend-patterns/SKILL.md@3f14a10, ECC:skills/react-testing/SKILL.md@3f14a10, ECC:agents/react-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Server/Client boundary rules (default RSC, `"use client"` line 1, server-only) | ECC `rules/react/patterns.md`, `coding-style.md` @3f14a10 | take | Core App Router correctness. |
| Hooks discipline (top-level, cleanup, no derived state in effect, no default memo) | ECC `rules/react/hooks.md`, `skills/react-patterns/SKILL.md` @3f14a10 | modify | Condensed to rules; dropped ESLint `react-hooks` config (Biome is the linter). |
| State location decision tree, URL as state | ECC `rules/react/patterns.md`, `rules/web/patterns.md` @3f14a10 | take | Short, stack-neutral. |
| React 19 forms (`useActionState`), ref as prop | ECC `skills/react-patterns/SKILL.md`, `rules/react/patterns.md` @3f14a10 | take | Matches shadcn/React 19 baseline. |
| React security (dangerouslySetInnerHTML, URL schemes, NEXT_PUBLIC, Server Action validation, localStorage tokens) | ECC `rules/react/security.md` @3f14a10 | modify | Kept rules; moved into checklist as critical; dropped Vite/CRA/Remix rows and CSP block (repo-specific). |
| `proxy.ts` vs `middleware.ts` naming | ECC `skills/nextjs-turbopack/SKILL.md` @3f14a10 | take | Prevents false review findings. |
| Turbopack/webpack tradeoffs, bundle analyzer | ECC `skills/nextjs-turbopack/SKILL.md` @3f14a10 | drop | Defaults suffice; version-specific tutorial content. |
| Anti-template design policy + component checklist | ECC `rules/web/design-quality.md` @3f14a10 | modify | Condensed; direction comes from the approved design doc, not agent taste. |
| Style direction list (neo-brutalism, glassmorphism...) | ECC `rules/web/design-quality.md` @3f14a10 | drop | Designer decides per design doc; token cost. |
| Web hooks (Prettier/ESLint/tsc PostToolUse hooks) | ECC `rules/web/hooks.md` @3f14a10 | drop | Stack uses Biome; skills must not add hooks; verification via profile commands. |
| CWV targets and bundle budgets | ECC `rules/web/performance.md` @3f14a10 | drop | Global thresholds; not in profile contract. Kept image/font/animation rules only. |
| Compositor-only animation, semantic HTML, tokens via CSS vars | ECC `rules/web/coding-style.md` @3f14a10 | modify | Mapped to Tailwind v4 `@theme` tokens. |
| Frontend code samples (compound components, virtualization, Framer Motion) | ECC `skills/frontend-patterns/SKILL.md` @3f14a10 | drop | Tutorial content; no rules beyond those already kept. |
| RTL query priority, userEvent, findBy, MSW, no snapshots | ECC `skills/react-testing/SKILL.md`, `rules/react/testing.md` @3f14a10 | modify | Applied only if repo already has component tests and per `test_types`; Vitest/Jest commands dropped (Bun). |
| Coverage targets per layer | ECC `skills/react-testing/SKILL.md` @3f14a10 | drop | Coverage comes from profile `coverage_target`/`coverage_paths`. |
| Reviewer severity lanes and approval criteria | ECC `agents/react-reviewer.md` @3f14a10 | modify | Mapped CRITICAL/HIGH/MEDIUM to critical/major/minor; approval stays with humans (Gate 2). |
| Reviewer diagnostic commands (npx eslint, npm audit, prettier) | ECC `agents/react-reviewer.md` @3f14a10 | drop | Replaced with Bun/Biome commands. |
| Tailwind v4 CSS-first setup (`@import "tailwindcss"`, `@tailwindcss/postcss`, no config file) | https://tailwindcss.com/docs/installation/framework-guides/nextjs v4.3 | write from docs | Required stack target; never adopt v3 atoms. |
| shadcn/ui v4 (`tw-animate-css`, OKLCH, `data-slot`, no forwardRef, empty `tailwind.config`) | https://ui.shadcn.com/docs/tailwind-v4, /docs/components-json accessed 2026-11-18 | write from docs | Current shadcn CLI behavior. |
| Next.js with Bun commands | https://bun.com/guides/ecosystem/nextjs Bun 1.x | write from docs | Replace npm/npx. |

### stack-hono-api

Sources read: ECC:skills/api-design/SKILL.md@3f14a10, ECC:skills/backend-patterns/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Resource naming (plural, kebab-case, no verbs) | ECC `skills/api-design/SKILL.md` @3f14a10 | take | Language-agnostic. |
| Method semantics + status code table | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Condensed to one rule line each. |
| Error envelope `{error:{code,message,details}}` | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Default shape; repo's existing shape wins for consistency. |
| Pagination (cursor default, offset for small admin) | ECC `skills/api-design/SKILL.md` @3f14a10 | take | Plus cap on `limit`. |
| Filtering/sorting/sparse fieldset syntax | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Style detail; repo convention decides; token cost. |
| Versioning strategy + breaking-change list | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Kept additive vs breaking; breaking change must appear in PR Risks. Sunset timeline dropped. |
| Rate-limit tiers/headers | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Numbers are product decisions; kept only "shared store" rule from backend-patterns. |
| Next.js, Django, Go implementation examples | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Other frameworks/languages; Hono replaces. |
| API design checklist | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Merged into critical/major/minor review checklist. |
| Repository/service layering, thin handlers | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Kept as structure rule; Supabase sample dropped. |
| Middleware pattern (withAuth HOF) | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Replaced with Hono `createMiddleware` + built-in middleware. |
| Centralized error handler | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Replaced with `HTTPException` + `app.onError`. |
| N+1, transactions, query optimization | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | drop | Owned by stack-prisma-postgres. |
| Redis caching, job queue, retry backoff, structured logger | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | drop | Not core to Hono routing; in-memory queue unsafe in containers; logger rule in stack-typescript-bun. |
| JWT/RBAC examples | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Kept "auth by default, ownership 403" rule; implementation via `hono/jwt`/`bearer-auth`. |
| Rate limiting must use shared store | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | take | Correct for multi-replica Coolify deploys. |
| Validator, zValidator, c.req.valid, Content-Type + lowercase header gotchas | https://hono.dev/docs/guides/validation Hono v4 | write from docs | Validation section. |
| app.request() tests, testClient + chained routes | https://hono.dev/docs/guides/testing, https://hono.dev/docs/helpers/testing Hono v4 | write from docs | Testing + structure sections. |
| HTTPException, getResponse, onError | https://hono.dev/docs/api/exception Hono v4 | write from docs | Errors section. |
| RPC `hc<AppType>`, Bun entry, built-in middleware names | Hono v4 docs (rpc, getting-started/bun) not re-fetched | write from docs | Marked in References as not re-fetched; verify against installed version. |

### stack-prisma-postgres

Sources read: ECC:skills/prisma-patterns/SKILL.md@3f14a10, ECC:skills/postgres-patterns/SKILL.md@3f14a10, ECC:skills/database-migrations/SKILL.md@3f14a10 (+ examples/*.sql listed, not adopted), ECC:agents/database-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Check Prisma version first | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Turned into a gate: pinned version only, never `prisma@latest`; Prisma 8 → `ai:needs-human` with default. |
| `migrate dev` can reset DB; deploy in CI | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | `migrate dev` only on disposable DB; production `migrate deploy` only via Gate 3 (agents never). |
| Never edit applied migration (checksum) | ECC `skills/prisma-patterns/SKILL.md`, `skills/database-migrations/SKILL.md` @3f14a10 | take | Integrity; fix forward. |
| Expand/contract multi-step | ECC `skills/database-migrations/SKILL.md` @3f14a10 | modify | Condensed 7-step SQL walkthrough to 4 steps; long SQL dropped. |
| Destructive migration definition + PR Risks flag | Conventions (PR template) | modify | Added explicit list + Risks/Rollback requirement; missing Risks = critical. |
| CREATE INDEX CONCURRENTLY via `--create-only` | ECC `skills/database-migrations/SKILL.md` @3f14a10 | take | Prisma cannot generate it; noted no-transaction constraint. |
| Schema/data migrations separate; forward-only prod | ECC `skills/database-migrations/SKILL.md` @3f14a10 | take | Core principles. |
| Drizzle, Kysely, Django, golang-migrate workflows | ECC `skills/database-migrations/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Self-checking SQL fixtures (examples/*.sql) | ECC `skills/database-migrations/examples/` @3f14a10 | drop | Require psql against a DB; token cost; principle kept. |
| ID strategy, include vs select, DTO mapping | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Repo strategy wins; condensed. |
| Transactions (array vs interactive, tx only, 5 s timeout, no external calls) | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | Common real bugs. |
| Traps: updateMany count, @updatedAt skip, deleteMany no where, soft delete findFirstOrThrow | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | One line each. |
| Error codes P2002/P2025/P2003 | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | Maps to Hono 409/404. |
| Singleton client, serverless connection_limit=1 | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Singleton kept; serverless/Vercel specifics dropped (Docker/Coolify target). |
| Index cheat sheet, composite order, FK indexes | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | modify | Kept as rules; partial/GIN/BRIN via raw SQL migration. |
| Data types (bigint, text, timestamptz, numeric) | ECC `skills/postgres-patterns/SKILL.md` @3f14a10 | modify | Expressed in Prisma terms; repo convention wins. |
| RLS / `auth.uid()` policies | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | drop | Supabase-specific; not in stack target. |
| ALTER SYSTEM config template, pg_stat diagnostics | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | drop | Ops on shared DB; agents must not touch; out of PR scope. |
| SKIP LOCKED queues, lock ordering, short transactions | ECC `agents/database-reviewer.md` @3f14a10 | modify | Kept lock ordering + short tx; queue pattern dropped as niche. |
| Reviewer checklist | ECC `agents/database-reviewer.md` @3f14a10 | modify | Merged into critical/major/minor checklist. |
| Prisma 8 RC replaces migrate/generate with `prisma db migrate` | https://www.prisma.io/docs (accessed 2026-11-18, Prisma 8 RC) + upgrade guide | write from docs | Used only to add a version gate; not adopted. |
| Prisma + Bun guide | https://www.prisma.io/docs/guides/runtimes/bun (accessed 2026-11-18) | write from docs | Describes Prisma 8 flow; not adopted; noted in References. |

### stack-playwright-e2e

Sources read: ECC:skills/e2e-testing/SKILL.md@3f14a10, ECC:agents/e2e-runner.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Activation for every E2E-capable repo | ECC `agents/e2e-runner.md` @3f14a10 ("use proactively") | modify | Gated on profile `test_types` including `e2e`. |
| Agent Browser as primary tool | ECC `agents/e2e-runner.md` @3f14a10 | drop | Not in stack target; global npm install in ephemeral containers. |
| `data-testid` > CSS > XPath locator priority | ECC `agents/e2e-runner.md`, `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Replaced with official role-first locators; testid as last resort. |
| Wait for conditions, never `waitForTimeout` | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Core flake prevention. |
| `waitForLoadState('networkidle')` as fix | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | Official docs discourage; use web-first assertions. |
| Test isolation, no shared state | ECC `agents/e2e-runner.md` @3f14a10 | take | Matches official guidance. |
| Page Object Model always | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Only when 2+ tests share a flow. |
| Config template (multi-browser, retries 2, reporters, `npm run dev` webServer) | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | Repo config is authority; versions follow repo. |
| Trace on first retry, screenshot/video on failure | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Traces on failure only. |
| Quarantine via `test.fixme`/`test.skip` by agent | ECC `skills/e2e-testing/SKILL.md`, `agents/e2e-runner.md` @3f14a10 | modify | Quarantine needs human (`ai:needs-human`); never skip to get green (integrity). |
| `--repeat-each=10` flake detection | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | take | Evidence before claims. |
| `--headed`, `--debug`, `show-report` | ECC `agents/e2e-runner.md` @3f14a10 | drop | No display in cloud sessions. |
| GitHub Actions E2E workflow (setup-node, npm ci) | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | CI is repo-owned; Node/npm not in stack. |
| E2E test report template | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | drop | evidence-report skill owns reporting. |
| Wallet/Web3 and financial flow examples | ECC `skills/e2e-testing/SKILL.md` @3f14a10 | modify | Kept only "never run against production". |
| Success metrics (95% pass, <5% flaky) | ECC `agents/e2e-runner.md` @3f14a10 | drop | Global thresholds; any flake is reported. |
| Role locators, web-first assertions, auth via setup project, install only needed browsers | https://playwright.dev/docs/best-practices accessed 2026-11-18 | write from docs | Official guidance; `bunx` instead of `npx`. |

### stack-deploy

Sources read: ECC:skills/docker-patterns/SKILL.md@3f14a10, ECC:skills/deployment-patterns/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Multi-stage Dockerfile (deps/build/runtime) | ECC `skills/deployment-patterns/SKILL.md`, `docker-patterns/SKILL.md` @3f14a10 | modify | Rebased on `oven/bun` with `bun install --frozen-lockfile [--production]`. |
| Node/Go/Python Dockerfiles | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Pinned tags, non-root user, dependency-first layer order, .dockerignore | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | take | Core hardening; `USER bun` from official image. |
| HEALTHCHECK with wget | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Slim Bun image lacks wget; use a tool present in the image. |
| No secrets in image/compose | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | take | Integrity. |
| Compose local dev stack with healthchecked DB | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | modify | Kept as local/test only; dropped Redis/Mailpit samples. |
| Compose security (no-new-privileges, cap_drop, read_only) | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | modify | Condensed to one rule. |
| Hardened CLI installer harness, Codex OAuth relay | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | drop | ECC-specific; unrelated to app deploy. |
| Rolling/blue-green/canary strategies | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Coolify handles rollout; humans own Gate 3. |
| CI/CD pipeline with deploy-to-production job | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Agents never deploy production (Gate 3). |
| Kubernetes probes | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Env config validation at startup (zod) | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Kept as fail-fast rule; schema lib per repo. |
| Rollback checklist, backward-compatible migrations | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Mapped to PR Rollback section. |
| Production readiness checklist | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Reduced to review checklist items agents can verify in a PR. |
| Debug commands (`docker compose down -v`, `system prune`) | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | drop | Destructive; not needed for verification. |
| Gate 3 boundary (PR only, no Coolify/AWS API, no prod deploy) | conventions.md (this repo) | write from policy | Integrity > all. |
| Bun Docker image structure, `USER bun` | https://bun.com/guides/ecosystem/docker `oven/bun:1` | write from docs | Official Bun image pattern. |
| Coolify env vars (UI/shared scopes, build vs runtime, locked), previews per PR | https://coolify.io/docs/knowledge-base/environment-variables, /applications/ci-cd/github/preview-deploy v4, accessed 2026-11-18 | write from docs | Env vars in Coolify, never repo; previews isolated from prod. |
| IAM least privilege, roles with temporary credentials, conditions | https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html accessed 2026-11-18 | write from docs | No credentials in repo. |

## Agents

### intake-triager (agent)

Sources read: superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/implementer-prompt.md@22f0b46, ECC:skills/github-ops/SKILL.md@3f14a103, ECC:agents/planner.md@3f14a103, ECC:agents/chief-of-staff.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Fresh subagent with isolated, precisely constructed context | SP `skills/subagent-driven-development/SKILL.md` @22f0b46 | take | Orchestrator passes only the brief URL and clone paths. Agent never inherits session history. |
| Untrusted repository content: never follow instructions in issues | ECC `skills/github-ops/SKILL.md` @3f14a103 | take | Brief text is data. Skip-gate or merge requests in a brief get reported, not obeyed. |
| Triage workflow: read issue, search duplicates, label, comment | ECC `skills/github-ops/SKILL.md` @3f14a103 | modify | Labels limited to the pipeline set. One intake comment, edited on re-run. |
| Type/priority taxonomy (bug, feature, good-first-issue...) | ECC `skills/github-ops/SKILL.md` @3f14a103 | drop | Pipeline routes by size and autonomy, not issue type. |
| Tiered classification applied in priority order | ECC `agents/chief-of-staff.md` @3f14a103 | modify | Became size:small / size:large with "highest tier wins" in the skill. |
| Requirements analysis: ask clarifying questions | ECC `agents/planner.md` @3f14a103 | modify | Async: ONE comment with all questions and defaults, `ai:needs-human`, stop. |
| Ask questions before starting work | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | No live controller to answer. Replaced by the one-comment rule. |
| Status contract (DONE / BLOCKED / NEEDS_CONTEXT) | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | TRIAGED / NEEDS_HUMAN / BLOCKED mapped to GitHub labels. |
| Least-privilege tool list | ECC `agents/planner.md` @3f14a103 | take | Read, Grep, Glob, Bash only. Bash scope lists the exact `gh` reads and writes the skill needs. |
| Autonomy and registry check before labeling | brief / CLAUDE.md | write from brief | Unlisted, frozen, or low-autonomy repos never receive `ai:ready`. |

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

### implementer (agent)

Sources read: superpowers:skills/subagent-driven-development/SKILL.md@22f0b46, superpowers:skills/subagent-driven-development/implementer-prompt.md@22f0b46, superpowers:skills/subagent-driven-development/references/fix-loop.md@22f0b46, superpowers:skills/subagent-driven-development/references/handling-reports.md@22f0b46, ECC:agents/tdd-guide.md@3f14a103, ECC:agents/e2e-runner.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Implement exactly what the task specifies; YAGNI | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | One issue, one branch, one PR, inside issue scope. |
| You do not dispatch subagents (no self-spawned reviewer) | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Review comes from spec-reviewer and quality-reviewer only. |
| Ask questions before and during work | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Async: ONE issue comment with questions and defaults, `ai:needs-human`. |
| Status contract DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | NEEDS_CONTEXT became NEEDS_HUMAN with a GitHub label. |
| Report file with RED/GREEN evidence | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | modify | Evidence goes into the PR body template, not a local report file. Containers are ephemeral. |
| Self-review before reporting | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Step 6 checks criteria coverage, scope, and patterns. |
| Fix round: re-run covering tests, append fix evidence | SP `skills/subagent-driven-development/references/fix-loop.md` @22f0b46 | modify | Evidence appended to the PR. Cap = `max_fix_attempts` from policy, then `ai:blocked`. |
| Fix-loop model escalation at rounds 4-5 | SP `skills/subagent-driven-development/references/fix-loop.md` @22f0b46 | drop | Orchestrator does not pick models per round; the cap stops the loop. |
| Escalate on architectural decisions | SP `skills/subagent-driven-development/implementer-prompt.md` @22f0b46 | take | Return NEEDS_HUMAN with the options. |
| RED-GREEN-REFACTOR cycle | ECC `agents/tdd-guide.md` @3f14a103 | take | Owned by the `tdd` skill; agent preloads it. |
| npm test / 80% coverage | ECC `agents/tdd-guide.md` @3f14a103 | modify | Commands and coverage come from `.agent/profile.yml`. Bun replaces npm. |
| Agent Browser primary, Playwright fallback | ECC `agents/e2e-runner.md` @3f14a103 | drop | Playwright only, via the `stack-playwright-e2e` pack when listed. |

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

### quality-reviewer (agent)

Sources read: superpowers:skills/subagent-driven-development/task-reviewer-prompt.md@22f0b46, ECC:agents/code-reviewer.md@3f14a103, ECC:agents/security-reviewer.md@3f14a103, ECC:agents/typescript-reviewer.md@3f14a103, ECC:agents/react-reviewer.md@3f14a103, ECC:agents/database-reviewer.md@3f14a103, ECC:agents/e2e-runner.md@3f14a103

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Pre-report gate (exact line, failure mode, context, defensible severity) | ECC `agents/code-reviewer.md` @3f14a103 | take | Step 6. Fail any answer: downgrade or drop. |
| HIGH/CRITICAL require snippet, scenario, why guards miss it | ECC `agents/code-reviewer.md` @3f14a103 | take | Applied to critical findings. |
| Zero findings is valid; common false positives list | ECC `agents/code-reviewer.md` @3f14a103 | modify | Kept the principle; detailed false-positive list lives in `review-two-stage`. |
| Merge readiness: report failing/pending checks first | ECC `agents/typescript-reviewer.md` @3f14a103 | modify | Reported as a finding via `gh pr checks`; no re-runs. |
| Run eslint / prettier / npm audit | ECC `agents/typescript-reviewer.md` @3f14a103 | drop | Biome and CI own lint. Reviewer reads CI output instead of running tools. |
| OWASP Top 10 and security pattern table | ECC `agents/security-reviewer.md` @3f14a103 | modify | Security reviewed first; checklist sits in the skill and packs. |
| Alert owner and rotate secrets on critical | ECC `agents/security-reviewer.md` @3f14a103 | drop | Reviewer is read-only; orchestrator posts the critical finding and humans rotate. |
| React hooks, RSC boundary, a11y checks | ECC `agents/react-reviewer.md` @3f14a103 | modify | Moved to `stack-nextjs-ui` pack checklist, loaded only when listed in `packs`. |
| Index FKs, timestamptz, short transactions | ECC `agents/database-reviewer.md` @3f14a103 | modify | Moved to `stack-prisma-postgres`. RLS / `auth.uid()` dropped (Supabase-specific). |
| Wait for conditions, not time; flaky quarantine | ECC `agents/e2e-runner.md` @3f14a103 | modify | Moved to `stack-playwright-e2e` review checklist. |
| Do not re-run tests; one focused test only on specific doubt | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | take | No installs, builds, migrations, or full suite. |
| Read-only, no posting, no labels | SP `skills/subagent-driven-development/task-reviewer-prompt.md` @22f0b46 | modify | Enforced with `disallowedTools`; orchestrator posts findings and sets labels. |

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

