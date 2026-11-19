---
name: run-pipeline
description: Fire a pipeline scheduled task now instead of waiting for its daily schedule, after a usage and runner check. Use when a human in an interactive session asks to run the pipeline now ("jalankan pipeline sekarang", "run batch", "jangan tunggu jadwal"), even if they do not say "run-pipeline". Never use from the pipeline scheduled tasks.
argument-hint: "[batch | onboarding] [force]"
compatibility: Cloud sessions only. Needs the claude-code-remote MCP (list_triggers, get_session, fire_trigger, list_events).
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Run pipeline

## Purpose

The pipeline runs from two scheduled tasks, once a day. A human sometimes wants a run now, for example right after labeling a brief or merging a design PR. This skill fires the existing scheduled task once. It does not change the schedule, the prompt, or any GitHub state.

| Argument | Scheduled task | Stages |
|---|---|---|
| `batch` (default) | `Pipeline: batch` | Intake, task review, one heavy item, review, report |
| `onboarding` | `Pipeline: onboarding scan` | Onboarding of one new repo |

## When to use / not use

Use when:
- A human in an interactive session asks to run the pipeline now.

Do not use when:
- A pipeline scheduled task runs. `CLAUDE.md` -> "Usage budget" forbids extra runs from the pipeline.
- The human wants to change the schedule or the prompt. Use `update_trigger` from the runner session.

## Procedure

1. **Find the task.** Call `list_triggers` with `enabled: true`. Keep the `data` list.
2. **Check the runner.** Take `persistent_session_id` of the matching task. Call `get_session` with it and read `status_bucket`. Skip this step when the task has no `persistent_session_id`.
3. **Check usage.** Run `usage-status` with `--json --policy <clone>/registry/policy.yml`. On an error, use `null`.
4. **Decide.** Pipe one JSON object to the gate script:
   ```bash
   python3 <skill-dir>/scripts/gate.py --stage <batch|onboarding> [--force] <<'JSON'
   {"triggers": <list_triggers data>, "usage": <usage json or null>, "runner_bucket": "<status_bucket or null>"}
   JSON
   ```
   Pass `--force` only when the human typed `force`. The gate stops when:
   - the task is missing or disabled,
   - the runner session is `working` (a second run would overlap),
   - usage advice is `pause`,
   - usage advice is `caution` on `batch` without `force`. Onboarding is light and runs at `caution`.
5. **Fire** only when `action` is `fire`. Call `fire_trigger` with `trigger_id` and this text:
   ```text
   Manual run requested by a human from an interactive session. Run the full prompt as a normal scheduled run.
   ```
6. **Reply** in semi-casual Bahasa Indonesia, at most four lines:
   - Fired: the task name, the runner session link `https://claude.ai/code/<persistent_session_id>`, and the gate `notes`. Say the result shows up in the runner session and on GitHub, not here.
   - Stopped: the gate `reason`. For `pause`, give the reset time in WIB. For `caution`, say that `force` overrides it. For a busy runner, say to try again after the run ends.
   - `fire_trigger` refused: show the error in one line. Say the human can start the run from the runner session.

## Outputs

- At most one `fire_trigger` call. One chat reply.
- No GitHub writes. No change to any scheduled task.

## Stop conditions

- After the reply.
- `fire_trigger` fails: report it. Do not retry and do not create a new scheduled task.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The runner is busy; firing just queues the run." | Two runs on the same queue can pick the same item. Wait for the run to end. |
| "Usage is at caution, but the human wants it now." | Fire a batch run at caution only with `force`. A run that hits the limit stops mid-step. |
| "Firing failed; I'll do the stages myself in this session." | This session has no runner setup. Report the error and stop. |
| "I'll fire both tasks to be thorough." | Fire the one the human asked for. Default is `batch`. |

Original to claude-cowork. No upstream source.
