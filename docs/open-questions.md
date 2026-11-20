# Open questions: verification results

Checked against official documentation on 2026-11-18.
Status values: **verified**, **partially verified**, **not verified**.
Where a point is not verified, the design uses the safest assumption.

## Q1. Hook and agent format

**Status: verified.**

Findings:
- Hooks live under `hooks.<Event>[]` in `.claude/settings.json`. Each entry has `matcher` and `hooks[]`. Each hook has `type: "command"`, `command`, and an optional `timeout` in seconds (default 600).
- A PreToolUse hook blocks a tool with exit code 2. Claude receives stderr as the reason. JSON output with `hookSpecificOutput.permissionDecision: "deny"` also blocks.
- For Bash, stdin JSON holds `tool_name: "Bash"` and `tool_input.command`.
- `${CLAUDE_PROJECT_DIR}` is the project root where the session started.
- Subagent frontmatter fields:
  - Required: `name`, `description`.
  - Optional: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `autoCompactWindow`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `omitClaudeMd`, `effort`, `isolation`, `color`, `initialPrompt`, `experimental`.
  - Unknown fields are ignored silently.
- `skills` preloads the full skill content into the subagent at startup. The docs prefer it over listing `Skill` in `tools`.
- SKILL.md frontmatter fields: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility`.

Design impact:
- Every agent preloads its core skill with `skills:`.
- Stack packs vary per repo. Agents load them at runtime with the Skill tool, or read the file directly as a fallback.
- `guard_bash.py` blocks with exit code 2 and a reason on stderr.

Sources:
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/skills

## Q2. GitHub events that trigger cloud scheduled tasks

**Status: verified.** The feature is in research preview.

Findings:
- Pull request events: opened, closed, assigned, labeled, synchronized, and other updates.
- Release events: created, published, edited, deleted.
- Issue events: opened, edited, closed, reopened, labeled, assigned, and other updates.
- A trigger can listen to one action, such as `pull_request.opened`, or to every action in a category.
- PR filters: author, title, body, base branch, head branch, labels, draft, merged. All conditions must match.
- No issue filters are documented. The prompt must check labels itself.
- The Claude GitHub App must be installed on the repository.
- Every event starts a new session.
- Per-task and per-account hourly caps apply. Events over the cap are dropped.

Design impact:
- Event triggers start the work. Hourly schedules catch dropped events.
- Every prompt re-reads labels before it acts, so duplicate or dropped events are harmless.
- See `docs/scheduled-tasks.md`.

Source: https://code.claude.com/docs/en/routines

## Q3. Public API to create cloud sessions

**Status: partially verified.**

Findings:
- A per-task trigger endpoint exists: `POST https://api.anthropic.com/v1/claude_code/routines/<trigger_id>/fire`.
  - It needs a per-task bearer token and the header `anthropic-beta: experimental-cc-routine-2026-04-01`.
  - The optional `text` field reaches the session as an untrusted `<routine-fire-payload>` block.
  - It starts a new session and returns the session URL.
  - It is experimental, claude.ai only, and has no SDK support.
- The CLI creates a cloud session with `claude --cloud "<task>"`. It queues a follow-up with `claude -p "<msg>" --cloud <session-id>`.
- No general "create session" REST API is documented.
- Managed Agents is a separate product. It does not create claude.ai/code sessions.

Design impact:
- v0.1.0 uses only GitHub event triggers and cron schedules. It needs no API.
- The `/fire` endpoint is an option for later, for example behind a webhook relay.
- A fire token is a secret. It never goes in this repo.

Sources:
- https://code.claude.com/docs/en/routines
- https://platform.claude.com/docs/en/api/claude-code/routines-fire
- https://code.claude.com/docs/en/claude-code-on-the-web

## Q4. Project config loading in cloud sessions

**Status: verified, with one gap.**

Findings:
- **One repository, hosted:** these load: `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `.mcp.json`, and the hooks and permission rules in `.claude/settings.json`.
- **Plugins:** plugins enabled with `enabledPlugins` are not installed. User `~/.claude/` settings are not read.
- **Several repositories, hosted:**
  - The session starts in the directory above the clones.
  - From each repo's `.claude/settings.json` it reads only `enabledPlugins` and `extraKnownMarketplaces`.
  - It does **not** read permission rules, hooks, or `env`.
  - Hooks still run from the **organization's server-managed settings**.
- **Self-hosted with `--capacity 1`:** the session starts in the first repository. Only that repository's `.claude/settings.json` applies.
- **Self-hosted with `--trust-workspace false`:**
  - It drops permission grants committed to the repo, and `.mcp.json` servers.
  - Allow rules then belong in the runner host's `~/.claude/settings.json`.
  - The docs do not say that this flag drops hooks.
- **Gap (not verified):** the docs do not state whether `CLAUDE.md`, agents, and skills from every clone load in a hosted multi-repo session.

Design impact (safest assumption):
- **This is the main open risk.** Every agent session is multi-repo: `claude-cowork` plus the target repo. In those sessions, the hooks and permissions in this repo's `.claude/settings.json` do **not** apply.
- Install `guard_bash.py` as an org server-managed hook. On self-hosted runners, add it to the host's `~/.claude/settings.json`. See `docs/setup.md`, step 4.
- Branch protection stays the first layer. It does not depend on any hook.
- Every scheduled-task prompt starts with "Read `claude-cowork/CLAUDE.md` and follow it." This works even if `CLAUDE.md` does not load on its own.
- If the Skill tool cannot find a skill, the agent reads its `SKILL.md` file directly.
- The target repo's `.claude/` may load next to ours. Precedence decides conflicts: platform > hook > `claude-cowork/CLAUDE.md`.
- Pilot check: run one multi-repo session and record which agents, skills, and hooks were active. See `docs/setup.md`, step 8.

Sources:
- https://code.claude.com/docs/en/cloud-environments
- https://code.claude.com/docs/en/settings#settings-in-cloud-sessions
- https://code.claude.com/docs/en/self-hosted-environments-configuration
- https://code.claude.com/docs/en/self-hosted-environments-reference

## Q5. Unattended scheduled tasks and permission prompts

**Status: verified, with one gap.**

Findings:
- A scheduled-task run starts in auto mode when available. Otherwise it keeps the mode it launched in.
- A run still stops and waits on an action that matches an `ask` rule. It also waits when auto mode hits its repeated-block thresholds.
- Cloud sessions ignore `defaultMode: "bypassPermissions"` and `"dontAsk"`. File edits are pre-approved in cloud sessions.
- `Skill(name)` matches one skill exactly. `Skill(name *)` matches a prefix.
- The Skill tool can prompt for skills that set `allowed-tools`, `disallowed-tools`, or `hooks`. An allow rule `Skill(name)` avoids that prompt.
- An `allowed-tools` grant lasts only for the turn that invoked the skill.
- **Gap (not verified):** whether auto mode alone approves those Skill prompts.

Design impact:
- Skills declare no `allowed-tools`, `disallowed-tools`, or `hooks`. One exception: `usage-status` declares `allowed-tools` for `list_events` and its script, because the orchestrator calls it before each delegation. `watchtower` warns on any other skill that declares one.
- `.claude/settings.json` still allows `Skill(<name>)` for every skill. `scripts/validate-config.py` enforces this.
- Repo permission rules do not load in multi-repo sessions (Q4). Add the same allow rules to the org's managed settings. See `docs/setup.md`, step 5.
- Do not add `ask` rules for commands that scheduled tasks need.

Sources:
- https://code.claude.com/docs/en/routines
- https://code.claude.com/docs/en/permission-modes
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/tools-reference

## Known facts confirmed

| Fact | Status | Source |
|---|---|---|
| `/loop` and session-scoped tasks stop with the container | verified | https://code.claude.com/docs/en/claude-code-on-the-web ("Environment expired") |
| Hosted containers have no command sandbox. `sandbox.filesystem` and `sandbox.network` rules are not enforced | verified | https://code.claude.com/docs/en/changelog, https://code.claude.com/docs/en/settings |
| Self-hosted runners should use `--trust-workspace false` | verified: the flag exists and drops repo permission grants | https://code.claude.com/docs/en/self-hosted-environments-reference |

## Account and plan constraint (2026-11-18)

**Status: verified.**

- `altaprimadev` is a personal GitHub user account, not an organization. The brief assumed an organization on the Team plan.
- Without Pro or Team, private repos cannot use branch protection. Layer 1 (platform integrity) is therefore missing.

Design impact (safest assumption):
- `CLAUDE.md` caps effective autonomy at `0` for any repo whose default branch is unprotected.
- CODEOWNERS uses usernames (`@adhemukhlis`) instead of teams.
- The machine user joins each repo as a collaborator. On a personal account, collaborators always get write access.
- Revisit when the account moves to Pro, or to an organization on the Team plan. See `docs/setup.md`, "Current state".

## Claude plan and account constraint (2026-11-18)

**Status: decision recorded. The Max behavior is not verified.**

- The Claude plan is Team Standard now. Decision (2026-11-18): move the agent account to **Team Premium** instead of individual Max. This keeps managed settings and gives Max-level usage.
- Server-managed settings are an organization feature (Team or Enterprise). An individual Max account has none.
- Without managed settings, no verified way exists to load the guard hook or the allow rules in multi-repo sessions (Q4).
- Decision (account owner, 2026-11-18): one Claude account runs agent sessions. Its GitHub connection is `altaprimadev`, the repo owner. No machine user is used. This deviates from the brief: no dedicated Claude account, and no GitHub machine user.
- The approval split still holds: the agent authors PRs as `altaprimadev`, and the human `adhemukhlis` approves. GitHub blocks self-approval, so `altaprimadev` cannot approve its own PRs.
- Accepted risk: the agent holds owner (admin) rights. The platform cannot limit it. The guard hook and `CLAUDE.md` are the barriers. Agent actions and human admin actions share one name in the audit log.
- Mitigation: the guard hook also blocks admin actions: `gh repo edit/archive/rename`, `gh secret`/`gh variable` changes, `gh auth token`, and non-GET `gh api` calls to repo settings, collaborators, hooks, keys, secrets, environments, transfer, and account settings.
- The hook only works where it loads. In multi-repo sessions that requires Claude managed settings (Team plan). After a move to individual Max, multi-repo agent sessions have no hook. Keep autonomy 0 until that gap is closed.

Consequences:
- Agent sessions and human sessions share one usage quota and one session list.
- Interactive sessions on that account also act on GitHub as `altaprimadev`.

Safe path:
- Decision (owner, 2026-11-19): a repo may run above autonomy 0 without branch protection when its registry entry has `branch_protection: unavailable`. Compensating rules in `CLAUDE.md`: agent PRs target the integration branch, agents never push to `development`, `staging`, or release branches, and never merge. The guard hook blocks those pushes and API merges. Accepted risk: where the hook does not load, only instructions stop an agent with admin rights from merging.
- Before raising autonomy on Max, test in a pilot whether an environment setup script can install the guard hook in multi-repo sessions. Record the result here.
- If agent usage hits plan limits, move the agent to its own Claude account.

## Observed in this build session

The build session ran with `claude-cowork` as its only repo. Its `.claude/settings.json` hook was active. It also blocked a `git push -f` by the build agent itself. The hook blocked a heredoc that only mentioned `gh pr merge` as text. That false positive was fixed: heredoc bodies are now treated as data. This observation supports the single-repo row of Q4.
