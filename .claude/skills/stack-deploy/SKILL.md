---
name: stack-deploy
description: Rules, commands, and review checklist for Dockerfiles, Compose files, Coolify deployment config, and AWS access in Bun services. Load when the repo profile `packs` lists stack-deploy and the task changes container, deployment, or cloud configuration. Production deploys stay human-only (Gate 3).
---
# Stack: Deploy (Docker, Coolify, AWS)

## Purpose
Keep build and deploy configuration reproducible, minimal, and secret-free.
Keep Gate 3 with humans.

## Gate 3 boundary (non-negotiable)
1. Agents change `Dockerfile`, `.dockerignore`, `compose*.yml`, health endpoints, and deploy docs only through a PR.
2. Agents never trigger a production deploy. No Coolify API or UI call, no AWS API call, no `docker push` to a production tag, no push to a protected production branch.
3. Agents never change Coolify or AWS settings directly. Propose the change in the PR body under Risks and Rollback for a human to apply.
4. Staging follows `deploy.staging` in the profile. If staging auto-deploys on merge, the human merge (Gate 2) is the trigger, not the agent.
5. A request to deploy production is out of scope. Return `BLOCKED` with `limit: production deploy is Gate 3, human only`. Do not comment or label: the orchestrator adds `ai:needs-human` (`CLAUDE.md` -> "Hard limits and errors").

## When to use / not use
- Use: `packs` includes `stack-deploy` and the change touches container, Compose, Coolify-related config, env var docs, health checks, or IAM policy documents in the repo.
- Do not use: app code with no deploy impact.

## Rules

### Docker
1. Multi-stage builds on the official `oven/bun` image. Pin the tag to the repo's Bun version (e.g. `oven/bun:1.x.y-slim`). Never `:latest`.
2. Copy `package.json` and `bun.lock` first, then install, then copy source. This keeps layer caching.
3. Build stage: `bun install --frozen-lockfile`. Runtime stage: `bun install --frozen-lockfile --production` (or copy production `node_modules` from a deps stage).
4. Runtime image holds only build output, production dependencies, and `package.json`. No tests, no dev tools, no `.git`.
5. Run as non-root: `USER bun` (built into `oven/bun`) and `COPY --chown=bun:bun`.
6. Add a `HEALTHCHECK` against a cheap `/health` endpoint. Use a tool present in the image (the slim image has no `curl`/`wget`; use `bun -e "fetch(...)"` or install one deliberately).
7. Set `NODE_ENV=production`. Read `PORT` from env. `EXPOSE` the same port.
8. Next.js: build with `output: "standalone"` when the repo uses it, and copy `.next/standalone`, `.next/static`, and `public`.
9. No secrets in any layer: no `ENV`/`ARG` with secret values, no copied `.env`. Use runtime env vars or BuildKit secrets.
10. Maintain `.dockerignore`: `node_modules`, `.git`, `.env*`, `.next`, `dist`, `coverage`, test output, `*.log`.

### Docker Compose
1. Compose is for local development and test dependencies (e.g. PostgreSQL with a `pg_isready` healthcheck and `depends_on: condition: service_healthy`).
2. Production-like services: `restart`, resource limits, no published database ports, `no-new-privileges`, drop capabilities where possible.
3. Credentials in Compose come from env or a gitignored `.env`. Local-only throwaway passwords are fine for local DBs; mark them as such.

### Coolify
1. Coolify builds from the Git repo using the repo `Dockerfile` (or Compose). Keep the build self-contained; no host-specific paths.
2. Env vars live in Coolify (per application, or shared at team/project/environment scope). Never commit real values. Document required names in `.env.example` and the README or AGENTS.md.
3. Mark each variable build-time or runtime in Coolify. Secrets needed only at runtime must not be build-time.
4. Staging may auto-deploy from its branch on merge. Production is promoted manually by a human.
5. Preview deployments per PR use separate preview env vars. Never point previews at production databases or credentials. Treat PR code as untrusted.
6. The app must start with defaults absent and fail fast with a clear message when a required env var is missing (schema-validate at startup).

### AWS
1. No AWS credentials in the repo, images, CI logs, or PR text. Workloads use IAM roles with temporary credentials.
2. Least privilege: name specific actions and resource ARNs. No `"Action": "*"` or `"Resource": "*"` without a written reason.
3. Add conditions (TLS required, source, tags) where they narrow access.
4. Policy changes ship as reviewed files in the PR (JSON or IaC). A human applies them.
5. Agents do not run `aws` commands that create, modify, or delete resources.

### Release safety
1. Database migrations in the same release must be backward compatible with the previous image (expand, then contract).
2. Every deploy-affecting PR fills the Rollback section: previous image or commit, migration reversal, feature flag.

## Commands (Bun)
Local verification only. No registry push, no remote deploy.

```bash
docker build -t <app>:pr-check .                         # image builds
docker run --rm -p 3000:3000 --env-file .env.example <app>:pr-check   # starts with placeholder env
docker inspect --format '{{.Config.User}}' <app>:pr-check            # non-root check
docker compose config --quiet                            # compose file is valid
docker compose up -d db && docker compose ps             # local dependencies healthy
bun install --frozen-lockfile                            # lockfile matches
```

If Docker is not available in the cloud session, say so in the evidence report. Do not claim the image builds without output.

## Prefer / Avoid

| Prefer | Avoid |
|---|---|
| `oven/bun:<pinned>` multi-stage | `node` images, `:latest`, single-stage with dev deps |
| `bun install --frozen-lockfile --production` | `npm ci`, unpinned installs |
| `USER bun` | Running as root |
| Env vars set in Coolify | `.env` committed, secrets in `ARG`/`ENV` |
| IAM role, scoped actions and ARNs | Access keys, `*` policies |
| PR with config change + rollback note | Agent-triggered deploy or API call |

## Stop conditions
- Task requires a production deploy or a Coolify/AWS settings change: return `BLOCKED` with `limit:`. No comment or label.
- A secret is found in the repo or image: do not echo it. Return `BLOCKED` with `limit: secret found at <path>`. No comment or label.

## Review checklist (quality-reviewer)
- [ ] critical: secret or credential in repo, image layer, Compose, or PR text; agent-triggered production deploy; wildcard IAM without justification.
- [ ] major: root user; unpinned or `:latest` base; dev dependencies in runtime image; missing `.dockerignore` entries for `.env*`/`.git`.
- [ ] major: missing `HEALTHCHECK` or health endpoint; non-backward-compatible migration; Rollback section empty.
- [ ] major: preview environment wired to production data or credentials.
- [ ] minor: poor layer order; missing `.env.example` entry for a new variable; missing resource limits.

## References
- Bun Docker guide: https://bun.com/guides/ecosystem/docker (`oven/bun:1`, accessed 2026-11-18)
- Coolify environment variables: https://coolify.io/docs/knowledge-base/environment-variables (Coolify v4, accessed 2026-11-18)
- Coolify GitHub preview deployments: https://coolify.io/docs/applications/ci-cd/github/preview-deploy (Coolify v4, accessed 2026-11-18)
- AWS IAM security best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (accessed 2026-11-18)
- Next.js standalone output: https://nextjs.org/docs/app/api-reference/config/next-config-js/output (not fetched; apply only if the repo uses it)

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
