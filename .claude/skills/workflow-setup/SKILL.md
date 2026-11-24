---
name: workflow-setup
description: Set up the agent pipeline from zero, or repair it. Audit every setup step against the internal rules as pass, fail, or error, show the manual guide for the steps no AI can do, and run a wizard that does every other step itself.
when_to_use: Use when a human in an interactive session asks to set up, install, repair, or check the pipeline setup ("setup workflow", "pasang pipeline", "runner hilang", "cek setup"), even if they do not say "workflow-setup". Never use from the pipeline scheduled tasks.
disable-model-invocation: true
model: opus
effort: medium
argument-hint: "[status | guide | wizard]"
compatibility: Cloud sessions only. Needs the claude-code-remote MCP (list_triggers, get_session, list_events, list_environments, list_repos, add_repo, create_session, create_trigger, update_trigger, delete_trigger) and gh with REST access.
metadata:
  version: "1.1.0"
  owner: claude-cowork
---
# Workflow setup

## Purpose

`claude-cowork/docs/setup.md` and `claude-cowork/docs/scheduled-tasks.md` describe the setup. This skill turns them into two tracks:

| Track | Who | Content |
|---|---|---|
| Manual guide | Human | Steps no AI session can do: payment, identity, browser consent, settings with no API, and requests the platform accepts only when a person types them. `references/human-guide.md`, steps H1 to H9. |
| Wizard | This session | Every other step, W1 to W9. The wizard checks state first, acts only on gaps, and verifies after each step. |

The audit is internal. It checks the setup against the rules and docs of claude-cowork, and reports each step as `pass`, `fail` (the state is wrong) or `error` (the check could not run), each with a reason. It gives no advice, suggestion, or improvement. Judging the rules themselves, from outside, is `watchtower`'s job.

A permission rule never moves a step to the manual guide. If only a rule blocks a step, the wizard does it. Merging a PR is the exception: it is a gate rule, so the wizard stops there and names the PR.

| Argument | Action |
|---|---|
| `status` (default) | Audit every step and reply with the table: pass, fail, or error, with reasons. No changes, no advice. |
| `guide` | The manual guide, with each H step's current status and the inputs the wizard prepared. No changes. |
| `wizard` | Audit, show the plan, ask once, then do every open W step and re-audit. |

## When to use / not use

Use when:
- A human sets up the pipeline for the first time, or after a reset (new runner session, new org, new environment).
- Something in the setup broke: the runner is archived, a task is missing, labels are gone.

Do not use when:
- The human wants a pipeline run now. Use `run-pipeline`.
- The human wants the skills, rules, or docs of this repo reviewed, or wants suggestions and improvements. Use `watchtower`. This skill checks the setup against those rules; it never judges or improves them.
- A scheduled task runs. This skill changes scheduled tasks and repo settings; only a human may start it.

## Audit (every mode)

1. **Collect** with MCP tools. Pass only these fields to the script, copied exactly:
   - `list_triggers` with `enabled` omitted: each task's `name`, `enabled`, `cron_expression`, `persistent_session_id`, and `derived_state.prompt`.
   - `get_session` on the `persistent_session_id` of the two pipeline tasks, when they share one: `id`, `session_status`, `session_context.sources`.
   - `list_environments`: each `name`.
   - `list_repos` with `query: "alta-prima-indonesia/"`: each `full_name`.
   - `runner_guard`: `list_events` on the runner with `kinds: ["result"]` and `limit: 100`. Take `active` or `inactive` from the newest `guard: <value>` line, else `null`.
2. **Repo access.** An active registry repo that `gh api` cannot read (HTTP 403) needs `add_repo`. In `status` and `guide`, call it with `access: "read"`. In `wizard`, call it with `access: "push"`, because W2 to W4 write.
3. **Run** the script:
   ```bash
   python3 <skill-dir>/scripts/setup_audit.py --root <clone> [--json] < <scratch>/setup-in.json
   ```
   Input: `{"triggers": [...], "runner": {...} or null, "environments": [...] or null, "org_repos": [...] or null, "runner_guard": "active" | "inactive" | null}`.
   Each step has `owner` (`human` or `ai`), `status` (`pass`, `fail`, `error`), and `reason`. A step that waits on another one fails with the reason `nunggu <ID>`.

## Mode `status`

Reply with the script output as is, outside a code block. Add nothing: no next step, no suggestion, no advice.

## Mode `guide`

Read `references/human-guide.md`. Reply with only the H steps whose status is not `pass`, in ID order. For each step, give the guide's steps and fill in the values the wizard knows: repo names, the org, the managed settings JSON, and the H9 messages (see W7). Steps that end in `error` because no tool can verify them (H2, H3): ask the human to confirm them once.

## Mode `wizard`

### Plan and the one ask

1. Run the audit with `--json`.
2. Run `usage-status` with `--json --policy <clone>/registry/policy.yml`. At `pause`, stop and give the reset time in WIB. The wizard is a light job; it runs at `caution`.
3. Show the plan in chat: every A step that is not `pass`, with the concrete actions (for example "create 13 labels in alta-prima-admin-prisma", "create task Pipeline: batch bound to session X"), then the open H steps, which the wizard cannot do.
4. Ask once: "Ketik `jalan` untuk mulai." This is the one confirmation for every outward action in the plan (`CLAUDE.md` → "Interactive sessions too"). Do nothing outward before it. A later step that was not in the plan needs its own ask.

### Steps

Run the steps in order. Skip a step whose audit status is `pass`. A step that fails with `nunggu <ID>` waits for that step; skip it and continue. A step with `error` needs repo access or input first. After each step, re-run the audit and confirm the step is `pass` before you report it done.

**W1. Config valid (A1).** `scripts/validate-config.py` must pass on `main`. If it fails, report the output. Fix it only when the fix is a sync between `.claude/settings.json` and `templates/managed-settings.json`. Then open a PR from your branch and wait for the merge.

**W2. Labels (A2).** The label list lives in `claude-cowork/scripts/setup-labels.sh` (`LABELS`). For each repo and missing label:
```bash
gh api -X POST "repos/$OWNER/$NAME_OF_REPO/labels" -f name="$LABEL" -f color="$COLOR" -f description="$DESC"
```
For a label that exists with another color or description, use `-X PATCH "repos/<owner>/<repo>/labels/<url-encoded name>"`. Never delete a label.

**W3. CODEOWNERS (A3).** Take the reviewers from `claude-cowork/.github/CODEOWNERS` (tier 1). For each repo without the file:
- Open a PR in that repo on branch `ai/setup-codeowners`, against the integration branch from its `AGENTS.md` (default branch when none). Content: `* @<reviewer> ...`.
- Check each reviewer's access: `gh api repos/<owner>/<repo>/collaborators/<user>` (204 = has access, 404 = none).
- A reviewer or the machine user (H3) without access needs an invitation. The guard hook blocks every write to the `collaborators` endpoint, by design: the agent identity holds admin rights. Do not work around it. List the missing invitation in the final reply under **Diblok aturan**, with the repo, the user, and `permission=push`. This is a rule block, not a human-only step, so it stays out of the manual guide.

**W4. Branch protection (A4).** Only when the audit fails with `belum diproteksi` (HTTP 404: the plan allows protection).
- For each unprotected repo, pick the required check: `validate` for `claude-cowork`, otherwise the CI job name from the repo's `.github/workflows/`. No CI job: protect without `--check`, and say so.
- Run `scripts/setup-branch-protection.sh <repo> --branch <default> [--check <job>]` (dry run). Show the request.
- Apply with `--apply`. Do the same for `development`, `staging`, and `production` when they exist.
- HTTP 403 means the plan has no protection: the step fails with `nunggu H1`. Do not change `branch_protection` in `registry/repos.yml` on your own; propose it under "Decisions for the reviewer" in a registry PR only when the human asks.

**W5. CI (A5).** A red run on `main`: read the job log (`gh api repos/<control>/actions/jobs/<id>/logs`). Report the failing test in one line. Fix it through a PR only when the cause is in setup files (settings, template, registry). Otherwise report it.

**W6. Project sync (A6).** Needs H5 and H6.
- `project.number` is 0 and the human gave the Project owner and number: open a PR that sets `project.owner` and `project.number` in `registry/policy.yml`. Wait for the merge.
- Dispatch: `gh api -X POST repos/alta-prima-indonesia/claude-cowork/actions/workflows/project-sync.yml/dispatches -f ref=main`.
- Wait for the run with the Monitor tool (poll `actions/workflows/project-sync.yml/runs?per_page=1` until `status` is `completed`), then read `conclusion`. On failure, read the log and report it in one line.

**W7. Runner session (A7).**
- No runner, or it is archived: call `create_session` with:
  - `source_url`: `https://github.com/alta-prima-indonesia/claude-cowork`,
  - `title`: `Pipeline runner (scheduled tasks)`,
  - `environment_id`: the id of `altaprima-default` from `list_environments`,
  - no `prompt`.
- Then print the two H9 messages in code blocks. The human types them in the runner. Build the attach message from `registry/repos.yml`:
  ```text
  Attach these repositories to this session with add_repo: <each active repo except claude-cowork> with access "push"; <each frozen repo> with access "read".
  ```
  Copy the pr-watch line from `claude-cowork/docs/scheduled-tasks.md` → "Current state" → "PR watch setup", exactly.
- Wait until the human says both are typed. Then re-run the audit; H9 ends in `error` (the pr-watch line cannot be checked) once every repo is attached.
- An old runner stays until the human confirms the new one works. Then archive it with `archive_session`.

**W8. Scheduled tasks (A8).** Prompts: the first `text` block under each task in `claude-cowork/docs/scheduled-tasks.md`, copied exactly.
- Missing task: `create_trigger` with `name`, `prompt`, `persistent_session_id` = runner, `initiation: "human_request"`, and `cron_expression`:
  - `Pipeline: batch`: `0 * * * *` (the server anchors it to the creation minute),
  - `Pipeline: onboarding scan`: `CRON_TZ=Asia/Jakarta 30 14 * * *`.
- Prompt differs: `update_trigger` with `prompt` only.
- Bound to another session: `update_trigger` cannot rebind. Call `delete_trigger`, then `create_trigger` as above. Say in the plan that this drops the run history.
- Disabled: enable it with `update_trigger` `enabled: true` only after H9 is done. A run in a runner without its repos stops at setup. Until then, set new tasks to `enabled: false`.

**W9. Registry (A9).** Repos in the org but not in `registry/repos.yml`: start an onboarding run with the `run-pipeline` skill (`onboarding`). One repo per run.

### Finish

1. Re-run the audit and reply with the table.
2. When H9 is done and the tasks are enabled, start one batch run with `run-pipeline` (`batch`). Its summary carries `guard: <value>`; the next `status` run uses it for H8.
3. List each PR the wizard opened, with its link, for the human to merge. Give merge feedback as `CLAUDE.md` → "Merge feedback" says: subscribe to PRs this session opened in `claude-cowork`; for PRs in other repos, use `send_later` checks.
4. List the rule blocks under **Diblok aturan**: actions the guard hook or `CLAUDE.md` stopped (for example a collaborator invitation), each with the rule that stops it.
5. End with the open H steps, one line each, and point to `/workflow-setup guide`.

## Outputs

- `status`, `guide`: one chat reply. No writes.
- `wizard`: labels, collaborator invitations, branch protection, PRs, a runner session, scheduled tasks, as the plan listed. One chat reply with the final audit.

## Stop conditions

- After the reply.
- The human does not type `jalan`: stop with no changes.
- A step fails twice: report its output, mark it in the final table, and continue with the next step.
- GitHub access fails for the control repo: stop and report it. Read the `github.access` page with `read_documentation`.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "The settings forbid it, so it goes in the human guide." | The guide holds only steps no AI can do. A rule-only block stays in the wizard. |
| "I'll ask before each label and task." | One `jalan` covers the plan. Ask again only for an action outside the plan. |
| "The runner is new; I'll send it the attach message myself." | The platform grants push access only on a request a person typed in that session. Print it for the human. |
| "The task is bound to the old runner; I'll leave it." | Runs then go to a session without the repos. Rebind it: delete, then create. |
| "The token is needed; I'll ask the human to paste it." | Never handle secrets. The human saves it as an Actions secret; the wizard checks only that it exists. |
| "Protection failed with 403; I'll retry." | 403 means the Free plan. The step waits for H1. |
| "The audit should say what to do next." | The audit reports pass, fail, or error with a reason. The wizard acts; `watchtower` advises. |
| "The guard blocks the invite; I'll call the API another way." | A guard block is a safety rule. Report it under **Diblok aturan**; never route around it. |

Original to claude-cowork. No upstream source.
