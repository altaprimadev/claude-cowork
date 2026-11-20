---
name: pipeline-status
description: Show a human what the agent pipeline is doing right now - whether the runner is working or idle, when the next scheduled run fires, which tasks are in progress, which PRs wait for agent review or a human merge, what the next run will pick up, and which tasks wait on dependencies. Read-only, in chat. Use when a human in an interactive session asks for the pipeline status ("status pipeline", "lagi ngerjain apa", "nunggu apa"), even if they do not say "pipeline-status". Never use in scheduled or unattended runs.
argument-hint: "[owner/repo to limit the list]"
compatibility: Cloud sessions. Needs the claude-code-remote MCP (list_triggers, get_session, list_events) and gh.
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Pipeline status

## Purpose

`daily-report` covers a day: done, stuck, recurring problems, cost. This skill answers a narrower question, now: what the pipeline is doing and what each item waits for. It reads GitHub and the runner session. It writes nothing.

| Group | Meaning |
|---|---|
| Runner | Runner session working or idle, next scheduled runs in WIB, the next heavy item |
| Lagi dikerjain | `ai:in-progress` without a PR, and agent PRs waiting for agent review |
| Nunggu merge dari lu | Design PRs (Gate 1), `ai:review-passed` PRs (Gate 2), onboarding and registry PRs |
| Nunggu jawaban lu | `ai:needs-human` and `ai:blocked` items |
| Antrian run berikutnya | Fix rounds, `ai:ready`, `ai:draft` (task review), new briefs, `ai:needs-design` |
| Nunggu dependency | Planned tasks with no stage label, with the dependencies still open |
| Mandek | `ai:in-progress` without a PR and no activity for more than 24 hours |

## When to use / not use

Use when:
- A human in an interactive session asks what the pipeline is doing or waiting for.

Do not use when:
- The human wants the daily summary, done items, or cost. Use `daily-report`.
- The human wants only what waits on them, with the questions. Use `inbox`.
- A scheduled task runs. This skill only answers humans.

## Procedure

1. **Runner and schedule.** Call `list_triggers` with `enabled: true`. Take the `persistent_session_id` of `Pipeline: batch` and call `get_session` with it.
2. **Usage.** Run `usage-status` with `--json --policy <clone>/registry/policy.yml`. On an error, use `null`.
3. **Build.** Write one JSON object to a scratch file and pipe it to the script:
   ```bash
   python3 <skill-dir>/scripts/status.py --registry <clone>/registry/repos.yml < <scratch>/status-in.json
   ```
   Input: `{"triggers": <list_triggers result>, "runner": <get_session JSON or null>, "usage": <usage json or null>}`. For `runner`, pass only the JSON object inside the session record, not the wrapper text around it.
   The script reads open issues and PRs with `gh api` in the control repo and every `active` registry repo.
4. **Reply** with the script output as is, outside a code block. With a repo argument, drop the lines of other repos. Add at most two lines:
   - Items wait on the human: point to `/inbox` or `/answer`.
   - The runner is idle and the queue holds work: say when the next run fires, or that `/run-pipeline` starts one now.

## Outputs

- One chat reply. No GitHub writes. No change to any scheduled task or session.

## Stop conditions

- After the reply.
- A repo shows under "Nggak kebaca": keep the reply, and name the repo.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The runner is idle and #46 is ready; I'll start it." | This skill reports. Use `/run-pipeline` when the human asks. |
| "The heavy item candidate is certain." | The batch picks by priority and budget at run time. Call it a candidate. |
| "The daily report already has this." | The report is a daily snapshot. This skill shows the state now. |
| "I'll rewrite the output in my own words." | Reply with the script output. Add at most two lines. |

Original to claude-cowork. No upstream source.
