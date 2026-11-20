---
name: stack-typescript-bun
description: TypeScript rules for repos that run on Bun (runtime, package manager, test runner) and use Biome for lint and format.
when_to_use: Load when `.agent/profile.yml` `packs` lists stack-typescript-bun and you design, implement, or review TypeScript code.
disable-model-invocation: false
---
# Stack: TypeScript on Bun

## Purpose
Give designer, implementer, and quality-reviewer one set of TypeScript, Bun, and Biome rules.
The compiler is a proof tool. Make it do real work; do not fight it.

## Scope
- Use for: `.ts`/`.tsx` source, `tsconfig.json`, `package.json` scripts, `bun.lock`, `biome.json`, `bun test` files.
- Not for: framework rules. Load `stack-hono-api`, `stack-nextjs-ui`, or `stack-prisma-postgres` for those.
- Versions follow the target repo's `package.json` and `bun.lock`. Check `bun --version` and `bunx biome --version` before relying on a flag.

## Toolchain rules
- Bun is the only package manager and runner. Never use npm, pnpm, yarn, npx, or `node`.
- Commit `bun.lock` (text). Do not add `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml`. Treat legacy `bun.lockb` as migrate-on-touch only if the repo already plans it.
- Biome is the only linter and formatter. Never add ESLint, Prettier, or their config files. Config lives in `biome.json` (or `biome.jsonc`).
- Do not weaken `biome.json` rules or add broad `// biome-ignore` comments to pass CI. A targeted ignore needs a reason in the comment.
- Run commands from `commands.*` in `.agent/profile.yml`. Use the defaults below only when the profile leaves a step empty and the repo clearly supports it.

## Commands
```bash
bun install --frozen-lockfile        # CI / verification install
bun add <pkg> | bun add -d <pkg>     # add runtime / dev dependency
bun remove <pkg>
bun run <script>                     # package.json script
bun src/index.ts                     # run a file (TS runs natively)
bunx tsc --noEmit                    # typecheck (Bun does not typecheck)
bun test                             # all tests
bun test path/to/file.test.ts        # one file
bun test -t "<name regex>"           # filter by test name
bun test --coverage                  # coverage (text; --coverage-reporter=lcov for CI)
bunx biome ci .                      # lint + format check, no writes (CI gate)
bunx biome check --write             # apply format + safe lint fixes locally
bunx biome check --changed --since=<base>   # only files changed vs base
bun audit                            # registry advisories from bun.lock (read-only)
```
- `bun audit fix` modifies the lockfile and installs packages. Treat it as a dependency change, not a check.
- `--unsafe` fixes change semantics. Use them only when the task asks and review the diff.

## Compiler baseline
- `strict: true` is mandatory. A repo that fails strict has a migration task, not an exemption.
- Recommended on new code: `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`, `moduleResolution: "bundler"`, `types: ["bun"]` (from `@types/bun`).
- Never relax a `tsconfig.json` flag to make a change compile. Flag any weakening as a major finding.

## Type rules
- Explicit parameter and return types on exported functions and public methods. Let locals infer.
- `interface` for extendable object shapes. `type` for unions, intersections, tuples, mapped types.
- String-literal unions over `enum`, unless interop needs runtime values.
- Model multi-state values as discriminated unions. End switches with `assertNever(x: never)`.
- Use `unknown` for untrusted input, then narrow. No `any` in application code.
- Validate at I/O boundaries (HTTP, env, files, queues) with a schema (Zod or the repo's choice). Derive the type with `z.infer`. Trust the refined type inside.
- Use type predicates or `asserts` functions instead of unchecked `as` casts. Keep any required cast inside the module that validated the value.
- Use `satisfies` to check a literal against a shape without widening it.
- Mark parameters `readonly` when the function does not mutate them. Update with spread, not mutation.
- Options objects for functions with more than two optional knobs.
- Named exports. No barrels that import everything; import concrete paths. Break circular imports by moving shared types to a contract module.

## Errors and async
- `throw new Error(msg, { cause })`. Never throw strings. Never stringify away the cause.
- Narrow `catch (error: unknown)` before use. No empty `catch`.
- Use a `Result` union for expected business failures. Reserve exceptions for the unexpected.
- Await or handle every promise. No floating promises. No `array.forEach(async ...)`; use `for...of` or `Promise.all`.
- `Promise.all` for fail-fast fan-out. `Promise.allSettled` when one failure must not drop others. Bound concurrency for large fan-out.
- Thread `AbortSignal` through long-running and outbound work.
- Wrap `JSON.parse` of external data and validate the result.

## Bun runtime
- Prefer built-ins before adding a dependency: `Bun.file`/`Bun.write`, `Bun.serve`, `Bun.password`, `fetch`, `crypto.randomUUID()`, `Bun.env`.
- Read env through one validated module at startup. Fail fast when a required variable is missing. Never hardcode secrets.
- Bun loads `.env` automatically. Never commit `.env`; keep `.env.example` current.
- Bun is not 100% Node-compatible. Verify native addons and `node:` internals with a test before relying on them.
- No `console.log` in production paths. Use the repo's logger.

## Testing (bun test)
- Import from `bun:test`: `test`, `describe`, `expect`, `mock`, `spyOn`, `beforeEach`, `afterEach`.
- Files: `*.test.ts` or `*.spec.ts`, next to the code or under `test/`, following repo convention.
- Default per-test timeout is 5000 ms. Raise it per test, not globally, and say why.
- Reset mocks in `afterEach` (`mock.restore()`). Do not leak module mocks across files.
- Assert behavior, not implementation details. Do not use Vitest or Jest packages.
- Coverage targets apply only to `coverage_paths` from the profile.

## Prefer / avoid
| Prefer | Avoid |
|---|---|
| `unknown` + narrowing | `any`, `as` casts that skip a check |
| Discriminated union + `assertNever` | Boolean flag soup, god interfaces |
| Schema at the boundary | Ad-hoc `typeof` checks scattered inside domain code |
| `bunx biome check --write` | Hand-formatting, ESLint/Prettier configs |
| `bun install --frozen-lockfile` in CI | `bun install` that silently rewrites `bun.lock` |
| `===`, `const`, `let` | `==`, `var` |
| Built-in APIs | Tiny utility dependencies |

## Review checklist (quality-reviewer)
Severity: critical / major / minor.
- [ ] critical: `eval`/`new Function`, shell exec, or path built from user input without allowlist/resolve check.
- [ ] critical: hardcoded secret or token; `.env` committed.
- [ ] critical: SQL or command built by string concatenation with user input.
- [ ] major: `any`, unjustified non-null `!`, or a cast that bypasses validation.
- [ ] major: floating promise, `forEach(async)`, swallowed error, thrown non-Error.
- [ ] major: missing boundary validation on external input or `process.env`/`Bun.env`.
- [ ] major: `tsconfig.json` or `biome.json` weakened; ESLint/Prettier or npm/yarn/pnpm lockfile added.
- [ ] major: `bun.lock` changed without a matching `package.json` change (or vice versa).
- [ ] minor: missing return type on an export; magic values; `console.log`; barrel import bloat.
- [ ] Evidence: `bunx biome ci .`, `bunx tsc --noEmit`, and `bun test` output present and green.

## References
- Bun docs, https://bun.sh/docs (test runner page https://bun.sh/docs/cli/test), Bun v1.4.4, accessed 2026-11-18.
- Biome CLI reference, https://biomejs.dev/reference/cli/, Biome v2.x, accessed 2026-11-18.
- TypeScript compiler options, https://www.typescriptlang.org/tsconfig (not fetched; baseline from upstream skill, TypeScript 5.x).

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
