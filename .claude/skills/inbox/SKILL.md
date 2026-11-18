---
name: inbox
description: Show a human everything in the pipeline that waits on them right now - `ai:needs-human` and `ai:blocked` items, design PRs at Gate 1, code PRs at Gate 2, and onboarding PRs - across the control repo and every registry repo, with links, age, and the next action. Read-only. Use when a human in an interactive session asks what waits on them, what is stuck, or for their inbox. Never use in scheduled or unattended runs.
argument-hint: "[owner/repo to limit the list]"
---
# Inbox

## Purpose

Answer "what waits on me?" in chat, in under a minute, without opening GitHub or waiting for the daily report. This skill only reads. It changes no issue, PR, or label.

## When to use / not use

Use when:
- A human in an interactive session asks what waits on them, what is stuck, or for their inbox.

Do not use when:
- The session is scheduled or unattended. The `daily-report` skill covers that.
- The human wants to answer an item. Use the `answer` skill.

## Inputs

- `registry/policy.yml` (`control_repo`) and `registry/repos.yml` (every repo except `frozen`).
- Optional argument: one `owner/repo` to limit the list.

## Procedure

1. **Pick the repos.** The control repo plus every registry repo whose status is not `frozen`. Limit to the argument repo when one is given.

2. **Collect items** with read-only calls. Use `gh` when it is authenticated. Otherwise use the GitHub MCP read tools (`list_issues`, `list_pull_requests`, `issue_read`). Run the repos in parallel when possible.
   ```bash
   R=<owner/repo>
   gh issue list --repo "$R" --state open --label ai:needs-human --json number,title,url,labels,updatedAt
   gh issue list --repo "$R" --state open --label ai:blocked     --json number,title,url,labels,updatedAt
   gh pr list    --repo "$R" --state open --json number,title,url,labels,headRefName,isDraft,updatedAt,reviewDecision
   ```
   Classify each open item into one group. An item goes into the first group that matches.

   | # | Group | Rule | Your action |
   |---|---|---|---|
   | 1 | Questions for you | `ai:needs-human` | Answer with `/answer <ref>` |
   | 2 | Blocked | `ai:blocked` | Read the failing output; answer or fix with `/answer <ref>` |
   | 3 | Gate 1: design to merge | Open PR, head branch `design/*`, not draft | Read the design, merge or comment |
   | 4 | Gate 2: code to approve | Open PR with `ai:review-passed` | Review, approve, merge |
   | 5 | Onboarding to merge | Open PR that adds `.agent/profile.yml`, or a registry PR in the control repo | Check the profile, merge |

   Detect onboarding PRs by title or by changed files (`gh pr view <n> --repo "$R" --json files`). Check files only for PRs that match no other group.

3. **Read the question for groups 1 and 2.** For each item, read the last comment that carries an agent marker (`<!-- ai:intake -->`, or the latest comment that lists questions or failing output). Summarize the question or error in one line. Do not copy long output.

4. **Spot answers that cannot work.** Mark an item **not answerable by comment** when the blocker is:
   - effective autonomy too low,
   - a repo that is not `active` or not in the registry,
   - missing branch protection.

   These need a registry PR or a platform change. Say what would fix it.

5. **Reply in chat**, in the human's language (semi-casual Bahasa Indonesia by default). Order: group 1 to 5. Within a group, oldest first.
   ```markdown
   **Nunggu kamu: 4 item**

   **Pertanyaan (1)**
   - [claude-cowork#12 Fix README typo](url) · 2 hari · Agent tanya: repo mana? Default: claude-cowork → `/answer #12`

   **Gate 2: approve kode (1)**
   - [web#40 Add reset endpoint](url) · 5 jam · review agent lolos
   ```
   - Age = now minus `updatedAt`, in hours or days.
   - Short refs: `#n` for the control repo, `<repo>#n` for others.
   - Empty groups are omitted. Nothing at all: say the inbox is empty and give the latest `ai:report` issue link if one exists.
   - End with at most one line of suggestion, for example the oldest item to handle first.

## Outputs

- One chat message. No GitHub writes.

## Stop conditions

- Message sent. Do not answer, label, or close anything in the same turn unless the human asks, and then use the `answer` skill.
- A repo cannot be read: list it under "Tidak bisa dibaca" with the error and continue with the others.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "I'll remove this stale label while I'm here." | Inbox is read-only. Use `answer` when the human asks. |
| "I'll show every open issue to be thorough." | Only items that wait on a human. The rest is noise. |
| "I'll paste the full failing log." | One line per item. The link has the detail. |
| "The question is about autonomy; I'll suggest answering it." | Autonomy is changed by PR, not by comment. Mark it not answerable by comment. |

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
