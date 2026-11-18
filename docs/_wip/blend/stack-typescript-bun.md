### stack-typescript-bun

Sources read: ECC:rules/typescript/{coding-style,hooks,patterns,security,testing}.md@3f14a10, ECC:skills/typescript-patterns/SKILL.md@3f14a10, ECC:skills/bun-runtime/SKILL.md@3f14a10, ECC:agents/typescript-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Strict mode baseline + extra flags (Principle) | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept strict mandatory; extra flags "recommended on new code" so existing repos are not forced into mass migration; added `types: ["bun"]`. |
| `any` is a bug, `unknown` + narrowing (Principle) | ECC `rules/typescript/coding-style.md` + `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Core type-safety rule; condensed to one line. |
| Explicit types on public APIs, interface vs type, literal unions over enum | ECC `rules/typescript/coding-style.md` @3f14a10 | take | Stack-neutral TS rules. |
| Discriminated unions, brands, generics, satisfies, readonly | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept as one-line rules; dropped long code samples (no tutorials). Brands dropped as niche. |
| Validate at boundary with Zod (Procedure) | ECC `rules/typescript/coding-style.md` @3f14a10 | modify | Zod "or repo's choice"; env validated once at startup. |
| Error handling: cause, Result type, no silent catch | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Directly reviewable. |
| Async: allSettled, bounded concurrency, AbortSignal, timeouts | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | modify | Kept rules, dropped `mapWithConcurrency`/`withTimeout` implementations. |
| Module boundaries, no barrels, no cycles | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | take | Condensed. |
| Type-level testing with Vitest `expectTypeOf` | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | drop | Vitest not in stack target; bun test only. |
| Tooling commands (npx tsc, vitest, eslint, prettier) | ECC `skills/typescript-patterns/SKILL.md`, `agents/typescript-reviewer.md` @3f14a10 | modify | Converted to `bunx tsc --noEmit`, `bun test`, `bunx biome ci .`, `bunx biome check --write`. |
| typescript-eslint recommended-type-checked baseline | ECC `skills/typescript-patterns/SKILL.md` @3f14a10 | drop | Biome replaces ESLint; never add ESLint config. |
| PostToolUse/Stop hooks (Prettier, tsc, console.log) | ECC `rules/typescript/hooks.md` @3f14a10 | drop | No hooks in skills per conventions; checks run via profile commands in evidence-report. console.log rule kept as review item. |
| Repository pattern, ApiResponse, React custom hooks | ECC `rules/typescript/patterns.md` @3f14a10 | drop | API shape belongs to stack-hono-api; React to stack-nextjs-ui. |
| Secret management via env | ECC `rules/typescript/security.md` @3f14a10 | modify | Uses `Bun.env`/validated env module; added `.env` never committed (Bun auto-loads .env). |
| Playwright E2E / e2e-runner agent reference | ECC `rules/typescript/testing.md` @3f14a10 | drop | Owned by stack-playwright-e2e; agent not adopted. |
| Bun as runtime/pm/test, lockfile, migration-from-Node notes, built-in APIs | ECC `skills/bun-runtime/SKILL.md` @3f14a10 | modify | Bun is mandatory, so "Bun vs Node" choice dropped; kept bun.lock, built-ins, compat caveat, `bun audit` vs `audit fix`. |
| Vercel bunVersion config | ECC `skills/bun-runtime/SKILL.md` @3f14a10 | drop | Deploy target is Docker/Coolify/AWS. |
| Reviewer priorities (security/type/async/error/idioms) | ECC `agents/typescript-reviewer.md` @3f14a10 | modify | Mapped CRITICAL/HIGH/MEDIUM to critical/major/minor checklist; React items dropped (stack-nextjs-ui). |
| Reviewer merge-readiness check + approve/block criteria | ECC `agents/typescript-reviewer.md` @3f14a10 | drop | Owned by review-two-stage; agents never approve. |
| Prompt defense baseline | ECC `agents/typescript-reviewer.md` @3f14a10 | drop | Not a stack concern; covered at agent level. |
| bun test flags, file patterns, bun:test imports, 5000 ms timeout | https://bun.sh/docs/cli/test Bun v1.4.4 | write from docs | Commands and testing section. |
| Biome check/ci/--write/--unsafe/--changed --since | https://biomejs.dev/reference/cli/ Biome v2.x | write from docs | Commands and lint rules. |
