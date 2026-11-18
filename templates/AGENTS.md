# AGENTS.md

Map of this repository for AI agents. Keep it short and factual. Update it in
the same PR as any change that makes it wrong.

## Summary

<!-- One paragraph: what this repo does, who uses it, where it runs. -->

## Structure

<!-- Key directories and what lives there. One line each. -->

| Path | Purpose |
|---|---|
| `src/` | |
| `tests/` | |

## Commands

The canonical commands live in `.agent/profile.yml` -> `commands`. Copy them here for humans.

| Step | Command |
|---|---|
| Install | `bun install --frozen-lockfile` |
| Lint | `bunx biome ci .` |
| Typecheck | `bunx tsc --noEmit` |
| Test | `bun test` |
| Build | `bun run build` |

## Conventions

<!-- Naming, folder layout, error handling, commit message style. -->

## Sensitive areas

<!-- Files and modules that need extra care: auth, payments, migrations,
     infrastructure, secrets handling. Agents flag any change here in the PR. -->

## How to verify a change

1. Run every command in the table above. All must pass.
2. <!-- Repo-specific checks: seed data, local services, manual smoke steps. -->

## Deployment

<!-- Staging and production flow. Production promotion is human-only (Gate 3). -->
