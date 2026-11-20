---
name: usage-reminder
description: Remind the human at every five-hour usage reset. At each reset, report the status of open pipeline tasks across active registry repos, or, when nothing is active, suggest productive use of the fresh window (write a brief, answer pending items). Self-rescheduling via send_later.
when_to_use: Use when a human asks to start, stop, check, or run the usage reset reminder ("reminder reset", "ingatkan saat usage reset"), or when a reminder message asks to run it. Never use from the pipeline scheduled tasks.
disable-model-invocation: false
model: sonnet
effort: low
argument-hint: "start | run | status | stop"
compatibility: Cloud sessions only. Needs the claude-code-remote MCP (send_later, list_triggers, delete_trigger, list_events) and read access to the active registry repos.
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Usage reminder

## Purpose

The five-hour usage window starts at the first request after a reset. It has no fixed schedule. This skill keeps a chain of one-shot reminders, one per reset:

- Each reminder runs `run`, which reads the new `resets_at` and schedules the next reminder.
- The reminder's own request starts the next window. So the reset time is always known when the next reminder is scheduled.

At each reset the human learns one of two things:
- Active tasks exist: their status, grouped by repo.
- No active tasks: a nudge to use the fresh window, for example writing a brief.

A reset helps, it does not interrupt: usage drops to 0%. Starting the window early brings the next refill earlier. The budget per window stays the same.

## When to use / not use

Use when:
- A human asks to start, stop, or check the usage reset reminder.
- A reminder message arrives that says to run this skill with `run`.

Do not use when:
- A pipeline scheduled task runs. The pipeline follows `CLAUDE.md` -> "Usage budget" and never schedules extra runs.
- The human only wants the current usage. Use `usage-status`.

## Inputs

- Argument: `start`, `run`, `status`, or `stop`. No argument means `status`.
- `registry/repos.yml` in the claude-cowork clone: repos with status `active`.
- The `usage-status` skill output (`--json`).

## Constants

- Reminder name: `Usage reset reminder`. All subcommands find the chain by this name.
- Reminder message, exactly:
  ```text
  [Usage reset reminder] Run the usage-reminder skill with argument `run`.
  ```
- Script: `<skill-dir>/scripts/reminder.py`. `<clone>` is the claude-cowork clone.

## Procedure

### start

1. Call `list_triggers` with `enabled: true`. If an entry named `Usage reset reminder` exists, report its `next_run_at` and stop. Never create a second chain.
2. Run `usage-status` with `--json --policy <clone>/registry/policy.yml`. Pipe the JSON to:
   ```bash
   python3 <skill-dir>/scripts/reminder.py next-fire
   ```
   It prints `{"at": "<UTC ISO>", "source": "reset" | "fallback"}`. On a usage-status error, pipe nothing; the script falls back to now + 5h.
3. Call `send_later` with `at`, the reminder name, the reminder message, and `initiation: human_request`.
4. Reply with the fire time in WIB (UTC+7). Say that the reminder fires in this session and stops if the session is archived.

### run

1. **Tasks.** Run:
   ```bash
   python3 <skill-dir>/scripts/reminder.py tasks --registry <clone>/registry/repos.yml
   ```
   Groups, first match wins: `needs_human`, `blocked`, `changes_needed`, `in_progress`, `review_passed` (PRs at Gate 2), `ready`, `draft`, `new_brief` (`ai:brief` without `ai:triaged`), `open_pr` (any other open PR). A repo under `errors` could not be read; name it in the reply.
2. **Usage.** Run `usage-status` with `--json --policy <clone>/registry/policy.yml`.
3. **Reply** in semi-casual Bahasa Indonesia. Keep it short.
   - `active_tasks` > 0: list each repo, then each non-empty group with linked items (`<repo>#<n> title`). Put the groups that wait on the human first. End with one line: `usage: 5h <pct>%, weekly <pct>%, reset berikutnya <WIB time>`.
   - `active_tasks` = 0: say the fresh window is free. Give one or two concrete suggestions: draft a brief with `/draft-brief`, check `/inbox`, or review open PRs. Base them on the repos, not on a generic list. End with the same usage line.
4. **Notify.** Send one `PushNotification`, under 200 characters, headline only. Examples: `Usage reset: 1 in progress, 2 ready, 0 waiting on you` or `Usage reset, no active task: time to write a brief`.
5. **Reschedule.** Follow `start` steps 2 and 3, with these changes:
   - In step 1, ignore the reminder that just fired. It is no longer enabled.
   - Use `initiation: human_schedule`.
   - When `next-fire` returns `source: fallback`, say so in the reply.
   - Skip the reschedule when the human asked to stop the reminders in this session.

### status

Call `list_triggers` with `enabled: true`. Report the `next_run_at` of `Usage reset reminder` in WIB, or say no reminder is pending.

### stop

Call `list_triggers` with `enabled: true`. Delete every entry named `Usage reset reminder` with `delete_trigger`. Confirm how many you removed.

## Outputs

- One chat reply per subcommand. One push notification per `run`.
- At most one pending reminder named `Usage reset reminder`.
- No GitHub writes.

## Stop conditions

- After the reply (and, for `run`, the notification and the reschedule).
- `send_later` fails: report the error and say the chain stopped. Do not retry in a loop.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The reset is at night; I'll shift the reminder to the morning." | The human wants reminders around the clock. Fire at the reset. |
| "I'll fix that stale label while I'm reading the issues." | This skill is read-only on GitHub. Use `answer` when the human asks. |
| "The window reset, so I'll start the next ready task." | A reminder reports. Pipeline work runs only from the scheduled tasks under the usage budget. |
| "A second reminder can't hurt." | Two chains double the notifications and the usage. Check `list_triggers` first. |

Original to claude-cowork. No upstream source.
