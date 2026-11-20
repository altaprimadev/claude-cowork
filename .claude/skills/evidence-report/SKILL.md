---
name: evidence-report
description: Run the repo profile's install, lint, typecheck, test, and build commands, capture real output, and fill the PR body sections (Summary, Related issue, RED/GREEN evidence, Verification output, Risks, Rollback).
when_to_use: Use after `tdd` finishes and before opening or updating an agent PR, and again after every fix round.
disable-model-invocation: false
model: opus
effort: high
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Evidence Report

## Purpose

No claim without output. This skill turns a finished change into a PR whose body proves what it says. It owns verification and the PR body for the implementer. It never approves or merges anything.

## The iron law

```
NO "PASSING", "DONE", OR "FIXED" WITHOUT FRESH COMMAND OUTPUT IN THE PR
```

Fresh means run in this session, on the current HEAD, after the last code change. An earlier run, a subagent's claim, or "should pass" is not evidence.

## When to use / not use

Use when:
- `tdd` reports all behaviors GREEN and you are about to open the PR.
- A fix round changed code on an existing PR.

Do not use to:
- Review someone else's PR. That is `review-two-stage`.
- Verify staging or production. Agents never deploy to production (Gate 3). Staging verification is out of scope; say "not performed" if the issue asks for it.

## Inputs

- Target repo clone on the feature branch, PR base branch known.
- `.agent/profile.yml` -> `commands.{install,lint,typecheck,test,build}`, `coverage_target`, `coverage_paths`.
- `registry/policy.yml` -> `max_fix_attempts`.
- The issue (acceptance criteria) and linked design doc.
- `"${TMPDIR:-/tmp}/evidence-<issue>.md"` from `tdd`. If it is gone (new container), rebuild RED/GREEN from the `[RED]`/`[GREEN]` commits: `git worktree add "$TMPDIR/red-<sha7>" <red-sha>`, run `commands.install` and the test there, capture, remove the worktree. Repeat for GREEN. If you cannot reproduce RED, say so; do not invent it.
- PR template: the target repo's `.github/pull_request_template.md`, else the control repo's.

## Procedure

1. **Run each command in order:** install, lint, typecheck, test, build. Skip a command whose value is `""` and record `not configured`. Run from the repo root and keep the full log outside the repo.
   ```bash
   set -o pipefail
   OUT="${TMPDIR:-/tmp}/verify-<issue>"; mkdir -p "$OUT"
   bash -c "<commands.lint>" > "$OUT/lint.log" 2>&1; echo "exit=$?" >> "$OUT/lint.log"
   ```
   Run all five even if one fails. Later failures matter too. If install fails, the rest are unreliable: record them as `not run: install failed`.

2. **Read the output.** Check the exit code. Count failures and warnings. A warning in test output is a defect to fix, not to hide.

3. **Coverage** (only if `coverage_target` is a number and `coverage_paths` is non-empty): run the test command with coverage and report line coverage for those paths only. Below target is a failure. No target set: write `no coverage target`.

4. **Check the diff.**
   ```bash
   git diff --stat origin/<base>...HEAD
   git diff origin/<base>...HEAD | grep -nE '(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=]|password\s*[:=]|BEGIN [A-Z ]*PRIVATE KEY)' || true
   ```
   Every changed file must belong to the issue. Revert unrelated changes. A possible secret is a failure: remove it and note it in Risks.

5. **Check requirements line by line.** For each acceptance criterion, name the test or output that proves it. A criterion without proof is not met, even if all commands pass.

6. **On any failure, fix and repeat.** Fix the cause (follow `tdd` for behavior fixes; use the repo's own formatter for format errors, e.g. `bunx biome check --write .`). Commit the fix. Re-run every command from step 1. Count each full re-run as one attempt. Stop when attempts reach the cap (`CLAUDE.md` -> "Stop cleanly", implementation loop).

7. **Build the PR body** in `"${TMPDIR:-/tmp}/pr-body-<issue>.md"` with the template sections below. Then:
   ```bash
   gh pr create --repo <owner/repo> --base <base> --head <branch> \
     --title "<type>(<scope>): <issue title>" --body-file "$TMPDIR/pr-body-<issue>.md"
   # existing PR (fix round):
   gh pr edit <pr> --repo <owner/repo> --body-file "$TMPDIR/pr-body-<issue>.md"
   ```
   At the attempt cap, keep the output in a draft PR so it survives the container: a new PR with `gh pr create --draft`, an existing one with `gh pr ready <pr> --undo`.

8. **On the cap:** add `ai:blocked` to the issue and the PR. Post one comment with the failing command, the exit code, and the failing output excerpt. Stop. Do not change other pipeline labels.

## Output rules

- Paste real output only. Never edit, reorder, or summarize it into a different meaning.
- **Passing command:** keep the command line, the exit code, and the last lines that carry the summary (about 20 lines). Mark cuts with `[... N lines truncated ...]`.
- **Failing command:** keep every error and failing test name, the first stack frame per error, and the summary. Cut only repeated noise. Cap at about 200 lines per command and say where the full log lives.
- **Test:** always include the pass/fail/skip counts line.
- Strip secrets and tokens from any output before posting.
- Never write "passes" in prose when a command was skipped, not configured, or failed.

## PR body template

````markdown
## Summary
- <what changed and why, 1-5 bullets>
- Acceptance criteria:
  - [x] <criterion> — proven by `<test name>` / <command>
  - [ ] <criterion> — not met: <reason>

## Related issue
Closes #<n>. Design: `docs/design/<file>.md` (size:large only).

## RED/GREEN evidence
<one block per behavior from the evidence file: RED sha + excerpt, GREEN sha + excerpt>
<or "n/a: <reason>" for docs-only or trivial changes>

## Verification output
Fix attempts: <k>/<max_fix_attempts>. HEAD: `<sha7>`.

### Lint
```text
$ <command>
<excerpt>
exit=0
```
### Typecheck
### Test
<include counts and coverage for coverage_paths, or "no coverage target">
### Build
<"not configured" when the command is "">

## Risks
- <migrations, auth, data, performance, config, test-type gaps, unverified criteria>

## Rollback
- <revert the PR; migration down steps or "no migration"; flag to toggle>
````

Install output goes under Verification output only when it failed or warned.

## Outputs

- PR opened or updated with every template section filled from real output.
- Full logs in `"${TMPDIR:-/tmp}/verify-<issue>/"` (ephemeral).
- On the cap: draft PR, `ai:blocked`, one comment with the failing output.

## Stop conditions

- All configured commands exit 0, every criterion has proof, PR body posted: done. Return the one-line evidence summary (e.g. `lint ok, typecheck ok, 42/42 tests, build ok, build not configured`).
- `max_fix_attempts` reached: `ai:blocked`, stop.
- A failure needs a decision outside the issue scope (dependency upgrade, CI change): post nothing. Return `NEEDS_HUMAN` with `escalations:` (Decision, Recommend, Alternatives, Checked, If no answer). The orchestrator vets it (`CLAUDE.md` → "Decide by default").

## Anti-rationalization

| Thought | Reality |
|---|---|
| "It should pass now." | Run it. Paste the output. |
| "Lint passed, so the build is fine." | Lint is not the compiler. Run the build. |
| "Typecheck is slow; tests cover it." | Run every configured command. |
| "This failure is pre-existing." | Report it by name with output. Silence is a false claim. |
| "The output is long; I'll summarize it as passing." | Paste the summary lines. A summary without output is a claim. |
| "One more attempt will fix it." | At the cap (`CLAUDE.md` -> "Stop cleanly"), stop and label `ai:blocked`. |
| "The evidence file is gone; I remember the RED output." | Memory is not output. Re-run from the commits or say it is missing. |

Adapted from obra/superpowers and affaan-m/ECC (MIT). See docs/blend-decisions.md.
