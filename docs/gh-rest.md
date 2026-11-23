# GitHub REST equivalents

Cloud sessions block GitHub GraphQL. A blocked call fails with `HTTP 403: GitHub GraphQL is not available from Claude Code sessions`. Many `gh issue`, `gh pr`, `gh label`, and `gh repo` subcommands call GraphQL. Some work, some do not, and this changes between `gh` versions. Use `gh api` with REST paths for every GitHub call in a cloud session.

Verified on 2026-11-23 in a cloud session: `gh issue list`, `gh issue view`, and `gh pr checks` return 403. `gh api repos/...` and `gh api -X GET search/...` work.

The issues endpoints also return PRs. Drop them with `select(.pull_request | not)` when you need issues only. REST field names use snake_case: `html_url`, `created_at`, `updated_at`, `merged_at`, `state_reason`, `head.ref`, `draft`.

| Instead of | Use |
|---|---|
| `gh issue list --label L --state S` | `gh api --paginate "repos/$R/issues?labels=L&state=S&per_page=100"` |
| `gh issue list --search "..."` | `gh api -X GET search/issues -f q="repo:$R is:issue ..."` |
| `gh issue view N --comments` | `gh api repos/$R/issues/N` and `gh api --paginate repos/$R/issues/N/comments` |
| `gh issue create` | `gh api repos/$R/issues -f title=... -f body=... -f 'labels[]=L'` |
| `gh issue edit N --add-label L` | `gh api repos/$R/issues/N/labels -f 'labels[]=L'` |
| `gh issue edit N --remove-label L` | `gh api -X DELETE repos/$R/issues/N/labels/L` |
| `gh issue edit N --body ...` | `gh api -X PATCH repos/$R/issues/N -f body=...` |
| `gh issue comment N --body ...` | `gh api repos/$R/issues/N/comments -f body=...` |
| `gh issue close N --reason completed` | `gh api -X PATCH repos/$R/issues/N -f state=closed -f state_reason=completed` |
| `gh pr list --state open` | `gh api --paginate "repos/$R/pulls?state=open&per_page=100"` |
| `gh pr list --head B` | `gh api "repos/$R/pulls?state=all&head=<owner>:B"` |
| `gh pr list --state merged --search "merged:>=D"` | `gh api -X GET search/issues -f q="repo:$R is:pr is:merged merged:>=D"` |
| `gh pr view N` | `gh api repos/$R/pulls/N` |
| `gh pr diff N` | `gh api repos/$R/pulls/N -H 'Accept: application/vnd.github.diff'` |
| `gh pr view N --json files` | `gh api --paginate repos/$R/pulls/N/files --jq '.[].filename'` |
| `gh pr checks N` | `gh api "repos/$R/commits/<head sha>/check-runs" --jq '.check_runs[] \| {name, status, conclusion}'` |
| `gh pr create` | `gh api repos/$R/pulls -f title=... -f head=B -f base=... -f body=...` (draft: `-F draft=true`) |
| `gh pr edit N --body ...` | `gh api -X PATCH repos/$R/pulls/N -f body=...` |
| `gh pr comment N --body ...` | `gh api repos/$R/issues/N/comments -f body=...` |
| `gh pr review N --comment -b ...` | `gh api repos/$R/pulls/N/reviews -f event=COMMENT -f body=...` (never `APPROVE`) |
| `gh pr ready N` | `gh api -X POST repos/$R/pulls/N/ccr/ready_for_review` |
| `gh label list` | `gh api --paginate "repos/$R/labels?per_page=100" --jq '.[].name'` |
| `gh label create L --color C` | `gh api repos/$R/labels -f name=L -f color=C` |
| `gh repo view` | `gh api repos/$R` |
| `gh repo list <org>` | the `list_repos` tool filtered to `<org>/` (`orgs/*` is blocked) |

`gh run list` uses REST and works. The GitHub MCP tools (`mcp__github__*`) also work, where an agent has them.
