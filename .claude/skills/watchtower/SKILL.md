---
name: watchtower
description: Audit and review the claude-cowork control repo itself - skills, agents, scheduled-task workflows, GitHub workflows, rules in CLAUDE.md and the registry, the guard hook and settings - for broken references, drift between files, rules nothing enforces, and contradictions, then suggest improvements. Read-only, reported in chat.
when_to_use: Use when a human in an interactive session asks to audit, review, health-check, or lint the pipeline config ("audit skill", "cek konsistensi", "review rules", "watchtower"), even if they do not say "watchtower". Never use in scheduled or unattended runs, and never on target repos.
disable-model-invocation: false
model: opus
effort: high
argument-hint: "[all|structure|skills|agents|rules|hooks|workflows|consistency|<skill name>]"
compatibility: Needs python3 with PyYAML and a claude-cowork clone.
metadata:
  version: "1.2.0"
  owner: claude-cowork
---
# Watchtower

## Purpose

Keep the control repo coherent as it grows. CI (`scripts/validate-config.py`) proves the structure parses. Watchtower finds what CI misses: a skill frontmatter field that is missing, unknown, or of the wrong type, a trigger in `description` instead of `when_to_use`, a label a skill uses but nobody creates, a "never" rule no hook enforces, a README that lists old skills, two rules that disagree.

It works in two layers:
1. `scripts/audit.py`: deterministic checks. It runs the CI validator, then the drift checks.
2. A judgment review against `references/rubric.md`, for what a script cannot see.

Scope is this repo only. Target repos have their own `AGENTS.md` and review flow.

## When to use / not use

Use when:
- A human asks to audit, review, or health-check the skills, workflows, rules, or hooks of claude-cowork.
- A human wants a consistency check after several config PRs.

Do not use when:
- The human asks about the state of pipeline items. Use `pipeline-status` or `inbox`.
- The human wants a code review of a target repo PR. That is `review-two-stage`.
- A scheduled task runs.

## Procedure

1. **Scope.** Read the argument:
   - none or `all`: every area.
   - `structure`, `skills`, `agents`, `rules`, `hooks`, `workflows`, `consistency`: that area.
   - a skill name: every check, filtered to findings about that skill.
   Pull first: `git -C <clone> pull --ff-only` on the current branch. When the pull fails (no upstream, diverged), audit the local `HEAD` and say so in the first reply line. Note the commit you audit.
2. **Mechanical checks.** Run the script from the clone:
   ```bash
   python3 <skill-dir>/scripts/audit.py --json                  # all areas
   python3 <skill-dir>/scripts/audit.py --json --area hooks     # one area
   python3 <skill-dir>/scripts/audit.py --json --skill inbox    # one skill
   ```
   Exit 1 means at least one `error`. Keep every finding. Do not re-check them by hand.
   `--skill` runs every area and keeps the findings in that skill's folder or that name the skill.
3. **Judgment review.** Read `references/rubric.md`. Review the files of each area in scope against its section.
   - One area or one skill: review it yourself.
   - `all`: check usage first with the `usage-status` skill (`--json --policy <clone>/registry/policy.yml`).
     - `advice: proceed` or no usage data: dispatch one `Explore` subagent per area group, in parallel: skills and agents; workflows; rules and hooks. `Explore` has no write tools. Tell it to read each file in full, not excerpts. Give each the rubric section, the file list, and the script findings for its area so it does not repeat them. Do consistency yourself.
     - `advice: caution`: no subagents. Review every area yourself.
     - `advice: pause`: skip the judgment review. Report the script findings and say the review waits for the reset (`resets_at_utc`).
   - Each finding needs a `path:line` and a quote. Drop any finding without one.
4. **Vet.** Check every judgment finding before you report it. Open the quoted line. Drop it when another file already settles the point, or when it repeats a script finding.
5. **Reply** in semi-casual Bahasa Indonesia, in this order:
   - One line: commit audited and counts per severity (`error`, `warn`, `info`). Script and judgment findings share this scale.
   - A table per area: severity, `claude-cowork/<path>:<line>`, the finding in one line. Errors first.
   - **Saran perbaikan**: at most five, ranked, from the rubric's last section.
   - One closing line: offer to fix the selected items on a branch with a PR, on the human's word.

## Outputs

- One chat reply. No file, branch, GitHub, or scheduled-task write. The pull in step 1 is the only change to the checkout.
- Read-only rests on this text. The skill declares no `disallowed-tools` (`docs/open-questions.md` Q5).
- A fix happens only after the human picks the items. It is then a normal change: branch, tests, PR, and a subscription to the PR (`CLAUDE.md`).

## Stop conditions

- After the reply.
- The script exits 2 (no such skill): show the name and the skill list from `skills-help`, then stop.
- PyYAML is missing: say so and stop. Do not audit by hand alone.
- Usage `advice: pause` on `all`: stop after the script findings (step 3).

## Anti-rationalization

| Thought | Reality |
|---|---|
| "CI is green, so the config is fine." | CI checks structure. Drift and contradictions pass CI. Run the script. |
| "I'll fix the small findings while I'm here." | Watchtower reports. Fix only the items the human picks, in a PR. |
| "This rule sounds risky; I'll flag it." | A finding needs a `path:line` and a quote. No quote, no finding. |
| "More suggestions show more value." | At most five, ranked. Restyling is not a suggestion. |
| "The target repo has the same problem." | Scope is claude-cowork. Note it in one line at most. |

Original to claude-cowork. No upstream source.
