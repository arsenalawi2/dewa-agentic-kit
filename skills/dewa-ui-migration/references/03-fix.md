# Phase 3 — Fix (fan out one agent per page)

**Goal:** restore every confirmed gap from Phase 1 and render each page in Astryx/DEWA, using many parallel agents that never touch the same file.

## The ordering that avoids conflicts

1. **Build shared infrastructure FIRST, on the main thread, and commit it.** Anything multiple pages need: shared data hooks/engines (e.g. a per-month aggregation engine), reusable chart components (scatter, sparkline, heat-grid), a CSV util, global stores (e.g. a "hide these players" toggle via `useSyncExternalStore` + localStorage), router fixes (redirects, catch-all 404), app-shell/chrome (identity, dynamic labels). Page agents then IMPORT these instead of reinventing them.
2. **Materialize a spec file per page** from the audit's confirmed gaps (`specs/<Page>.md`): each gap's title, status, and a concrete fix hint. Agents read their spec.
3. **Fan out — one agent per SERVED page file.** All page files are disjoint, so they run concurrently with no merge step (edit the real working tree directly; no worktrees needed). Batch ~8 at a time.

## The per-agent brief (template)

Give each agent:
- Its ONE page file to edit + the page's spec file + the OLD reference file(s).
- The shared infra available (with import paths + signatures) so it reuses, not reinvents.
- Hard rules:
  - **Edit ONLY your assigned page file.** If you must add a helper component, name it `<Page>Xxx.jsx` (page-prefixed, unique) to avoid collisions. Prefer inline.
  - **Do NOT run `npm run build` / `npm install`** (concurrent builds race on `dist/`; the orchestrator verifies). **No new npm deps** — charts/graphs/animations are dependency-free SVG + React. No `Math.random`/`Date.now` in render (breaks determinism/SSR).
  - Additive: preserve what the redesign already does well; only add back what was lost. Keep admin-gating as-is.
  - Match the file's existing Astryx idioms.
  - Return a short summary: gaps fixed, any not fixed (why), any new file.

## What the orchestrator does between/after batches

- Watch the editor diagnostics stream — mid-edit "unused import" noise is normal; a real `Cannot redeclare` / undefined-reference means an agent left the file broken.
- If an agent needs a shared-file change (e.g. a hook must expose `error`), it should FLAG it, not edit the shared file mid-fan-out — you apply that 1-liner yourself after the wave (avoids two agents clobbering `hooks/useData.js`).
- After each batch: `npm run build`. Fix or re-dispatch the file that broke.
- Commit per wave.

## Correcting an agent mid-flight

If a requirement changes while an agent runs (it happens), `SendMessage` the agent's id with the correction — it's delivered at the agent's next tool round. (On the real run this was used to add the F1 theme music and to move the "Show Player 0" toggle from admin-only to all-users.)

## Heavy items

Big rebuilds (an animated replay, a force-directed network graph, a month-over-month compare) are still one agent each — just give a richer brief and demand dependency-free SVG + `requestAnimationFrame`. Deliver a solid functional version; note any fidelity gap rather than blocking.

## Scale reference (leaderboard, 35 pages)

~15 page agents + a few for small single-gap pages, plus the orchestrator building shared infra (a monthly engine, a scatter chart, router/chrome fixes) and doing the small self-contained fixes directly. Everything disjoint → all concurrent. Total fix wave ≈ 20 agents.
