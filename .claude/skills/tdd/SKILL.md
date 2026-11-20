---
name: tdd
description: Test-first implementation for one ai:ready issue. Write a test, watch it fail for the right reason, write the minimum code to pass, and record one RED and one GREEN commit per behavior with output excerpts.
when_to_use: Use before writing any production code, including bug fixes and fix rounds.
disable-model-invocation: false
model: opus
effort: high
metadata:
  version: "1.2.0"
  owner: claude-cowork
---
# TDD

## Purpose

Prove every behavior change with a test that failed first. A test you never saw fail proves nothing. This skill owns how the implementer writes code. `evidence-report` owns the final verification and the PR body.

## The iron law

```
NO PRODUCTION CODE WITHOUT A TEST THAT FAILED FIRST, FOR THE RIGHT REASON
```

Production code written before its test gets deleted and redone. Do not keep it as reference. Do not adapt it while writing the test. Remove it (`git restore <file>` or delete the new file), then start from the test.

## When to use / not use

Use for:
- New behavior, bug fixes, behavior-changing refactors.
- Fix rounds after review (`ai:changes-needed`): a finding about behavior gets a failing test first.

Skip TDD only for (write `n/a: <reason>` in the evidence):
- Docs, comments, or typos on a `Trivial: yes` issue.
- Pure config, generated code, or lockfile changes with no behavior.

Never skip because the change "is too small". Small code breaks too.

## Inputs

- The issue: acceptance criteria and "Required tests".
- The linked design doc's test strategy, if any.
- `.agent/profile.yml`: `commands.test`, `test_types`, `coverage_target`, `coverage_paths`, `packs`.
- Stack packs from `packs` for test conventions and runner details.

## Rules from the profile

- **Runner.** Always run `commands.test`. Never swap in another runner. You may append a file path filter while iterating (e.g. `bun test src/order.test.ts`). The final GREEN check runs `commands.test` unfiltered.
- **Test types.** Write only types listed in `test_types`. No E2E unless `e2e` is listed. If a behavior needs an unlisted type, use the closest listed type and record the gap under Risks in the PR.
- **Coverage.** No global target. If `coverage_target` is a number and `coverage_paths` is non-empty, check line coverage for those paths only (e.g. `bun test --coverage`). Otherwise there is no numeric target. Never add tests just to raise a number.
- `commands.test` is `""`: stop. Return `BLOCKED` with `limit: no test command`. Do not comment or label: the orchestrator adds `ai:needs-human` (`CLAUDE.md` -> "Hard limits and errors").

## Procedure

Repeat steps 1–6 for each behavior in the acceptance criteria. One behavior per cycle.

1. **Name the break.** Before writing the test, state the production change that should make it fail. Cannot name one: redesign the test around an observable result. Only an intentional decision (a constant, exact wording) would fail it: test the behavior that depends on the decision instead.

2. **RED: write one minimal test.** One behavior, a name that states it, real code under test. Expected values are hand-written literals or fixtures, never computed by the code under test.

3. **Verify RED.** Run the test. Confirm:
   - It fails. A runtime failure is best.
   - The message shows the missing behavior, not a typo, setup error, or missing dependency.
   - A "missing export/symbol" error counts as RED only if it names exactly the symbol this cycle adds.

   Passes immediately: you are testing existing behavior. Fix the test. Errors for another reason: fix the test setup and re-run.

4. **Commit RED.** Stage only test files.
   ```bash
   git add <test files>
   git commit -m "test(<scope>): <behavior> [RED]"
   ```
   Append the excerpt to the evidence file (see Evidence).

5. **GREEN: write the minimum code** that passes this test. No extra options, no refactor of unrelated code, no features the test does not demand. Run the test. If it fails, fix the code, not the test. Then run the full `commands.test`. Fix any test you broke now.
   ```bash
   git add <production files>
   git commit -m "feat(<scope>): <behavior> [GREEN]"   # fix(<scope>) for a bug
   ```
   Append the GREEN excerpt to the evidence file.

6. **Refactor** (optional). Remove duplication, improve names. Add no behavior. Tests stay green. Commit as `refactor(<scope>): <what>`.

7. **Finish.** Run `commands.test` unfiltered once more. Run the coverage check if the profile sets one. Then hand over to `evidence-report`. Report every failing test by name, including failures you did not cause.

## Test rules

- **Real behavior.** Assert outputs, state, and side effects of the real code. Never assert that a mock was rendered or exists.
- **Mocks only at system boundaries:** network calls, time and timers, external services (payment, email, third-party APIs). Keep everything inside the process real. Use the database for real when `integration` is in `test_types`; follow the stack pack.
- **Mock the complete shape** of a boundary response, not only the fields the test reads.
- **No test-only methods** in production code. Cleanup helpers live in test utilities.
- **Independent tests.** Each test sets up its own data. No order dependence.
- **Mutation check** before finishing: for each realistic mutation (wrong constant, wrong branch, missing side effect, empty return, missing validation for empty, null, unauthorized, or malformed input) at least one test fails.
- **Pristine output.** Warnings and stray logs in test output are defects. Fix them.

## Evidence

Containers are ephemeral. Keep evidence in three places:

1. **Commits** (durable): the `[RED]` and `[GREEN]` commits on the branch.
2. **Local file** outside the repo working tree: `"${TMPDIR:-/tmp}/evidence-<issue>.md"`. Never commit it.
3. **PR body draft**: paste the same blocks into the RED/GREEN evidence section when `evidence-report` builds the body.

One block per behavior. Keep each excerpt short: the command, the failing assertion or error line, and the summary line.

````markdown
### <behavior>
RED `<sha7>` — `bun test src/order.test.ts`
```text
(fail) order total > applies discount to subtotal
  Expected: 90
  Received: 100
 0 pass  1 fail
```
GREEN `<sha7>` — `bun test`
```text
 42 pass  0 fail
```
````

## Outputs

- Per behavior: one `[RED]` commit with tests only, one `[GREEN]` commit with production code, optional `refactor` commit.
- `"${TMPDIR:-/tmp}/evidence-<issue>.md"` with RED/GREEN excerpts.
- A green unfiltered `commands.test` run.

## Stop conditions

- All acceptance criteria have a GREEN test and the full suite passes: hand over to `evidence-report`.
- The criterion is ambiguous: apply `CLAUDE.md` → "Decide by default". Pick the reading that matches existing code and decisions, test that, and record it under Assumptions for the PR body.
- A tier 3 item: record it under "Decisions for the reviewer" for the PR and continue (`CLAUDE.md` -> "Continue when a gate follows").
- You cannot write a failing test for a criterion even after that, or a wrong guess on a tier 3 item is irreversible or invalidates most of the work: post nothing. Return `NEEDS_HUMAN` with `escalations:` to the orchestrator.
- A test stays red when fix attempts reach the cap (`CLAUDE.md` -> "Stop cleanly", implementation loop): follow `evidence-report` step 8. It owns the draft PR, the `ai:blocked` label, and the one comment.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "Too simple to test." | Simple code breaks. The test takes a minute. |
| "I'll write the tests after." | Tests written after pass at once and prove nothing. |
| "I already wrote the code; I'll keep it as reference." | You will adapt it. Delete it and start from the test. |
| "Deleting hours of work is wasteful." | Sunk cost. Untrusted code is the waste. |
| "I tested it manually." | Manual checks leave no record and cannot re-run. |
| "Mocking the database is faster." | Inside the process stays real. Mock only network, time, external services. |
| "The criterion could mean two things. I'll ask." | Pick the reading that fits the code and decisions. Record it. Gate 2 catches a wrong pick. |
| "The test passed on the first run, good." | A test that never failed proves nothing. Make it fail first. |
| "One commit for test and code is cleaner." | Reviewers need the RED commit to see the test failed without the code. |

Adapted from obra/superpowers and affaan-m/ECC (MIT). See docs/blend-decisions.md.
