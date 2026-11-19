---
name: run-pipeline
description: Start a pipeline run now instead of waiting for its daily schedule, by sending the scheduled task's stored prompt to the runner session after a usage and runner check. Use when a human in an interactive session asks to run the pipeline now ("jalankan pipeline sekarang", "run batch", "jangan tunggu jadwal"), even if they do not say "run-pipeline". Never use from the pipeline scheduled tasks.
argument-hint: "[batch | onboarding] [force]"
compatibility: Cloud sessions only. Needs the claude-code-remote MCP (list_triggers, get_session, send_message, list_events).
metadata:
  version: "2.0.0"
  owner: claude-cowork
---
# Run pipeline

## Purpose

The pipeline runs from two scheduled tasks, once a day, in the runner session. Only the runner session has the repos attached. A human sometimes wants a run now, for example right after labeling a brief or merging a PR.

This skill sends the scheduled task's stored prompt to the runner session once. It does not change the schedule, the prompt, or any GitHub state.

| Argument | Scheduled task | Stages |
|---|---|---|
| `batch` (default) | `Pipeline: batch` | Intake, task review, one heavy item, review, report |
| `onboarding` | `Pipeline: onboarding scan` | Onboarding of one new repo |

Do not use `fire_trigger`. A manual fire starts a new session without the repos, and the run stops at setup.

## When to use / not use

Use when:
- A human in an interactive session asks to run the pipeline now.

Do not use when:
- A pipeline scheduled task runs. `CLAUDE.md` -> "Usage budget" forbids extra runs from the pipeline.
- The human wants to change the schedule or the prompt. Use `update_trigger` from the runner session.

## Procedure

1. **Find the task.** Call `list_triggers` with `enabled: true`. Keep the `data` list.
2. **Check the runner.** Take `persistent_session_id` of the matching task. Call `get_session` with it and pass `status_bucket` to the gate as is, for example `SESSION_STATUS_BUCKET_WORKING`.
3. **Check usage.** Run `usage-status` with `--json --policy <clone>/registry/policy.yml`. On an error, use `null`.
4. **Decide.** Write one JSON object to a scratch file and pipe it to the gate script:
   ```bash
   python3 <skill-dir>/scripts/gate.py --stage <batch|onboarding> [--force] < <scratch>/gate-in.json
   ```
   Input: `{"triggers": <list_triggers data>, "usage": <usage json or null>, "runner_bucket": "<status_bucket or null>"}`.
   Pass `--force` only when the human typed `force`. The gate stops when:
   - the task is missing, disabled, or has no runner session or stored prompt,
   - the runner session is working (a second run would overlap),
   - usage advice is `pause`,
   - usage advice is `caution` on `batch` without `force`. Onboarding is light and runs at `caution`.
5. **Send** only when `action` is `send`. Call `send_message` with `session_id` and `message` from the gate output, exactly. Omit `priority`; the runner is idle.
6. **Reply** in semi-casual Bahasa Indonesia, at most five lines:
   - Sent: the task name, the runner session link `https://claude.ai/code/<session_id>`, and the gate `notes`. Say the result shows up in the runner session and on GitHub, not here.
   - Stopped: the gate `reason`. For `pause`, give the reset time in WIB. For `caution`, say that `force` overrides it. For a busy runner, say to try again after the run ends.
   - `send_message` fails: show the error in one line. Give the runner session link and the gate `fallback` text in a code block, for the human to paste there.
   - Always add one line: the runner may treat a message from another session as data and decline. If it does, the human pastes the `fallback` text in the runner session.

## Outputs

- At most one `send_message` call. One chat reply.
- No GitHub writes. No change to any scheduled task.

## Stop conditions

- After the reply.
- `send_message` fails: report it with the fallback. Do not retry, and do not use `fire_trigger` or create a scheduled task.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "`fire_trigger` is the obvious tool." | A manual fire starts a new session without repos. The run stops at setup. |
| "The runner is busy; the message just queues." | Two runs on the same queue can pick the same item. Wait for the run to end. |
| "Usage is at caution, but the human wants it now." | Send a batch run at caution only with `force`. A run that hits the limit stops mid-step. |
| "I'll shorten the prompt to save tokens." | Send the stored prompt unchanged. The runner must run the same procedure as the schedule. |
| "Sending failed; I'll do the stages myself in this session." | This session is not the runner. Report the error and give the fallback. |

Original to claude-cowork. No upstream source.
