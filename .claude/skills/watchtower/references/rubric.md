# Watchtower review rubric

The audit script catches mechanical drift. This rubric covers what needs judgment.
Report a finding only with a `path:line` and a quote that proves it. Drop anything you cannot point to.

Severity:
- `error`: an agent following the text does the wrong thing, or two rules contradict.
- `warn`: drift, a gap, or wording an agent can misread.
- `suggest`: an improvement. Not broken today.

## Skills (`.claude/skills/*/SKILL.md`)

1. **Trigger.** The description says what the skill does, in the third person, with no trigger sentence. `when_to_use` says when to use it and when not to (`Use when ...`, `Never use ...`). A human's likely phrasing (often Indonesian) triggers it. It does not overlap another skill's trigger.
2. **One owner.** The skill does one stage or one human task. It does not repeat a procedure another skill owns. It links instead.
3. **Procedure.** Numbered steps an agent can follow without guessing. Every command is complete. Every input has a source.
4. **Stops.** Stop conditions cover the failure paths: missing access, empty input, usage pause, hard limits.
5. **Anti-rationalization.** The table names the shortcuts an agent is likely to take for this task, not generic ones.
6. **Outputs.** The skill says what it writes (GitHub, files, chat) and what it never writes.
7. **Progressive disclosure.** Long templates and reference detail live in `references/`. The body stays the procedure.
8. **Scripts.** Deterministic work (parsing, grouping, formatting) lives in a tested script, not in prose.
9. **Language.** Concise technical English. The chat reply language matches `CLAUDE.md`.
10. **Frontmatter values.** The script checks presence and types (required: `name`, `description`, `when_to_use`, `disable-model-invocation`, `model`, `effort`; stack packs skip `model` and `effort`). Review whether the values fit the skill:
    - `effort` follows the stage weight in `CLAUDE.md` -> "Usage budget": heavy stages and judgment reviews `high`, light stages `medium`, read-only chat lookups `low`.
    - `model` names the smallest model that does the job. Never `inherit` or `default`. Skills that reason (design, planning, triage, task review, code review, implementation, audits, drafting from a human's intent) use `opus`. Mechanical skills (run a script, format output, list items) may use `sonnet` or `haiku`.
    - The skill's `model` and `effort` apply to the rest of the invoking turn. A skill the orchestrator invokes inside a pipeline run (for example `usage-status` before each delegation, `review-two-stage`, `pr-watch`) uses `opus` and `high`, or it downgrades the rest of the run.
    - `disable-model-invocation: true` fits a human skill with side effects that must not start from casual phrasing. It removes the description from context and blocks agent preload.
    - A read-only skill names its write tools in `disallowed-tools`. A skill that runs its own script scopes `allowed-tools` with `${CLAUDE_SKILL_DIR}`.

## Agents (`.claude/agents/*.md`)

1. The tool list is the minimum. Reviewers and the task reviewer have no write tools.
2. The input list matches what the orchestrator passes in the skill and in `docs/scheduled-tasks.md`.
3. The output format matches what the orchestrator parses (`PASS`, `CHANGES`, `NEEDS_HUMAN` with `escalations:`).
4. The agent does not post escalations or set `ai:needs-human` (CLAUDE.md "Escalation flow").

## Workflows

Scope: the scheduled-task prompts in `docs/scheduled-tasks.md`, the stage map in `CLAUDE.md`, `pr-watch`, `run-pipeline`, `.github/workflows/`, and the state machine in `docs/labels-and-states.md`.

1. **Coverage.** Every label state has a phase that moves it forward. No item can sit forever without showing in `inbox` or `pipeline-status`.
2. **Order.** Light stages run before heavy ones. Usage checks sit before each delegation and before review stage 2.
3. **Re-entry.** A rerun of the same phase is idempotent: markers (`<!-- ai:... -->`) prevent duplicate comments and issues.
4. **Merge path.** A human merge reaches the next step without a human message (pr-watch). Planning promotion follows a closed sub-issue.
5. **Prompt sync.** The batch and onboarding prompts in `docs/scheduled-tasks.md` match the skills they call. A changed prompt names the manual copy step into the scheduled task.
6. **GitHub workflows.** Least-privilege permissions, pinned actions, timeouts, and no secrets in logs. `project-sync.yml` mirrors only labels.

## Rules (`CLAUDE.md`, `registry/policy.yml`, `docs/labels-and-states.md`)

1. **No contradictions.** Two rules never give different answers for the same case. Check `CLAUDE.md` against each skill that restates a rule.
2. **Single source.** A number (limits, thresholds, fix cap) lives in `registry/policy.yml`. Prose names the key, not a copy of the value.
3. **Enforceable.** Each "never" rule has a layer that enforces it: the platform, the hook, settings `deny`, or a reviewer step. Name the rules that rely on instructions only.
4. **Escalation.** The tier rules in "Decide by default" are restated nowhere else with different wording.
5. **Size.** `CLAUDE.md` stays a router. A procedure in it belongs in a skill.

## Hooks (`.claude/hooks/`, `.claude/settings.json`)

1. Each blocked pattern has a test in `tests/test_guard_bash.py`.
2. The hook fails open on its own errors and says so on stderr. Check that the fail-open paths are the ones intended.
3. Bypass forms: `bash -c`, `env`, `sudo`, subshells, `;`, `&&`, heredocs, quoted branch names, refspecs (`HEAD:main`, `+main`).
4. The hook sees Bash only. MCP tools that merge, approve, or change protection need a `deny` rule.
5. Repo hooks do not load in multi-repo cloud sessions (`docs/open-questions.md` Q4). Rules that rely only on the hook carry that risk.

## Consistency

1. The same name, label, path, and command are spelled the same everywhere.
2. `README.md`, `docs/architecture.md`, and `docs/setup.md` describe the current skill set and flow.
3. Every skill and agent has a `docs/blend-decisions.md` entry and an attribution line.
4. Skills that cite another skill's step (`docs/scheduled-tasks.md B5`) still point to a step that exists.

## Improvement suggestions

Rank by value to the pipeline: fewer human stops, fewer wasted runs, fewer wrong actions.
Each suggestion names the files to change, the change in one line, and the risk.
At most five. Skip a suggestion that only restyles text.
