---
name: usage-status
description: Report the active plan's usage-limit status as two lines, time left until the limit window resets and the percent of the limit used, by reading Claude Code rate-limit events and formatting them with a bundled Python script. Use whenever someone asks how much plan usage, quota, or limit is left, when the limit resets, "sisa usage", "kuota", "limit reset kapan", or wants to check usage before starting a big task, even if they do not say "usage-status".
---
# Usage status

## Purpose

Show the plan usage limit in a fixed format:

```
remaining hour to reset: 1h30m
usage percentage: 29%
```

The numbers are for the **five-hour window** by default. That window is the limit that blocks work first. The weekly window (`seven_day`) is available with `--all`.

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
   - `--all`: print the five-hour and the weekly windows.
   - `--window seven_day`: print only the weekly window.
   - `--json`: machine-readable output, with the UTC reset time and status.

4. Reply with the script output exactly, inside a code block. Add one short line only when it helps:
   - The script printed `status: rejected`: the limit is reached; work resumes at the reset time.
   - The script printed `window already reset`: the data predates the reset, and usage is back to 0%.

## Other inputs

The script also accepts a single `rate_limit_info` object, or the status line JSON of local Claude Code (field `rate_limits.five_hour.used_percentage` and `resets_at`). Use those when the MCP tool is not available, for example in a local terminal session with a status line script.

If no source is available, say so in one line, and point the user to Settings -> Usage on claude.ai. Do not guess numbers.
