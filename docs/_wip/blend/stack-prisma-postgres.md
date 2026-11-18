### stack-prisma-postgres

Sources read: ECC:skills/prisma-patterns/SKILL.md@3f14a10, ECC:skills/postgres-patterns/SKILL.md@3f14a10, ECC:skills/database-migrations/SKILL.md@3f14a10 (+ examples/*.sql listed, not adopted), ECC:agents/database-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Check Prisma version first | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Turned into a gate: pinned version only, never `prisma@latest`; Prisma 8 → `ai:needs-human` with default. |
| `migrate dev` can reset DB; deploy in CI | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | `migrate dev` only on disposable DB; production `migrate deploy` only via Gate 3 (agents never). |
| Never edit applied migration (checksum) | ECC `skills/prisma-patterns/SKILL.md`, `skills/database-migrations/SKILL.md` @3f14a10 | take | Integrity; fix forward. |
| Expand/contract multi-step | ECC `skills/database-migrations/SKILL.md` @3f14a10 | modify | Condensed 7-step SQL walkthrough to 4 steps; long SQL dropped. |
| Destructive migration definition + PR Risks flag | Conventions (PR template) | modify | Added explicit list + Risks/Rollback requirement; missing Risks = critical. |
| CREATE INDEX CONCURRENTLY via `--create-only` | ECC `skills/database-migrations/SKILL.md` @3f14a10 | take | Prisma cannot generate it; noted no-transaction constraint. |
| Schema/data migrations separate; forward-only prod | ECC `skills/database-migrations/SKILL.md` @3f14a10 | take | Core principles. |
| Drizzle, Kysely, Django, golang-migrate workflows | ECC `skills/database-migrations/SKILL.md` @3f14a10 | drop | Not in stack target. |
| Self-checking SQL fixtures (examples/*.sql) | ECC `skills/database-migrations/examples/` @3f14a10 | drop | Require psql against a DB; token cost; principle kept. |
| ID strategy, include vs select, DTO mapping | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Repo strategy wins; condensed. |
| Transactions (array vs interactive, tx only, 5 s timeout, no external calls) | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | Common real bugs. |
| Traps: updateMany count, @updatedAt skip, deleteMany no where, soft delete findFirstOrThrow | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | One line each. |
| Error codes P2002/P2025/P2003 | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | take | Maps to Hono 409/404. |
| Singleton client, serverless connection_limit=1 | ECC `skills/prisma-patterns/SKILL.md` @3f14a10 | modify | Singleton kept; serverless/Vercel specifics dropped (Docker/Coolify target). |
| Index cheat sheet, composite order, FK indexes | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | modify | Kept as rules; partial/GIN/BRIN via raw SQL migration. |
| Data types (bigint, text, timestamptz, numeric) | ECC `skills/postgres-patterns/SKILL.md` @3f14a10 | modify | Expressed in Prisma terms; repo convention wins. |
| RLS / `auth.uid()` policies | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | drop | Supabase-specific; not in stack target. |
| ALTER SYSTEM config template, pg_stat diagnostics | ECC `skills/postgres-patterns/SKILL.md`, `agents/database-reviewer.md` @3f14a10 | drop | Ops on shared DB; agents must not touch; out of PR scope. |
| SKIP LOCKED queues, lock ordering, short transactions | ECC `agents/database-reviewer.md` @3f14a10 | modify | Kept lock ordering + short tx; queue pattern dropped as niche. |
| Reviewer checklist | ECC `agents/database-reviewer.md` @3f14a10 | modify | Merged into critical/major/minor checklist. |
| Prisma 8 RC replaces migrate/generate with `prisma db migrate` | https://www.prisma.io/docs (accessed 2026-11-18, Prisma 8 RC) + upgrade guide | write from docs | Used only to add a version gate; not adopted. |
| Prisma + Bun guide | https://www.prisma.io/docs/guides/runtimes/bun (accessed 2026-11-18) | write from docs | Describes Prisma 8 flow; not adopted; noted in References. |
