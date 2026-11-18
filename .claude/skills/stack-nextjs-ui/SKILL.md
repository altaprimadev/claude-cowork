---
name: stack-nextjs-ui
description: Rules, commands, and review checklist for Next.js App Router UIs built with TailwindCSS v4 and shadcn/ui on Bun. Load when the repo profile `packs` lists stack-nextjs-ui and the task designs, implements, or reviews pages, components, styles, or Server Actions.
---
# Stack: Next.js UI (App Router, Tailwind v4, shadcn/ui)

## Purpose
Give designer, implementer, and quality-reviewer one shared rule set for Next.js App Router frontends.
Versions follow the target repo's `package.json` and lockfile. Read them before applying version-specific rules.

## When to use / not use
- Use: `.agent/profile.yml` `packs` includes `stack-nextjs-ui`, and the change touches `app/`, components, styles, `components.json`, or Server Actions.
- Do not use: API-only services (use stack-hono-api), pure `.ts` logic with no React (use stack-typescript-bun).
- Generic TypeScript rules (types, async, env validation) live in stack-typescript-bun. Load both for `.tsx` work.

## Rules

### Next.js App Router
1. New files are Server Components by default. Add `"use client"` only for state, effects, refs, browser APIs, or event handlers.
2. Put `"use client"` on line 1. Keep client islands small; the directive propagates to everything the file imports.
3. A Client Component never imports a Server Component. Pass server content via `children` or named slots.
4. Mark modules holding DB clients or secrets with `import "server-only"`.
5. Pass only serializable, minimal props from server to client. Never pass full records with tokens or hashes.
6. Fetch per-request data with `await` in Server Components. Do not fetch app data in `useEffect`.
7. Treat every Server Action and Route Handler as a public endpoint: validate input with a schema, authenticate, authorize per record.
8. `NEXT_PUBLIC_*` values ship to the browser. Never put secrets there.
9. Next.js 16+ names the middleware file `proxy.ts`. Pre-16 uses `middleware.ts`. Check the repo's Next.js version before flagging either.
10. Pair each `Suspense` boundary with an error boundary (`error.tsx` or `react-error-boundary`). Place boundaries near the data, not only at the route root.
11. Use `loading.tsx`, `error.tsx`, `not-found.tsx` per route segment where the UX needs them.

### React
1. Hooks at top level only. Never conditional, never after an early return.
2. Derive values during render. Do not mirror props or computed values into state via `useEffect`.
3. Every effect with a subscription, timer, listener, or request returns a cleanup (`AbortController` for fetch).
4. Do not memoize by default. Add `useMemo`/`useCallback`/`React.memo` only for a memoized child, a hook dependency, or a measured cost.
5. Stable `key` from data IDs. Never array index for lists that reorder, insert, or delete.
6. State location: local `useState` > lift to common ancestor > Context (low-frequency only) > external store. Server data stays in RSC or a server-state library. Shareable UI state (filters, tab, page) goes in the URL.
7. Forms: prefer `<form action>` with `useActionState` on React 19. Use a form library only for multi-step or dynamic-field forms.
8. React 19: `ref` is a normal prop. Do not add `forwardRef` in new code.
9. No class components in new code.

### TailwindCSS v4 (CSS-first)
1. Entry CSS uses `@import "tailwindcss";`. Never `@tailwind base/components/utilities` (v3 syntax).
2. PostCSS plugin is `@tailwindcss/postcss` in `postcss.config.mjs`. Do not add `tailwindcss` or `autoprefixer` as PostCSS plugins.
3. Define tokens with `@theme` (or `@theme inline` for variables that reference other variables) in CSS. Do not create `tailwind.config.js`/`.ts`. If the repo already has one loaded via `@config`, keep it and do not extend it without need.
4. Plugins load with `@plugin` in CSS. Custom utilities use `@utility`; custom variants use `@custom-variant`.
5. Use design tokens (`bg-background`, `text-muted-foreground`, `--color-*`). No raw hex in class strings unless the design doc says so.
6. Merge conditional classes with the repo's `cn()` helper (`clsx` + `tailwind-merge`). No string concatenation for conflicting utilities.
7. Animate `transform`, `opacity`, `clip-path` only. Respect `motion-reduce:`.

### shadcn/ui
1. Add components with `bunx shadcn@latest add <name>`. Do not hand-copy from the website.
2. `components.json` on Tailwind v4: `tailwind.config` stays empty; `tailwind.css` points at the global CSS; `rsc: true` for App Router.
3. Generated files under the `ui` alias are owned code. Edit them for product needs; keep `data-slot` attributes.
4. Use `tw-animate-css`. `tailwindcss-animate` is deprecated for v4 projects.
5. Theme colors are CSS variables (OKLCH) in `:root` and `.dark`, mapped through `@theme inline`.
6. Compose primitives; do not fork Radix behavior. Keep keyboard, focus, and ARIA logic from the primitive.

### Design quality and accessibility
1. No unmodified template output: no default card grid, stock gradient hero, or uniform radius/spacing/shadow everywhere. Follow the design doc direction.
2. Clear hierarchy through scale and spacing. Designed hover, focus-visible, and active states.
3. Semantic HTML first: `<button>`, `<a>`, `<nav>`, `<main>`, ordered headings.
4. Every input has a label. Images have `alt` (`alt=""` if decorative). Color is never the only signal.
5. Manage focus on dialog open/close and route changes. Both themes look intentional if both exist.
6. Use `next/image` with explicit size; `next/font` with at most two families.

### Security
1. `dangerouslySetInnerHTML` only with same-call-site sanitization (DOMPurify allowlist). Otherwise critical.
2. Validate URL schemes (`http:`, `https:`, `mailto:`) for user-supplied `href`/`src`.
3. `target="_blank"` needs `rel="noopener noreferrer"`.
4. No session tokens in `localStorage`. Use httpOnly cookies.

## Commands (Bun)
Use the repo's `commands.*` from `.agent/profile.yml` first. Typical equivalents:

```bash
bun install --frozen-lockfile
bun --bun run dev                 # next dev (Turbopack default on 16+)
bun --bun run build               # next build
bunx biome ci .                   # lint + format check
bunx tsc --noEmit                 # typecheck
bunx shadcn@latest init           # only if components.json is missing and the plan says so
bunx shadcn@latest add button dialog
```

New app scaffold (design-approved only): `bun create next-app@latest <name>`, then Tailwind v4 via `bun add tailwindcss @tailwindcss/postcss postcss`.
Never add ESLint or Prettier config. Biome is the linter and formatter.

## Testing
- Add component tests only if the repo already has a component test setup, and only test kinds listed in `test_types`.
- Test behavior: query by role, then label, then text. `data-testid` is the last resort.
- Use `userEvent` (awaited) over `fireEvent`. Use `findBy*` for async content. No `setTimeout` waits.
- Mock the network at the boundary (MSW if present). Never mock React or hooks.
- No DOM snapshot tests for components.
- Full user flows belong to stack-playwright-e2e, and only when `test_types` includes `e2e`.

## Prefer / Avoid

| Prefer | Avoid |
|---|---|
| Server Component + small client island | `"use client"` on pages or layouts |
| `await` data in RSC, server-state library on client | `fetch` in `useEffect` |
| `@theme` tokens in CSS | `tailwind.config.js`, v3 `@tailwind` directives |
| `bunx shadcn@latest add` | Copy-pasted component source, `npx` |
| `cn()` for conditional classes | Template-string class concatenation |
| Derived values in render | Effect-synced derived state |
| `useActionState` + schema-validated Server Action | Unvalidated `FormData` use |

## Review checklist (quality-reviewer)
Severity: critical / major / minor.
- [ ] critical: unsanitized `dangerouslySetInnerHTML`, unvalidated user URL, secret in `NEXT_PUBLIC_*`, Server Action without validation or auth, server-only module imported in a client file.
- [ ] critical: conditional hook call or direct state mutation.
- [ ] major: missing effect cleanup, missing deps, effect for derived state, index keys on dynamic lists.
- [ ] major: `"use client"` wider than needed; sensitive data passed as props.
- [ ] major: Tailwind v3 artifacts added (`tailwind.config.js`, `@tailwind`, `tailwindcss-animate`), ESLint/Prettier added.
- [ ] major: inaccessible interaction (`div onClick`, unlabeled input, missing `alt`, broken focus).
- [ ] minor: default-template look, uniform emphasis, raw hex colors, unneeded memoization, component over ~200 lines.
- [ ] Verification output for lint, typecheck, test, build is present in the PR.

## References
- Tailwind CSS v4 Next.js guide: https://tailwindcss.com/docs/installation/framework-guides/nextjs (v4.3, accessed 2026-11-18)
- shadcn/ui Tailwind v4: https://ui.shadcn.com/docs/tailwind-v4 (accessed 2026-11-18)
- shadcn/ui components.json: https://ui.shadcn.com/docs/components-json (accessed 2026-11-18)
- Bun + Next.js guide: https://bun.com/guides/ecosystem/nextjs (Bun 1.x, accessed 2026-11-18)
- Next.js proxy (middleware) docs: https://nextjs.org/docs/app/getting-started/proxy (Next.js 16, via ECC; not fetched)

Adapted from affaan-m/ECC (MIT). See docs/blend-decisions.md.
