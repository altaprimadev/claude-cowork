# Setup: from zero to pilot

Do these steps in order. Each step lists who does it.
The agent never runs the scripts in this repo against GitHub. Humans run them.

## Current state (2026-11-18)

| Item | State |
|---|---|
| `altaprimadev` account type | **Personal user account**, not an organization. There are no GitHub teams. |
| GitHub plan | Free. No Pro or Team plan yet. |
| Branch protection | **Not active.** Private repos on a free personal account cannot use it. |
| CODEOWNERS | `@adhemukhlis` (a human collaborator) |
| Network access | **Full** (unrestricted) by owner decision. Outbound data is not restricted. |
| Autonomy cap | Repos with `branch_protection: unavailable` in `registry/repos.yml` may run above 0 under the compensating rules in `CLAUDE.md`. Every other unprotected repo stays at 0. |
| Agent GitHub identity | **`altaprimadev`, the repo owner (admin).** No separate machine user. Accepted risk: the agent holds admin rights, so the guard hook and `CLAUDE.md` are the only barriers. |
| Agent Claude account | **One shared Claude account** runs both agent sessions and human chat sessions. Its GitHub connection is `altaprimadev`. The human reviewer `adhemukhlis` approves only in GitHub web. |
| Claude plan | Team Standard now. **Team Premium** (Max-level usage) for the account that runs agents, coming soon. The team stays on a Team plan so managed settings keep the guard hook active in multi-repo sessions. |

Without branch protection, the gates rest on instructions, the guard hook, and a human who merges by hand. That breaks the brief's rule that the platform enforces integrity. At autonomy 0 agents open no code PRs, so the gap is acceptable for the pilot.

When `altaprimadev` gets Pro, or moves to an organization on the Team plan:

1. Apply branch protection (step 2).
2. Remove the autonomy cap rows above.
3. Raise autonomy per repo (step 8).

Moving to an organization is recommended before onboarding a second repo. It adds teams, per-repo access for the machine user, and Team-plan protection rules.

## 1. Agent identity (account owner)

- [ ] Create a company Claude account for the agent. Use a Team or Enterprise seat, so Claude managed settings apply.
- [ ] Create a GitHub machine user for the agent, for example `altaprima-agent`.
  - Turn on 2FA.
  - Store its recovery codes in the company vault.
  - Never reuse `altaprimadev` or a person's account.
- [ ] Turn on 2FA for `altaprimadev` and for every human reviewer.
- [ ] As `altaprimadev`, invite the machine user as a **collaborator** on each managed repo.
  - A personal account always grants collaborators write access. An organization can grant less.
  - Never make the machine user a code owner.
- [ ] Connect the agent Claude account to GitHub as the machine user. Install the Claude GitHub App on `claude-cowork` and on every managed repo. Event triggers need the app (Q2).

## 2. GitHub integrity (repo owner, per repo)

Branch protection needs Pro (personal account) or Team (organization) for private repos. Run the protection script as `altaprimadev`: collaborators on a personal account are not admins.

- [ ] Set `.github/CODEOWNERS` to human reviewers: GitHub usernames, or `@org/team` after a move to an organization. Invite each reviewer as a collaborator.
- [ ] Create the labels:

  ```bash
  scripts/setup-labels.sh altaprimadev/claude-cowork altaprimadev/<repo>
  ```

- [ ] Set up the GitHub Project board (once, for all repos):
  1. Signed in as `altaprimadev`, create a Project (Profile → Projects → New project). Note its number from the URL (`/users/altaprimadev/projects/<number>`).
  2. Give the single-select field `Status` these options: `Brief`, `Design`, `Draft`, `Backlog`, `Ready`, `In progress`, `Blocked`, `Needs human`, `Done`.
  3. Create a **classic** personal access token as `altaprimadev` (Settings → Developer settings → Personal access tokens → Tokens (classic)). Scopes: `project` and `repo`. Set an expiry. Fine-grained tokens cannot reach Projects owned by a user account. After a move to an organization, switch to a fine-grained token with Projects read/write and Issues read.
  4. Save it as the Actions secret `PROJECT_SYNC_TOKEN` in `claude-cowork` (Settings → Secrets and variables → Actions). Agents never see it.
  5. Set `project.number` in `registry/policy.yml` through a PR. `0` keeps the sync off.
  6. Run the workflow once: Actions → Project sync → Run workflow. Check that items appear.
- [ ] Preview branch protection with a dry run, then apply it:

  ```bash
  scripts/setup-branch-protection.sh altaprimadev/<repo> --check "<ci-check-name>"
  scripts/setup-branch-protection.sh altaprimadev/<repo> --check "<ci-check-name>" --apply
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
- [ ] Self-hosted runners: add the same block to the host's `~/.claude/settings.json`.
- [ ] Verify in a pilot session: `git push origin main` must be blocked with a `BLOCKED by .claude/hooks/guard_bash.py` message.

## 5. Permissions for unattended runs (Claude org admin)

Scheduled-task runs start in auto mode (Q5). They still stop on `ask` rules. Repo permission rules do not load in multi-repo sessions (Q4).

- [ ] Copy `permissions.allow` and `permissions.deny` from `.claude/settings.json` into the Claude organization managed settings. Include every `Skill(<name>)` rule.
- [ ] Add no `ask` rule for commands that scheduled tasks need.
- [ ] Keep `deny` rules for `gh pr merge`, `gh repo delete`, and force pushes.

## 6. How sessions use claude-cowork

- Main repo: `altaprimadev/claude-cowork`, always first.
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
  scripts/setup-branch-protection.sh altaprimadev/claude-cowork --check validate
  ```

## 10. Usage tracking per task (operator)

- [ ] For each brief, record: issue link, sessions used, approximate token or usage cost from the claude.ai usage page, and outcome.
- [ ] Keep the log in the daily report issue, or in a GitHub Project field.
- [ ] Review it weekly. Lower `max_parallel_sessions` in `registry/policy.yml` if usage is too high.
