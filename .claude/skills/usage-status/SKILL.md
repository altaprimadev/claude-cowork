---
name: usage-status
description: Report the active plan's usage-limit status (time left until the limit window resets, percent used) from Claude Code rate-limit events, formatted by a bundled Python script. Use whenever someone asks how much plan usage, quota, or limit is left, or when the limit resets ("sisa usage", "kuota", "limit reset kapan"), even if they do not say "usage-status".
when_to_use: Before starting a task, so the agent can predict whether the work will finish without hitting the limit. During long work, to decide when to pause at a clean point and when to resume after the reset.
argument-hint: "[--json]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - mcp__claude-code-remote__list_events
  - Bash(python3 *usage_status.py*)
compatibility: Python 3. Cloud sessions need the claude-code-remote MCP (list_events). Local sessions need status line JSON with a rate_limits field.
metadata:
  version: "1.1.0"
  owner: claude-cowork
---
# Usage status

## Purpose

Show the plan usage limit in a fixed format:

```
remaining hour to reset: 1h30m
usage percentage:
- 5h: 29%
- weekly: 70%
```

The reset time is for the **five-hour window**. That window blocks work first. The percentages cover both windows. The weekly reset time is in the `--json` output.

## Where the data comes from

Every API call in a Claude Code session returns rate-limit info. In a cloud session the platform stores it as `rate_limit_event` entries in the session transcript. Read those events through the `claude-code-remote` MCP. Do not call the OAuth usage endpoint and do not open `~/.claude/.credentials.json`: the repo rules forbid reading credentials, and the events already hold the same numbers.

## Steps

1. Get the MCP session id:

   ```bash
   python3 <skill-dir>/scripts/usage_status.py --session-id
   ```

2. Call `mcp__claude-code-remote__list_events` with that `session_id`, `kinds: ["rate_limit_event"]`, and `limit: 100`.
   - With no cursor, the call returns the newest events, oldest first. The last event is the current state.
   - If `data` is empty and `has_more` is true, call again with `before_id` set to `first_id`. Repeat until you find an event or `has_more` is false.

3. Pass the full JSON result to the script through a quoted heredoc. The script finds the newest snapshot by itself.

   ```bash
   python3 <skill-dir>/scripts/usage_status.py <<'JSON'
   <paste the list_events result here>
   JSON
   ```

   Flag:
   - `--json`: machine-readable output for both windows, with reset times, status, and `advice`.

4. Reply with the script output exactly, inside a code block. Add one short line only when it helps:
   - The script printed `status: limit reached`: work resumes at the reset time of that window.
   - The script printed `window already reset`: the data predates the reset, and usage is back to 0%.

## Plan work around the limit

When you check usage for your own planning, not for a human question, run the script with `--json`. Read `advice` and `resets_at_iso` of each window.

| `advice` | Condition | What to do |
|---|---|---|
| `proceed` | Five-hour usage below 70% | Start or continue the task. |
| `caution` | 70% to 89% | Take only work that fits in a few steps. Commit and push after each step, so a stop loses nothing. Check again before the next step. |
| `pause` | 90% or more, or status not `allowed` | Stop at the next clean point. Commit and push. Post one comment on the issue or PR with the progress and the resume time. Schedule a resume at `resets_at_iso` with `send_later` (or `ScheduleWakeup` in a `/loop`). |

Why stop early: a session that hits the limit stops in the middle of a step. Half-written files and unpushed commits are hard to recover in an ephemeral container. A clean stop at 90% costs a little capacity and saves the work.

Check both windows. If `seven_day` is at `pause`, do not start new tasks. Report the weekly reset time instead.

## Other inputs

The script also accepts a single `rate_limit_info` object, or the status line JSON of local Claude Code (field `rate_limits.five_hour.used_percentage` and `resets_at`). Use those when the MCP tool is not available, for example in a local terminal session with a status line script.

If no source is available, say so in one line, and point the user to Settings -> Usage on claude.ai. Do not guess numbers.
