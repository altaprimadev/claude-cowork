---
name: usage-status
description: Report the active plan's usage-limit status (time left until the limit window resets, percent used) from Claude Code rate-limit events, formatted by a bundled Python script. Use whenever someone asks how much plan usage, quota, or limit is left, or when the limit resets ("sisa usage", "kuota", "limit reset kapan"), even if they do not say "usage-status".
when_to_use: Before starting a task, so the agent can predict whether the work will finish without hitting the limit. During long work, to decide when to pause at a clean point and when to resume after the reset.
argument-hint: "[--json] [--policy registry/policy.yml]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - mcp__claude-code-remote__list_events
  - Bash(python3 *usage_status.py*)
compatibility: Python 3. Cloud sessions need the claude-code-remote MCP (list_events). Local sessions need status line JSON with a rate_limits field.
metadata:
  version: "1.2.0"
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

   Flags:
   - `--json`: machine-readable output. Top level: `advice` (five-hour window; a reached limit in any window pauses), `captured_at` (event time), `thresholds`, and `windows` with each window's percent, reset times, status, and advice.
   - `--policy <claude-cowork clone>/registry/policy.yml`: read thresholds from `usage_budget`. Without it, the script uses 70% and 90%.

4. Reply with the script output exactly, inside a code block. Add one short line only when it helps:
   - The script printed `status: limit reached`: work resumes at the reset time of that window.
   - The script printed `window already reset`: the data predates the reset, and usage is back to 0%.

## Plan work around the limit

**In the claude-cowork pipeline**, the orchestrator runs this skill before each delegation and applies `CLAUDE.md` -> "Usage budget". That rule decides which stages run. Use the table below only outside the pipeline, in interactive sessions.

When you check usage for your own planning, run the script with `--json`. Read the top-level `advice`. It follows the five-hour window; the weekly percent does not change it unless the weekly limit is reached.

| `advice` | Condition (default thresholds) | What to do |
|---|---|---|
| `proceed` | Five-hour window below 70% | Start or continue the task. |
| `caution` | Five-hour window at 70% to 89% | Take only work that fits in a few steps. Commit and push after each step, so a stop loses nothing. Check again before the next step. |
| `pause` | Five-hour window at 90% or more, or any window's status not `allowed` | Stop at the next clean point. Commit and push. Tell the human the resume time (`resets_at_utc` of the window that paused). |

Why stop early: a session that hits the limit stops in the middle of a step. Half-written files and unpushed commits are hard to recover in an ephemeral container. A clean stop at 90% costs a little capacity and saves the work.

## Other inputs

The script also accepts a single `rate_limit_info` object, or the status line JSON of local Claude Code (field `rate_limits.five_hour.used_percentage` and `resets_at`). Use those when the MCP tool is not available, for example in a local terminal session with a status line script.

If no source is available, say so in one line, and point the user to Settings -> Usage on claude.ai. Do not guess numbers.

Original to claude-cowork. No upstream source.
