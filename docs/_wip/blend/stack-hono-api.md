### stack-hono-api

Sources read: ECC:skills/api-design/SKILL.md@3f14a10, ECC:skills/backend-patterns/SKILL.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Resource naming (plural, kebab-case, no verbs) | ECC `skills/api-design/SKILL.md` @3f14a10 | take | Language-agnostic. |
| Method semantics + status code table | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Condensed to one rule line each. |
| Error envelope `{error:{code,message,details}}` | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Default shape; repo's existing shape wins for consistency. |
| Pagination (cursor default, offset for small admin) | ECC `skills/api-design/SKILL.md` @3f14a10 | take | Plus cap on `limit`. |
| Filtering/sorting/sparse fieldset syntax | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Style detail; repo convention decides; token cost. |
| Versioning strategy + breaking-change list | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Kept additive vs breaking; breaking change must appear in PR Risks. Sunset timeline dropped. |
| Rate-limit tiers/headers | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Numbers are product decisions; kept only "shared store" rule from backend-patterns. |
| Next.js, Django, Go implementation examples | ECC `skills/api-design/SKILL.md` @3f14a10 | drop | Other frameworks/languages; Hono replaces. |
| API design checklist | ECC `skills/api-design/SKILL.md` @3f14a10 | modify | Merged into critical/major/minor review checklist. |
| Repository/service layering, thin handlers | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Kept as structure rule; Supabase sample dropped. |
| Middleware pattern (withAuth HOF) | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Replaced with Hono `createMiddleware` + built-in middleware. |
| Centralized error handler | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Replaced with `HTTPException` + `app.onError`. |
| N+1, transactions, query optimization | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | drop | Owned by stack-prisma-postgres. |
| Redis caching, job queue, retry backoff, structured logger | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | drop | Not core to Hono routing; in-memory queue unsafe in containers; logger rule in stack-typescript-bun. |
| JWT/RBAC examples | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | modify | Kept "auth by default, ownership 403" rule; implementation via `hono/jwt`/`bearer-auth`. |
| Rate limiting must use shared store | ECC `skills/backend-patterns/SKILL.md` @3f14a10 | take | Correct for multi-replica Coolify deploys. |
| Validator, zValidator, c.req.valid, Content-Type + lowercase header gotchas | https://hono.dev/docs/guides/validation Hono v4 | write from docs | Validation section. |
| app.request() tests, testClient + chained routes | https://hono.dev/docs/guides/testing, https://hono.dev/docs/helpers/testing Hono v4 | write from docs | Testing + structure sections. |
| HTTPException, getResponse, onError | https://hono.dev/docs/api/exception Hono v4 | write from docs | Errors section. |
| RPC `hc<AppType>`, Bun entry, built-in middleware names | Hono v4 docs (rpc, getting-started/bun) not re-fetched | write from docs | Marked in References as not re-fetched; verify against installed version. |
