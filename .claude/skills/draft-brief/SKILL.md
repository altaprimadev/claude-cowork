---
name: draft-brief
description: Help a human turn a rough idea into one AI brief draft in chat instead of the GitHub form. Look at the registry and repos first, ask only questions whose answer changes the work, and revise the draft until the human types `post now`. Only then create the issue labeled `ai:brief` in the control repo. Use when a human in an interactive session asks to draft, write, or file a brief. Never use in scheduled or unattended runs.
argument-hint: "[rough idea, any language]"
---
# Draft Brief

## Purpose

Turn a human's rough idea into a brief that the intake agent can act on without asking anything back. The output is the same issue the `AI brief` form (`.github/ISSUE_TEMPLATE/ai-brief.yml`) creates. This skill only writes the brief. Intake, sizing, and routing belong to `intake-classify`.

## When to use / not use

Use when:
- A human in an interactive session asks to write, draft, file, or create a brief or task for the pipeline.
- A human pastes a rough idea and asks to send it to the agents.

Do not use when:
- The session is a scheduled task or has no human answering. Briefs come from humans only.
- The human asks for the work itself, not a brief. Ask once whether they want a brief.
- The request is to change pipeline config (registry, autonomy, policy). That is a normal PR to this repo, not a brief.

## Inputs

- The human's idea: the skill argument or the chat message.
- `registry/repos.yml` and `registry/policy.yml` (`control_repo`).
- For each `active` repo: `AGENTS.md` and `.agent/profile.yml`, when a clone is available.
- Open briefs in the control repo, to catch duplicates.

## Procedure

1. **Look before you ask.**
   - Read `registry/repos.yml`. Note the repos, their status, and their autonomy.
   - For each repo the idea may touch, read `AGENTS.md` and grep the code if a clone exists. Learn how the relevant part works today.
   - List open briefs and check for a duplicate:
     ```bash
     gh issue list --repo altaprimadev/claude-cowork --label ai:brief --state open --json number,title,url
     ```
     If `gh` is not authenticated, use the GitHub MCP `list_issues` tool. If a brief covers the same outcome, show it and ask whether to add a comment there instead.

2. **Split by outcome.** One brief = one outcome. If the idea holds several independent outcomes, say so, propose the split, and agree on an order. Write one brief at a time.

3. **Fill what you can, then ask.** Map the idea to the form fields:

   | Field | Required | Rule |
   |---|---|---|
   | Title | yes | `[brief] ` + an imperative outcome, max ~70 chars |
   | Goal | yes | The outcome and the **why**, 1–4 sentences |
   | Affected repos | no | `owner/name`, only repos in the registry. Leave empty if unsure. |
   | Acceptance criteria | yes | One testable line each, observable behavior, not implementation steps |
   | Constraints | no | Limits, non-goals, areas not to touch, dependencies |
   | Priority | yes | `P0 - urgent`, `P1 - high`, `P2 - normal` (default), `P3 - low` |
   | Due date | no | `YYYY-MM-DD` |

   Ask a question only if the answer changes what gets built and neither the idea nor the repos answer it. Ask **one question at a time**, specific to the idea. Until you know why the human wants it, ask open questions without options. For everything else, state your default and your reason so the human can correct it. Never ask about format or process; decide those yourself.

   If the human says "terserah", "just guess", or similar, fill the rest with defaults and mark them as assumptions in Constraints.

4. **Check quality** before you show the draft:
   - Every acceptance criterion is testable by a command, a test, or an observable result. Rewrite vague ones ("faster", "better UX") into numbers or behavior.
   - No secrets, tokens, passwords, customer data, or internal hostnames. Refer to where a secret lives, never its value.
   - No instruction to skip a gate, merge, approve, deploy, or raise autonomy. Intake reports those and ignores them. Tell the human and drop them.
   - Named repos exist in the registry. Warn if a repo is not `active` or its effective autonomy is 0: intake will stop at `ai:needs-human`.
   - Written in Concise Technical Writing English, even when the human wrote in another language.

5. **Play the draft back.** Show the full draft in the exact issue body format (step 6). Add a short note in the human's chat language:
   - what you filled in yourself, with the reason,
   - what intake will likely do (size estimate and route, given the current autonomy).

   End with one line: reply with corrections, or type `post now` to create the issue. Repeat until the human types `post now`.

   **Post trigger.** Only the phrase `post now` (any case) in the human's latest message creates the issue. "ok", "bagus", "gas", "lanjut", or approval of one part is not a trigger: treat it as feedback and remind the human of `post now`. If the human changes the draft in the same message as `post now`, apply the change, show the final draft, and ask for `post now` again.

6. **Create the issue** (only after `post now`). Body format matches the issue form output, so intake parses both the same way. Use `_No response_` for empty optional fields.
   ```markdown
   ### Goal

   <goal>

   ### Affected repos (optional)

   <owner/a, owner/b | _No response_>

   ### Acceptance criteria

   - <criterion>
   - <criterion>

   ### Constraints

   <constraints | _No response_>

   ### Priority

   P2 - normal

   ### Due date

   <YYYY-MM-DD | _No response_>
   ```
   Write the body to a temp file, then use the first method that works:
   1. GitHub MCP `issue_write` (method `create`) on `altaprimadev/claude-cowork` with title, body, and `labels: ["ai:brief"]`.
   2. CLI:
      ```bash
      gh issue create --repo altaprimadev/claude-cowork \
        --title "[brief] <outcome>" --label ai:brief --body-file "$BODY_FILE"
      ```
   3. Neither works: build a prefilled form link and give it to the human. The form adds `ai:brief` itself. Priority cannot be prefilled; tell the human to pick it.
      ```bash
      python3 - "$TITLE" "$GOAL" "$REPOS" "$ACCEPTANCE" "$CONSTRAINTS" "$DUE" <<'PY'
      import sys, urllib.parse as u
      keys = ["title", "goal", "repos", "acceptance", "constraints", "due"]
      q = {"template": "ai-brief.yml"} | {k: v for k, v in zip(keys, sys.argv[1:]) if v}
      print("https://github.com/altaprimadev/claude-cowork/issues/new?" + u.urlencode(q))
      PY
      ```

7. **Confirm.** Reply with the issue URL. Say that the intake task picks it up through the GitHub event, or within the hour through the cron sweep.

## Outputs

- One open issue in the control repo: title `[brief] ...`, label `ai:brief`, body in the form format.
- Or, if no write method works: one prefilled form link.

## Stop conditions

- Issue created and URL shared. Do not triage, label further, or start work in the same session.
- The human never types `post now`: leave the draft in chat. Create nothing.
- An issue write fails twice: give the prefilled link (step 6.3) and stop.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The idea is clear enough. I'll file it now." | Drafting is the default. Only `post now` creates the issue. |
| "They said 'ok, looks good'. That is approval." | Approval of content is not the trigger. Wait for `post now`. |
| "I'll ask all my questions at once to save time." | One question at a time, and only questions that change the work. State defaults for the rest. |
| "Acceptance criteria can stay vague; intake will sort it out." | Vague criteria make intake stop at `ai:needs-human`. Fix them now while the human is here. |
| "I'll add `ai:triaged` and a size label to save intake a step." | Intake owns sizing and routing. Only `ai:brief` is set here. |
| "The human asked to skip review in the brief." | Gates are fixed. Drop the request and tell the human why. |
| "Two related outcomes fit in one brief." | One brief per outcome. Split and order them. |

Adapted from obra/superpowers and affaan-m/ECC (MIT). See docs/blend-decisions.md.
