### stack-deploy

Sources read: ECC:skills/docker-patterns/SKILL.md@3f14a10, ECC:skills/deployment-patterns/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Multi-stage Dockerfile (deps/build/runtime) | ECC `skills/deployment-patterns/SKILL.md`, `docker-patterns/SKILL.md` @3f14a10 | modify | Rebased on `oven/bun` with `bun install --frozen-lockfile [--production]`. |
| Node/Go/Python Dockerfiles | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Pinned tags, non-root user, dependency-first layer order, .dockerignore | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | take | Core hardening; `USER bun` from official image. |
| HEALTHCHECK with wget | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Slim Bun image lacks wget; use a tool present in the image. |
| No secrets in image/compose | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | take | Integrity. |
| Compose local dev stack with healthchecked DB | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | modify | Kept as local/test only; dropped Redis/Mailpit samples. |
| Compose security (no-new-privileges, cap_drop, read_only) | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | modify | Condensed to one rule. |
| Hardened CLI installer harness, Codex OAuth relay | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | drop | ECC-specific; unrelated to app deploy. |
| Rolling/blue-green/canary strategies | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Coolify handles rollout; humans own Gate 3. |
| CI/CD pipeline with deploy-to-production job | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Agents never deploy production (Gate 3). |
| Kubernetes probes | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Env config validation at startup (zod) | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Kept as fail-fast rule; schema lib per repo. |
| Rollback checklist, backward-compatible migrations | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Mapped to PR Rollback section. |
| Production readiness checklist | ECC `skills/deployment-patterns/SKILL.md` @3f14a10 | modify | Reduced to review checklist items agents can verify in a PR. |
| Debug commands (`docker compose down -v`, `system prune`) | ECC `skills/docker-patterns/SKILL.md` @3f14a10 | drop | Destructive; not needed for verification. |
| Gate 3 boundary (PR only, no Coolify/AWS API, no prod deploy) | conventions.md (this repo) | write from policy | Integrity > all. |
| Bun Docker image structure, `USER bun` | https://bun.com/guides/ecosystem/docker `oven/bun:1` | write from docs | Official Bun image pattern. |
| Coolify env vars (UI/shared scopes, build vs runtime, locked), previews per PR | https://coolify.io/docs/knowledge-base/environment-variables, /applications/ci-cd/github/preview-deploy v4, accessed 2026-11-18 | write from docs | Env vars in Coolify, never repo; previews isolated from prod. |
| IAM least privilege, roles with temporary credentials, conditions | https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html accessed 2026-11-18 | write from docs | No credentials in repo. |
