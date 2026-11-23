# Setup: from zero to pilot

Do these steps in order. Each step lists who does it.
The agent never runs the scripts in this repo against GitHub. Humans run them.

## Current state (2026-11-23)

| Item | State |
|---|---|
| Repo owner | **Organization `alta-prima-indonesia`** since 2026-11-23. The repos moved from the personal account `altaprimadev`. `altaprimadev/apsy-api` (frozen) stays under `altaprimadev`. |
| GitHub plan | Free. The org Team plan payment is pending. |
| Branch protection | **Not active.** Private repos on a Free org cannot use it. `gh api repos/<repo>/branches/<branch>/protection` returns 403 "Upgrade to GitHub Pro" for `main` and `development` of `claude-cowork`, `alta-prima-admin-back-end`, and `alta-prima-admin-prisma` (checked 2026-11-23). |
| CODEOWNERS | `@adhemukhlis` (a human collaborator) |
| Network access | **Full** (unrestricted) by owner decision. Outbound data is not restricted. |
| Autonomy cap | Repos with `branch_protection: unavailable` in `registry/repos.yml` may run above 0 under the compensating rules in `CLAUDE.md`. Every other unprotected repo stays at 0. |
| Agent GitHub identity | **`altaprimadev`, with admin rights on every `alta-prima-indonesia` repo** (`permissions.admin: true`, checked 2026-11-23). No separate machine user. Accepted risk: the agent holds admin rights, so the guard hook and `CLAUDE.md` are the only barriers. |
| Agent Claude account | **One shared Claude account** runs both agent sessions and human chat sessions. Its GitHub connection is `altaprimadev`. The human reviewer `adhemukhlis` approves only in GitHub web. |
| Claude plan | Team Standard now. **Team Premium** (Max-level usage) for the account that runs agents, coming soon. The team stays on a Team plan so managed settings keep the guard hook active in multi-repo sessions. |

Without branch protection, the gates rest on instructions, the guard hook, and a human who merges by hand. That breaks the brief's rule that the platform enforces integrity. The pilot first accepted this gap because every repo ran at autonomy 0. That reason no longer holds: `alta-prima-admin-back-end` and `alta-prima-admin-prisma` now run at autonomy 2 under the compensating rules, with an agent identity that holds admin rights. The account owner must re-confirm this risk or lower autonomy.

When the `alta-prima-indonesia` org gets the Team plan:

1. Apply branch protection (step 2).
2. Remove the autonomy cap rows above.
3. Raise autonomy per repo (step 8).

The org adds teams and per-repo access for a machine user. Team-plan protection rules arrive with the paid plan.

## 1. Agent identity (account owner)

- [ ] Create a company Claude account for the agent. Use a Team or Enterprise seat, so Claude managed settings apply.
- [ ] Create a GitHub machine user for the agent, for example `altaprima-agent`.
  - Turn on 2FA.
  - Store its recovery codes in the company vault.
  - Never reuse `altaprimadev` or a person's account.
- [ ] Turn on 2FA for `altaprimadev` and for every human reviewer.
- [ ] As an `alta-prima-indonesia` org owner, give the machine user access to each managed repo.
  - Grant write access, not admin.
  - Never make the machine user a code owner.
- [ ] Connect the agent Claude account to GitHub as the machine user. Install the Claude GitHub App on `claude-cowork` and on every managed repo. Event triggers need the app (Q2).

## 2. GitHub integrity (repo owner, per repo)

Branch protection needs the Team plan for private org repos. Run the protection script as an org owner or a repo admin.

- [ ] Set `.github/CODEOWNERS` to human reviewers: GitHub usernames, or `@org/team` after a move to an organization. Invite each reviewer as a collaborator.
- [ ] Create the labels:

  ```bash
  scripts/setup-labels.sh alta-prima-indonesia/claude-cowork alta-prima-indonesia/<repo>
  ```

- [ ] Set up the GitHub Project board (once, for all repos):
  1. Signed in as `altaprimadev`, create a Project (Profile → Projects → New project). Note its number from the URL (`/users/altaprimadev/projects/<number>`). Project #2 still lives there after the move; a Project in the `alta-prima-indonesia` org needs a new number and owner in `registry/policy.yml`.
  2. Give the single-select field `Status` these options: `Brief`, `Design`, `Draft`, `Backlog`, `Ready`, `In progress`, `Blocked`, `Ready to merge`, `In review`, `Done`.
  3. Create a **classic** personal access token as `altaprimadev` (Settings → Developer settings → Personal access tokens → Tokens (classic)). Scopes: `project` and `repo`. Set an expiry. Fine-grained tokens cannot reach Projects owned by a user account. After the Project moves to the org, switch to a fine-grained token with Projects read/write and Issues read.
  4. Save it as the Actions secret `PROJECT_SYNC_TOKEN` in `claude-cowork` (Settings → Secrets and variables → Actions). Agents never see it.
  5. Set `project.number` in `registry/policy.yml` through a PR. `0` keeps the sync off.
  6. Run the workflow once: Actions → Project sync → Run workflow. Check that items appear.
- [ ] Preview branch protection with a dry run, then apply it:

  ```bash
  scripts/setup-branch-protection.sh alta-prima-indonesia/<repo> --check "<ci-check-name>"
  scripts/setup-branch-protection.sh alta-prima-indonesia/<repo> --check "<ci-check-name>" --apply
  ```

  This enables:
  - required PR,
  - at least 1 approval,
  - dismiss stale reviews,
  - code owner review,
  - strict required checks,
  - enforce for admins,
  - no force push,
  - no deletion.
- [ ] Protect `production` the same way when a repo uses a production branch.
- [ ] For `claude-cowork` itself, use the check from this repo's CI (step 9).
- [ ] Or import the ruleset templates in `templates/rulesets/` per target repo (Settings -> Rules -> Rulesets -> Import a ruleset): `development-protector.json` and `staging-protector.json`. They block deletion and force-push and require a PR, with 0 approvals. They require no status check, because the CI job name differs per repo. Add a `required_status_checks` rule with the repo's job name (`integration_id: 15368`). Use Merge, not Squash, on promotion PRs (`development` -> `staging` -> `main`).

## 3. Cloud environment (account owner, claude.ai/code)

Open it from a session: the cloud environment menu in the session's title bar → **Edit**, or create a new environment from the same menu. Reference: https://code.claude.com/docs/en/cloud-environments#network-access

- [ ] Create a hosted environment named `altaprima-default`. Use it for every scheduled task.
- [ ] **Network access:** choose **Full** (unrestricted). Decision by the account owner, 2026-11-18: agents need outside access (docs, APIs, registries), and data exfiltration is an accepted risk.
  - The guard hook still blocks network-to-shell pipes (`curl | sh`).
  - It does not block outbound data, such as `curl -d @file https://...`.
  - To tighten later, switch to **Limited** with **Allow package managers** ticked, and add hosts under **Allowed domains** as skills need them.

- [ ] **Environment variables and secrets:** add none. The pipeline needs no secret in v0.1.0. Setup scripts cannot read saved variables.
- [ ] **Setup script:** the hosted image already has Bun (1.4.4 observed on 2026-11-18) and Python 3. Keep the script as a guard only:

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  command -v python3 >/dev/null || { echo "python3 missing: guard hook cannot run" >&2; exit 1; }
  if ! command -v bun >/dev/null; then
    curl -fsSL https://bun.sh/install -o /tmp/bun-install.sh
    bash /tmp/bun-install.sh
  fi
  ```

- [ ] Self-hosted environment: create one only for repos that need a private network or heavy builds. Start the runner with `--trust-workspace false`.

## 4. Guard hook in managed settings (Claude org admin)

Repo hooks do **not** load in multi-repo hosted sessions (`docs/open-questions.md`, Q4). Every agent session is multi-repo, so install the hook at org level as well.

- [ ] In the Claude organization's server-managed Claude Code settings, add:

  ```json
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"$(find \"$CLAUDE_PROJECT_DIR\" -maxdepth 3 -path '*/claude-cowork/.claude/hooks/guard_bash.py' -print -quit)\"",
              "timeout": 10
            }
          ]
        }
      ]
    }
  }
  ```

  The command finds the `claude-cowork` clone under the session's start directory. If the guard is missing, the command fails. Python reports the error, and the hook does not block (fail-open). Branch protection still holds.
- [ ] Add the compaction hook in the same `hooks` object. It sets what a compaction summary keeps (`CLAUDE.md` -> "Lean context"), and it never blocks:

  ```json
  "PreCompact": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"$(find \"$CLAUDE_PROJECT_DIR\" -maxdepth 3 -path '*/claude-cowork/.claude/hooks/pre_compact.py' -print -quit)\"",
          "timeout": 10
        }
      ]
    }
  ]
  ```
- [ ] Optional, in the runner's cloud environment variables: `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`. Auto-compaction then starts at half of the window, before old runs crowd the context. It can only lower the threshold. A new session reads it.
- [ ] Self-hosted runners: add the same block to the host's `~/.claude/settings.json`.
- [ ] Verify in a pilot session: `git push origin main` must be blocked with a `BLOCKED by .claude/hooks/guard_bash.py` message.

## 5. Permissions for unattended runs (Claude org admin)

Scheduled-task runs start in auto mode (Q5). They still stop on `ask` rules. Repo permission rules do not load in multi-repo sessions (Q4).

- [ ] Copy `permissions.allow` and `permissions.deny` from `.claude/settings.json` into the Claude organization managed settings. Include every `Skill(<name>)` rule.
- [ ] Add no `ask` rule for commands that scheduled tasks need.
- [ ] The `mcp__claude-code-remote__*` allow rules cover scheduled tasks, sessions, and PR subscriptions. Without them, the auto mode classifier can refuse `delete_trigger` and `archive_session` even after a human asked. Server-side limits still apply: only the bound session can change a task's prompt, and only a human can attach push repos or give the pr-watch instruction.
- [ ] Keep `deny` rules for `gh pr merge`, `gh repo delete`, and force pushes.
- [ ] Add these MCP `deny` rules **org-wide**. No human or agent should merge or run workflows through Claude: `mcp__github__merge_pull_request`, `mcp__github__enable_pr_auto_merge`, `mcp__github__actions_run_trigger`.
- [ ] The other MCP denies in `.claude/settings.json` (`pull_request_review_write`, `push_files`, `create_or_update_file`, `delete_file`) stay repo-level. Managed settings apply to every org session, and humans use these tools in interactive work. The pipeline does not use any `mcp__github__*` tool.
- [ ] After a change to `.claude/hooks/guard_bash.py`, no admin step is needed: the managed hook runs the script from the `claude-cowork` clone, and each run pulls `main` first. Re-copy the `deny` list only when it changes.

## 6. How sessions use claude-cowork

- Main repo: `alta-prima-indonesia/claude-cowork`, always first.
- Additional repos: the active managed repos.
- Every prompt starts with "Read `claude-cowork/CLAUDE.md`". The orchestrator then routes work to the fixed agents in `.claude/agents/`.
- Agents load skills from `.claude/skills/`. If the Skill tool cannot find a skill, they read the file directly.

## 7. Scheduled tasks (operator)

- [ ] Create the five tasks in `docs/scheduled-tasks.md` with the agent account. Paste each prompt exactly.
- [ ] Set the GitHub event triggers and filters as listed.

## 8. Pilot: autonomy 0 → 1

1. Onboard one low-risk repo. Merge its onboarding PR and its registry PR. Autonomy is 0.
2. Run one week at autonomy 0. Agents only review and report. Check:
   - [ ] Reviews have useful findings with real evidence.
   - [ ] The daily report is correct.
   - [ ] The guard hook blocks a test push to `main` (step 4).
   - [ ] Record which agents, skills, and hooks were active in a multi-repo session. Update `docs/open-questions.md` (Q4 gap).
3. Raise the repo to autonomy 1, in both `registry/repos.yml` and its `.agent/profile.yml`. File 3–5 `size:small` briefs.
4. Review each agent PR as a normal PR. Track the results below.
5. Go to autonomy 2 only after at least 10 merged agent PRs with no rollback.

## 9. CI for this repo (repo owner)

- [x] `.github/workflows/ci.yml` runs on every PR and on pushes to `main`:
  - `scripts/validate-config.py`,
  - `pytest tests/`,
  - a syntax check of `scripts/*.sh`.
- [ ] After Pro/Team is active, make the `validate` job a required check:

  ```bash
  scripts/setup-branch-protection.sh alta-prima-indonesia/claude-cowork --check validate
  ```
- [ ] Or apply the ruleset template `templates/rulesets/main-protector.json` (Settings -> Rules -> Rulesets -> Import a ruleset). It blocks deletion and force-push on `main`, requires a PR, and requires the `validate` check from GitHub Actions. It requires 0 approvals: Gate 2 rests on the agent rules and the guard hook. Repository admins can bypass it through a PR.

## 10. Usage tracking per task (operator)

- [ ] For each brief, record: issue link, sessions used, approximate token or usage cost from the claude.ai usage page, and outcome.
- [ ] Keep the log in the daily report issue, or in a GitHub Project field.
- [ ] Review it weekly. Lower `max_parallel_sessions` in `registry/policy.yml` if usage is too high.
