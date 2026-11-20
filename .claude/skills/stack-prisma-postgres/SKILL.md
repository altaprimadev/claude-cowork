---
name: stack-prisma-postgres
description: Rules for Prisma ORM on PostgreSQL with Bun - schema design, safe migrations (expand/contract), indexes, transactions, N+1 prevention. Load when `.agent/profile.yml` `packs` lists stack-prisma-postgres and you design, implement, or review schema, migrations, or queries.
---
# Stack: Prisma + PostgreSQL on Bun

## Purpose
Give designer, implementer, and quality-reviewer one set of data rules.
Load together with `stack-typescript-bun`.

## Scope
- Use for: `schema.prisma`, `prisma/migrations/**`, `prisma.config.ts`, queries, transactions, seed scripts.
- Not for: production deploys. Production migrations run only through the human-gated deploy (Gate 3, `stack-deploy`). Agents never run them.

## Version check (first step)
- Read the pinned `prisma` and `@prisma/client` versions in `package.json`. Use only that version. Never run `bunx prisma@latest`.
- This skill targets Prisma ORM 6/7 with `schema.prisma` and `prisma migrate`.
- Prisma 7: `prisma-client` generator with an explicit `output`, a driver adapter (`@prisma/adapter-pg`), and the datasource URL in `prisma.config.ts`. `migrate dev` does not run `generate`; run it yourself.
- Prisma ORM 8 (release candidate as of 2026-11) replaces `schema.prisma`, `generate`, and `migrate dev/deploy` with a contract and `prisma db migrate`. If the repo uses Prisma 8 or the commands below fail as unknown, stop. Keep the current major: never upgrade or downgrade Prisma. Return `BLOCKED` with `limit: Prisma 8 is not covered by stack-prisma-postgres` and the failing command output. Do not comment or label: the orchestrator adds `ai:needs-human` (`CLAUDE.md` -> "Hard limits and errors").

## Commands (local or ephemeral test DB only)
```bash
bunx prisma validate                              # schema syntax
bunx prisma format                                # format schema.prisma
bunx prisma generate                              # regenerate client after schema change
bunx prisma migrate dev --name <snake_name>       # create + apply migration (local DB only)
bunx prisma migrate dev --create-only --name <n>  # create SQL to edit before applying
bunx prisma migrate status                        # pending / drift report
bunx prisma migrate diff --from-migrations prisma/migrations \
  --to-schema-datamodel prisma/schema.prisma --script   # preview SQL
bunx prisma migrate deploy                        # apply committed migrations (CI/test DB; prod only via Gate 3)
```
- `migrate dev` may detect drift and reset the database. Run it only against a disposable local or CI database. Never against shared, staging, or production.
- Never run `migrate reset`, `db push`, or `--accept-data-loss` outside a disposable database.
- If no disposable database is available in the session, stop instead of pointing at a shared one. Return `BLOCKED` with `limit: no disposable database`. Do not comment or label: the orchestrator adds `ai:needs-human` (`CLAUDE.md` -> "Hard limits and errors").

## Migration rules
- Every schema change is a committed migration. No manual SQL on any shared database.
- Migrations are immutable once merged. Editing one causes a checksum mismatch. Fix forward with a new migration.
- Production is forward-only. Rollback = a new forward migration or app rollback; document it in PR Rollback.
- Keep schema (DDL) and data backfill in separate migrations.
- Review the generated `migration.sql` before committing. Prisma may emit DROP + ADD for a rename.

### Expand / contract
1. Expand: add new column/table, nullable or with a non-volatile default. Deploy.
2. App writes both old and new. Backfill in bounded batches (separate migration or script). Verify zero mismatches.
3. App reads new, still writes both, through the rollback window.
4. Contract: remove code references, deploy, then drop the old column in a later migration.
- Add `NOT NULL` only after backfill, in its own migration.
- Large-table indexes: `--create-only`, then edit SQL to `CREATE INDEX CONCURRENTLY`. `CONCURRENTLY` cannot run inside a transaction; keep it alone in its migration file.

### Destructive migrations (flag in PR Risks)
Destructive = any `DROP TABLE`, `DROP COLUMN`, column type narrowing, `NOT NULL` on populated data, renames emitted as drop+add, `TRUNCATE`/`DELETE` backfills, or enum value removal.
- List each one under PR **Risks** with: affected table, row-count estimate if known, lock impact, data-loss impact.
- State the rollback path under PR **Rollback**.
- A destructive migration without a Risks entry is a critical review finding.

## Schema rules
- IDs: keep the repo's strategy. New tables: `cuid()`/UUIDv7-style or `BigInt @default(autoincrement())` for internal tables. Avoid random UUIDv4 on hot write tables.
- Timestamps: `DateTime @db.Timestamptz` where the repo uses it; `createdAt @default(now())`, `updatedAt @updatedAt`.
- Money: `Decimal @db.Decimal(p, s)`, never `Float`.
- Map to `snake_case` with `@map`/`@@map` if the repo does so. Follow existing naming.
- Foreign keys: explicit `onDelete`. Add `@@index` on every FK column. Postgres does not index FKs automatically.
- `@unique` already creates an index. Do not duplicate with `@@index`.
- Composite index order: equality columns first, then range/sort columns.
- Partial, covering, GIN, or BRIN indexes need raw SQL in a `--create-only` migration.

## Query rules
- No N+1: never query inside a loop over results. Use `include`/`select` on the relation or one `findMany({ where: { id: { in: ids } } })` plus a `Map`.
- Use `select` on hot paths and wide tables. Map entities to response DTOs; never return raw rows.
- Paginate with cursor: `take: limit + 1`, `cursor: { id }`, `skip: 1`, `orderBy` with a unique tiebreaker (`id`).
- `updateMany`/`deleteMany` return `{ count }`, not rows. They skip `@updatedAt`; set `updatedAt: new Date()` yourself.
- `deleteMany` always has a `where`.
- Soft delete: filter `deletedAt: null` explicitly; use `findFirstOrThrow`, not `findUniqueOrThrow`.
- Raw SQL only via tagged `$queryRaw`/`$executeRaw`. Never `$queryRawUnsafe` with user input.
- Translate `Prisma.PrismaClientKnownRequestError` at the service boundary: `P2002` → conflict, `P2025` → not found, `P2003` → bad reference.

## Transactions
- Array form `$transaction([...])` for independent writes. Interactive form `$transaction(async (tx) => ...)` when a step depends on an earlier result.
- Inside interactive transactions use only `tx`, never the outer client.
- No external calls (HTTP, email, queues) inside a transaction. The default interactive timeout is 5 s.
- Keep transactions short. Lock rows in a consistent order (`ORDER BY id FOR UPDATE`) to avoid deadlocks.

## Client
- One `PrismaClient` per process, in one module. Reuse it across requests.
- Read `DATABASE_URL` from validated env. Connection params (`connection_limit`, `pool_timeout`) live in the URL or adapter config.

## Prefer / avoid
| Prefer | Avoid |
|---|---|
| Expand → backfill → contract | Rename/NOT NULL in one step |
| `--create-only` + reviewed SQL | Blindly committing generated SQL |
| `include`/`in` batch | Queries in loops |
| Cursor pagination | Large `OFFSET` |
| Indexed FKs and filter columns | Seq scans on large tables |
| Short `tx`-only transactions | External calls inside `$transaction` |

## Review checklist (quality-reviewer)
Severity: critical / major / minor.
- [ ] critical: destructive migration not listed in PR Risks with rollback.
- [ ] critical: edited an already-merged migration; `migrate dev`/`reset`/`db push` aimed at a shared DB.
- [ ] critical: `$queryRawUnsafe` or string-built SQL with user input; `deleteMany()` without `where`.
- [ ] major: `NOT NULL` added to populated column without backfill; non-concurrent index on a large table.
- [ ] major: N+1 query; unbounded `findMany`; external call inside a transaction.
- [ ] major: FK or frequently filtered column without index; schema changed without `prisma generate` and migration committed together.
- [ ] major: raw entity returned to API; Prisma error message leaked.
- [ ] minor: naming drift from repo convention; missing `updatedAt` in `updateMany`.
- [ ] Evidence: `bunx prisma validate` and `bunx prisma migrate status` output (or migration applied on a test DB) present.

## References
- Prisma docs, https://www.prisma.io/docs, accessed 2026-11-18. Site now defaults to Prisma ORM 8 (RC); Prisma 6/7 commands (`migrate dev/deploy`, `generate`) written from upstream skill and Prisma 7 knowledge, not re-fetched.
- Prisma 7 → 8 upgrade guide, https://www.prisma.io/docs/guides/upgrade-prisma-orm/postgresql, accessed 2026-11-18 (used only to scope the version gate).
- Prisma Bun guide, https://www.prisma.io/docs/guides/runtimes/bun, accessed 2026-11-18 (Bun >= 1.3; Prisma 8 flow; not adopted).
- PostgreSQL ALTER TABLE / CREATE INDEX, https://www.postgresql.org/docs/current/sql-altertable.html (via upstream, not re-fetched).

Adapted from affaan-m/ECC (MIT), including patterns ECC credits to Supabase Agent Skills (MIT). See docs/blend-decisions.md.
