---
name: watchtower
description: Audit and review the claude-cowork control repo itself - skills, agents, scheduled-task workflows, GitHub workflows, rules in CLAUDE.md and the registry, the guard hook and settings - for broken references, drift between files, rules nothing enforces, and contradictions, then suggest improvements. Read-only, reported in chat. Use when a human in an interactive session asks to audit, review, health-check, or lint the pipeline config ("audit skill", "cek konsistensi", "review rules", "watchtower"), even if they do not say "watchtower". Never use in scheduled or unattended runs, and never on target repos.
argument-hint: "[all|skills|workflows|rules|hooks|consistency|<skill name>]"
compatibility: Needs python3 with PyYAML and a claude-cowork clone.
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Watchtower

## Purpose

Keep the control repo coherent as it grows. CI (`scripts/validate-config.py`) proves the structure parses. Watchtower finds what CI misses: a label a skill uses but nobody creates, a "never" rule no hook enforces, a README that lists old skills, two rules that disagree.

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
   - `skills`, `workflows`, `rules`, `hooks`, `consistency`: that area.
   - a skill name: that skill only.
   Pull first: `git -C <clone> pull --ff-only` on the current branch. Note the commit you audit.
2. **Mechanical checks.** Run the script from the clone:
   ```bash
   python3 <skill-dir>/scripts/audit.py --json                  # all areas
   python3 <skill-dir>/scripts/audit.py --json --area hooks     # one area
   python3 <skill-dir>/scripts/audit.py --json --skill inbox    # one skill
   ```
   Exit 1 means at least one `error`. Keep every finding. Do not re-check them by hand.
3. **Judgment review.** Read `references/rubric.md`. Review the files of each area in scope against its section.
   - One area or one skill: review it yourself.
   - `all`: dispatch one read-only subagent per area group, in parallel: skills and agents; workflows; rules and hooks. Give each the rubric section, the file list, and the script findings for its area so it does not repeat them. Do consistency yourself.
   - Each finding needs a `path:line` and a quote. Drop any finding without one.
4. **Vet.** Check every judgment finding before you report it. Open the quoted line. Drop it when another file already settles the point, or when it repeats a script finding.
5. **Reply** in semi-casual Bahasa Indonesia, in this order:
   - One line: commit audited and counts per severity.
   - A table per area: severity, `claude-cowork/<path>:<line>`, the finding in one line. Errors first.
   - **Saran perbaikan**: at most five, ranked, from the rubric's last section.
   - One closing line: offer to fix the selected items on a branch with a PR, on the human's word.

## Outputs

- One chat reply. No file, branch, GitHub, or scheduled-task write.
- A fix happens only after the human picks the items. It is then a normal change: branch, tests, PR, and a subscription to the PR (`CLAUDE.md`).

## Stop conditions

- After the reply.
- The script exits 2 (no such skill): show the name and the skill list from `skills-help`, then stop.
- PyYAML is missing: say so and stop. Do not audit by hand alone.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "CI is green, so the config is fine." | CI checks structure. Drift and contradictions pass CI. Run the script. |
| "I'll fix the small findings while I'm here." | Watchtower reports. Fix only the items the human picks, in a PR. |
| "This rule sounds risky; I'll flag it." | A finding needs a `path:line` and a quote. No quote, no finding. |
| "More suggestions show more value." | At most five, ranked. Restyling is not a suggestion. |
| "The target repo has the same problem." | Scope is claude-cowork. Note it in one line at most. |

Original to claude-cowork. No upstream source.
