---
name: stack-hono-api
description: Rules for HTTP APIs built with Hono on Bun - routing, validation, middleware, error handling, RPC types, and tests with app.request() and bun test.
when_to_use: Load when `.agent/profile.yml` `packs` lists stack-hono-api and you design, implement, or review API endpoints.
disable-model-invocation: false
---
# Stack: Hono API on Bun

## Purpose
Give designer, implementer, and quality-reviewer one contract for Hono endpoints.
Load together with `stack-typescript-bun`. Load `stack-prisma-postgres` for data access.

## Scope
- Use for: routes, validators, middleware, error handlers, RPC client types, API tests.
- Not for: Next.js route handlers (`stack-nextjs-ui`), deployment (`stack-deploy`).
- Hono version follows the repo's `package.json` (rules target Hono v4).

## Structure
- One `Hono` instance per resource module. Mount with `app.route('/api/v1/users', users)`.
- Chain route definitions on the instance (`new Hono().get(...).post(...)`). Chaining keeps RPC and `testClient` types.
- Keep handlers thin: validate, call a service, map the result to a response DTO.
- Services own business logic. Repositories own data access. Handlers never call Prisma directly unless the repo already does so.
- Export the app without listening in tests. Entry point for Bun: `export default app` or `export default { port, fetch: app.fetch }`.
- Type bindings and variables: `new Hono<{ Variables: { user: User } }>()`. Set with `c.set`, read with `c.get`.

## Resource and HTTP conventions
- URLs: plural nouns, lowercase, kebab-case, no verbs (`/api/v1/team-members`). Action endpoints only when CRUD does not fit (`POST /orders/:id/cancel`).
- Methods: GET reads, POST creates, PUT replaces, PATCH updates partially, DELETE removes.
- Status codes: 200 read/update, 201 create (+ `Location`), 204 no body, 400 malformed, 401 unauthenticated, 403 forbidden, 404 missing, 409 conflict, 422 semantic validation, 429 rate limited, 500 unexpected.
- Never return 200 with an error body.
- Error body shape: `{ "error": { "code": "snake_case", "message": "...", "details"?: [{ "field", "message", "code" }] } }`. Follow the repo's existing shape if it differs.
- Lists are paginated. Prefer cursor pagination (`limit` + `cursor`, fetch `limit + 1`). Offset only for small admin lists. Cap `limit`.
- Additive changes (new field, new optional param, new endpoint) need no new version. Removing or renaming fields is breaking: needs `/v2` or a deprecation plan, and a PR Risks entry.

## Validation
- Validate every input target: `json`, `query`, `param`, `header`, `form`, `cookie`.
- Prefer `zValidator(target, schema)` from `@hono/zod-validator` when the repo uses Zod. Otherwise use `validator(target, fn)` from `hono/validator`.
- Read validated data only with `c.req.valid(target)`. Never re-read `c.req.json()` after validation.
- `json` and `form` validation need a matching `Content-Type` header. Without it the body is not parsed. Tests must send the header.
- Header validation keys are lowercase (`idempotency-key`).
- Return 400/422 with field-level `details` on failure. Use a custom hook on `zValidator` to keep the error shape consistent.

## Middleware
- Order matters: request id/logger, secure headers, CORS, body limit, auth, then routes.
- Use built-ins before writing your own: `hono/logger`, `hono/cors`, `hono/secure-headers`, `hono/body-limit`, `hono/request-id`, `hono/jwt` or `hono/bearer-auth`.
- Write custom middleware with `createMiddleware` from `hono/factory` so variable types flow.
- CORS: explicit origin allowlist in production. No `origin: '*'` with credentials.
- Auth on every route by default. Mark public routes explicitly. Check resource ownership (403) after authentication (401).
- Rate limiting needs a shared store or the platform limiter. Never an in-memory counter in production.

## Errors
- Throw `new HTTPException(status, { message, cause })` from `hono/http-exception` for expected HTTP failures.
- Register one `app.onError((err, c) => ...)`. Map `HTTPException` via `err.getResponse()` or the repo's error shape. Map domain errors (not found, conflict) to 404/409. Return a generic 500 for the rest.
- `getResponse()` ignores headers set on the context. Copy them when needed.
- Log unexpected errors with request id. Never return stack traces, SQL, or Prisma messages to clients.
- Register `app.notFound` to return the standard error shape.

## RPC types
- Export the route type: `export type AppType = typeof routes`.
- Clients use `hc<AppType>(baseUrl)` from `hono/client`. Shared types travel through the type, not duplicated DTOs.
- Changing a route's input or output changes `AppType`. Run the typecheck of every consumer listed in `depends_on`.

## Testing (bun test)
- Integration-style tests call `app.request(path, init?, env?)` and assert `res.status` and the parsed body.
- JSON requests: `app.request('/x', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } })`.
- Typed tests: `testClient(app)` from `hono/testing`, e.g. `client.users.$get({ query })`.
- Cover per endpoint: happy path, validation failure, unauthenticated, forbidden, not found, conflict where relevant.
- Mock services or use a test database per `test_types` in the profile. Do not hit external networks.

```ts
import { describe, expect, test } from 'bun:test'
import app from '../src/app'

describe('POST /api/v1/users', () => {
  test('returns 422 on invalid email', async () => {
    const res = await app.request('/api/v1/users', {
      method: 'POST',
      body: JSON.stringify({ email: 'nope' }),
      headers: { 'Content-Type': 'application/json' },
    })
    expect(res.status).toBe(422)
  })
})
```

## Prefer / avoid
| Prefer | Avoid |
|---|---|
| Chained routes, `app.route()` | Unchained `app.get` (loses RPC types) |
| `zValidator` + `c.req.valid` | Manual `await c.req.json()` + casts |
| `HTTPException` + one `onError` | try/catch returning ad-hoc JSON in each handler |
| Response DTO mapping | Returning raw DB entities |
| `app.request()` tests | Starting a real server in unit tests |
| Built-in middleware | Hand-rolled CORS, JWT parsing |

## Review checklist (quality-reviewer)
Severity: critical / major / minor.
- [ ] critical: route lacks auth or ownership check where data is user-scoped.
- [ ] critical: response leaks secrets, password hashes, stack traces, or raw DB errors.
- [ ] major: input target used without validation; validated data not read via `c.req.valid`.
- [ ] major: wrong status code class (200 for errors, 500 for validation).
- [ ] major: breaking contract change without versioning and PR Risks entry.
- [ ] major: unbounded list endpoint; wildcard CORS with credentials; in-memory rate limit.
- [ ] major: new endpoint without tests for success and main failure paths.
- [ ] minor: naming (verbs, singular, snake_case URLs); missing `Location` on 201; inconsistent error codes.

## References
- Hono validation guide, https://hono.dev/docs/guides/validation, Hono v4, accessed 2026-11-18.
- Hono testing guide, https://hono.dev/docs/guides/testing, and testing helper, https://hono.dev/docs/helpers/testing, Hono v4, accessed 2026-11-18.
- Hono HTTPException, https://hono.dev/docs/api/exception, Hono v4, accessed 2026-11-18.
- Middleware, RPC (`hc`), and Bun entry point: written from Hono v4 docs knowledge (https://hono.dev/docs/guides/rpc, https://hono.dev/docs/getting-started/bun), not re-fetched. Verify names against the installed version.

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
