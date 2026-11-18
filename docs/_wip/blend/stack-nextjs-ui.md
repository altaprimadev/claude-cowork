### stack-nextjs-ui

Sources read: ECC:rules/react/{coding-style,hooks,patterns,security,testing}.md@3f14a10, ECC:rules/web/{coding-style,design-quality,hooks,patterns,performance,security,testing}.md@3f14a10, ECC:skills/nextjs-turbopack/SKILL.md@3f14a10, ECC:skills/react-patterns/SKILL.md@3f14a10, ECC:skills/frontend-patterns/SKILL.md@3f14a10, ECC:skills/react-testing/SKILL.md@3f14a10, ECC:agents/react-reviewer.md@3f14a10

| Atom | Source (repo, path, commit) | Decision | Reason |
|---|---|---|---|
| Server/Client boundary rules (default RSC, `"use client"` line 1, server-only) | ECC `rules/react/patterns.md`, `coding-style.md` @3f14a10 | take | Core App Router correctness. |
| Hooks discipline (top-level, cleanup, no derived state in effect, no default memo) | ECC `rules/react/hooks.md`, `skills/react-patterns/SKILL.md` @3f14a10 | modify | Condensed to rules; dropped ESLint `react-hooks` config (Biome is the linter). |
| State location decision tree, URL as state | ECC `rules/react/patterns.md`, `rules/web/patterns.md` @3f14a10 | take | Short, stack-neutral. |
| React 19 forms (`useActionState`), ref as prop | ECC `skills/react-patterns/SKILL.md`, `rules/react/patterns.md` @3f14a10 | take | Matches shadcn/React 19 baseline. |
| React security (dangerouslySetInnerHTML, URL schemes, NEXT_PUBLIC, Server Action validation, localStorage tokens) | ECC `rules/react/security.md` @3f14a10 | modify | Kept rules; moved into checklist as critical; dropped Vite/CRA/Remix rows and CSP block (repo-specific). |
| `proxy.ts` vs `middleware.ts` naming | ECC `skills/nextjs-turbopack/SKILL.md` @3f14a10 | take | Prevents false review findings. |
| Turbopack/webpack tradeoffs, bundle analyzer | ECC `skills/nextjs-turbopack/SKILL.md` @3f14a10 | drop | Defaults suffice; version-specific tutorial content. |
| Anti-template design policy + component checklist | ECC `rules/web/design-quality.md` @3f14a10 | modify | Condensed; direction comes from the approved design doc, not agent taste. |
| Style direction list (neo-brutalism, glassmorphism...) | ECC `rules/web/design-quality.md` @3f14a10 | drop | Designer decides per design doc; token cost. |
| Web hooks (Prettier/ESLint/tsc PostToolUse hooks) | ECC `rules/web/hooks.md` @3f14a10 | drop | Stack uses Biome; skills must not add hooks; verification via profile commands. |
| CWV targets and bundle budgets | ECC `rules/web/performance.md` @3f14a10 | drop | Global thresholds; not in profile contract. Kept image/font/animation rules only. |
| Compositor-only animation, semantic HTML, tokens via CSS vars | ECC `rules/web/coding-style.md` @3f14a10 | modify | Mapped to Tailwind v4 `@theme` tokens. |
| Frontend code samples (compound components, virtualization, Framer Motion) | ECC `skills/frontend-patterns/SKILL.md` @3f14a10 | drop | Tutorial content; no rules beyond those already kept. |
| RTL query priority, userEvent, findBy, MSW, no snapshots | ECC `skills/react-testing/SKILL.md`, `rules/react/testing.md` @3f14a10 | modify | Applied only if repo already has component tests and per `test_types`; Vitest/Jest commands dropped (Bun). |
| Coverage targets per layer | ECC `skills/react-testing/SKILL.md` @3f14a10 | drop | Coverage comes from profile `coverage_target`/`coverage_paths`. |
| Reviewer severity lanes and approval criteria | ECC `agents/react-reviewer.md` @3f14a10 | modify | Mapped CRITICAL/HIGH/MEDIUM to critical/major/minor; approval stays with humans (Gate 2). |
| Reviewer diagnostic commands (npx eslint, npm audit, prettier) | ECC `agents/react-reviewer.md` @3f14a10 | drop | Replaced with Bun/Biome commands. |
| Tailwind v4 CSS-first setup (`@import "tailwindcss"`, `@tailwindcss/postcss`, no config file) | https://tailwindcss.com/docs/installation/framework-guides/nextjs v4.3 | write from docs | Required stack target; never adopt v3 atoms. |
| shadcn/ui v4 (`tw-animate-css`, OKLCH, `data-slot`, no forwardRef, empty `tailwind.config`) | https://ui.shadcn.com/docs/tailwind-v4, /docs/components-json accessed 2026-11-18 | write from docs | Current shadcn CLI behavior. |
| Next.js with Bun commands | https://bun.com/guides/ecosystem/nextjs Bun 1.x | write from docs | Replace npm/npx. |
