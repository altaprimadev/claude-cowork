# Human guide: steps no AI session can do

This guide lists only actions that an AI session cannot do at all. The cause is never a permission rule. It is one of these:

- **Payment:** a plan upgrade or seat needs a billing owner and a payment method.
- **Identity:** a new account, 2FA, or recovery codes need a person's email, phone, or authenticator device.
- **Browser consent:** an OAuth or app-install screen needs a signed-in person to click it.
- **No API:** the setting exists only in a web UI. No tool or endpoint reaches it from a session.
- **Human origin:** the platform accepts the request only when a person types it in that session.

The wizard prepares every input for these steps: exact text, JSON, and values. It verifies each step afterwards with `setup_audit.py`, when the step can be verified at all.

| ID | Step | Cause | Verified by the wizard |
|---|---|---|---|
| H1 | GitHub Team plan for the org | Payment | Yes: branch protection stops returning 403 |
| H2 | Claude plan and agent seat | Payment, identity | No: confirm by hand |
| H3 | GitHub machine user with 2FA | Identity | No: confirm by hand |
| H4 | Connect Claude to GitHub, install the Claude GitHub App | Browser consent | Partly: `gh api user` works |
| H5 | GitHub Project board with the `Status` field | No API (Projects need GraphQL, blocked in cloud sessions) | Yes: `project.number` in `registry/policy.yml` |
| H6 | `PROJECT_SYNC_TOKEN` token and Actions secret | Identity (token creation needs sudo mode) | Yes: secret metadata or a successful sync run |
| H7 | Cloud environment `altaprima-default` | No API (`list_environments` reads only) | Partly: the name exists |
| H8 | Org managed settings (hooks and permissions) | No API (admin console only) | Yes: the runner reports `guard: active` |
| H9 | Push repos and the pr-watch line in the runner session | Human origin | Partly: the runner sources list the repos |

## H1. GitHub Team plan

1. Sign in to GitHub as an owner of the `alta-prima-indonesia` org.
2. Open the org → Settings → Billing and plans → upgrade to Team.
3. Tell the wizard "H1 done". The wizard then applies branch protection (W4) and proposes removing the cap rows in `claude-cowork/docs/setup.md` → "Current state".

## H2. Claude plan and agent seat

1. As the Claude org admin, assign the seat that runs agents (Team Premium when available).
2. Keep the org on a Team or Enterprise plan. Managed settings (H8) need it.

## H3. GitHub machine user

1. Create the account, for example `altaprima-agent`, with a company email.
2. Turn on 2FA. Store the recovery codes in the company vault.
3. Accept the org or repo invitation in that account. The wizard sends the invitation (W3) when you name the account.
4. Turn on 2FA for every human reviewer too.

## H4. Connect Claude to GitHub

1. In the agent's Claude account, open https://claude.ai/connect-github and sign in as the machine user (or `altaprimadev` until H3 is done).
2. Install the Claude GitHub App: https://github.com/apps/claude/installations/select_target. Select `claude-cowork` and every active registry repo.

## H5. GitHub Project board

1. In GitHub web, create a Project under the org (or the current owner in `registry/policy.yml` → `project.owner`). Note the number in the URL.
2. Add the single-select field `Status` with these options, in this order: `Brief`, `Design`, `Draft`, `Backlog`, `Ready`, `In progress`, `Blocked`, `Ready to merge`, `In review`, `Done`.
3. Tell the wizard the owner and number. The wizard opens the `registry/policy.yml` PR (W6).

## H6. Project sync token

1. In GitHub web, as the Project owner: Settings → Developer settings → Personal access tokens.
   - Project owned by a user: classic token, scopes `project` and `repo`, with an expiry.
   - Project owned by the org: fine-grained token, Projects read/write and Issues read.
2. In `claude-cowork` → Settings → Secrets and variables → Actions, save it as `PROJECT_SYNC_TOKEN`.
3. Never paste the token in chat. The wizard only checks that the secret exists and that the sync run succeeds.

## H7. Cloud environment

Open a session at claude.ai/code → the environment menu in the title bar → Edit, or create a new one.

1. Name: `altaprima-default`. Use it for every scheduled task and the runner.
2. Network access: **Full** (owner decision, 2026-11-18).
3. Environment variables: none, except the optional `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`.
4. Setup script: paste the script from `claude-cowork/docs/setup.md` → section 3.

## H8. Org managed settings

1. Open the Claude admin console → Claude Code → managed settings.
2. Replace the whole content with the JSON the wizard prints from `claude-cowork/templates/managed-settings.json`.
3. Repeat after every merged PR that changes that template.
4. The wizard verifies it from the runner's next summary: `guard: active`.

## H9. Runner session

The wizard creates the runner session (W7) and prints two messages. Type them yourself in that session, one at a time:

1. The attach message: the active repos with push access, the frozen repos read-only.
2. The pr-watch line from `claude-cowork/docs/scheduled-tasks.md` → "Current state".

A message sent from another session does not count. The platform grants push access and acts on PR events only on a request a person typed in that session.

## Not in this guide, on purpose

These steps stay with humans because of a rule, not a missing capability. The wizard stops at them and names them; they are not setup steps.

| Item | Rule |
|---|---|
| Merge a PR (Gate 1, Gate 2, registry, onboarding) | `claude-cowork/CLAUDE.md` → "Never approve, merge, or deploy" |
| Promote to production (Gate 3) | Same rule |
| Accept a risk, such as autonomy above 0 without branch protection | A business decision; no source states it |
