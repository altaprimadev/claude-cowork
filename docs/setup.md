# Setup: from zero to pilot

Do these steps in order. Each step lists who does it.
The agent never runs the scripts in this repo against the org. Humans run them.

## 1. Agent identity (org admin)

- [ ] Create a company Claude account for the agent. Use a Team or Enterprise seat so org managed settings apply.
- [ ] Create a GitHub machine user, for example `altaprima-agent`. Turn on 2FA. Store its recovery codes in the company vault.
- [ ] Add the machine user to the org with **write** access to managed repos only.
  - Never give it admin rights.
  - Never add it to CODEOWNERS.
  - Never add it to a team that can approve.
- [ ] Connect the agent Claude account to GitHub as the machine user. Install the Claude GitHub App on `claude-cowork` and on every managed repo. Event triggers need the app (Q2).

## 2. GitHub integrity (repo admin, per repo)

- [ ] Fill in `.github/CODEOWNERS` with a human team. Replace `<owner-team>`.
- [ ] Create the labels:

  ```bash
  scripts/setup-labels.sh altaprimadev/claude-cowork altaprimadev/<repo>
  ```

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

## 3. Cloud environment (org admin, claude.ai/code)

- [ ] Create a hosted environment named `altaprima-default`.
- [ ] Network: use an allowlist, not full access. Allow only:
  - `github.com`, `api.github.com`, `codeload.github.com`, `objects.githubusercontent.com`
  - `registry.npmjs.org`, `bun.sh`
  - `cdn.playwright.dev`, `playwright.download.prss.microsoft.com` (only for repos with E2E)
  - `binaries.prisma.sh` (only for Prisma repos)
- [ ] Secrets: add none by default. If a repo needs a test secret, use a staging-only value.
- [ ] Setup script: install Bun if the image lacks it (`curl -fsSL https://bun.sh/install -o /tmp/bun-install.sh && bash /tmp/bun-install.sh`). Pin the version.
- [ ] Self-hosted environment: create one only for repos that need a private network or heavy builds. Start the runner with `--trust-workspace false`.

## 4. Guard hook in managed settings (org admin)

Repo hooks do **not** load in multi-repo hosted sessions (`docs/open-questions.md`, Q4). Every agent session is multi-repo, so install the hook at org level as well.

- [ ] In the org's server-managed Claude Code settings, add:

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

## 5. Permissions for unattended runs (org admin)

Scheduled-task runs start in auto mode (Q5). They still stop on `ask` rules. Repo permission rules do not load in multi-repo sessions (Q4).

- [ ] Copy `permissions.allow` and `permissions.deny` from `.claude/settings.json` into the org managed settings. Include every `Skill(<name>)` rule.
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

## 9. CI for this repo (repo admin)

- [ ] Add a workflow that runs `python3 scripts/validate-config.py` and `python3 -m pytest tests/`. Make it a required check on `main`.

## 10. Usage tracking per task (operator)

- [ ] For each brief, record: issue link, sessions used, approximate token or usage cost from the claude.ai usage page, and outcome.
- [ ] Keep the log in the daily report issue, or in a GitHub Project field.
- [ ] Review it weekly. Lower `max_parallel_sessions` in `registry/policy.yml` if usage is too high.
