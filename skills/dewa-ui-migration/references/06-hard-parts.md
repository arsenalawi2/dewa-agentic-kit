# The hard parts — state, data, a changing backend, accessibility, non-Vue sources

The five phases assume the easy case: a frozen backend, the same API, a Vue source. Real migrations rarely are. This doc covers the parts that actually bite.

## 1. Global state + data-fetching (the real work of Phase 2/3)

Moving a framework's state + fetching layer is usually harder than the components. Map it deliberately:

| Old (source) | New (React/Astryx) |
|---|---|
| Vuex / Pinia / Redux / NgRx store | A tiny `useSyncExternalStore` module per store (localStorage-backed if persisted), or Zustand for larger trees. The leaderboard used bare `useSyncExternalStore` stores (`lib/admin.js`, `lib/session.js`, `lib/hidden.js`). |
| Vue composables / Angular services | Plain hooks in `src/hooks/` or `src/lib/`. |
| axios + interceptors | ONE `fetch` wrapper (`lib/api.js`) that attaches auth headers + handles 401 → refetch on auth change. |
| Vue Query / SWR / RxJS polling | A shared "resource" (`createResource(url, {pollMs, fixture})`) with one poll per URL across all consumers, a dev-fixture fallback gated on `import.meta.env.DEV || VITE_USE_FIXTURES`, and a subscribe-on-auth-change refetch. |

**The 401-cache trap (cost real debugging):** if a resource fetches once while the user is unauthenticated (401), caches it, and never refetches after login, the board stays empty. Every data resource must **refetch on auth change** (notify from your session store; resources subscribe). The audit's "data layer" cross-cut exists precisely because a dropped data capability = a dead feature — treat it as a first-class audit unit, not an afterthought.

## 2. When the backend also changes

The skill's default assumes the new frontend talks to the identical API. If the backend is changing at the same time (renamed/removed fields, new auth, pagination, REST→GraphQL):

1. **Capture the OLD API contract** as an explicit audit artifact — every endpoint, response shape, and auth mechanism the old UI relied on. This is part of the data-layer audit unit.
2. **Put an adapter layer in the new app** (`lib/api-adapters.js`): the UI codes against a stable internal shape; adapters map whatever the (moving) backend returns into it. A field rename becomes a one-line adapter change, not a hunt across pages.
3. **Contract tests**: `old-response-fixture → adapter → expected-UI-props`. Run them in CI so a backend field change is caught before deploy, not in production.
4. **Coordinate cutover + rollback across both tiers.** Version the API; deploy the backend behind a flag first and verify; then the frontend. **Rollback must cover both** — rolling back only the dist against a new API re-breaks the old UI. Keep both rollback commands together.

## 3. Prove features WORK, not just render (Phase 4, deeper)

The smoke test proves the app doesn't crash. For a feature-preservation migration that's necessary, not sufficient. Add a parity tier:

- **Data-parity checks:** for each KPI / derived metric, assert `new value == old value` on the SAME input fixture. A tiny harness that runs the old app's compute fn and the new one over one fixture and diffs catches "the number moved" regressions the eye misses.
- **Interaction assertions:** for the highest-value restored controls, a Playwright assertion that the control *does its job* — e.g. select a month → the top row changes; type in search → the list filters; click Export → a file downloads. A handful of these per app, on the features the audit flagged as previously-dropped.
- **Visual regression (optional):** screenshot each page old-vs-new and diff, if you have a baseline.

## 4. Accessibility (non-negotiable for a DEWA/government app)

DEWA is a public utility — WCAG conformance is an obligation, not a nicety. Bake a11y into two phases:

- **Audit (Phase 1):** add "keyboard nav / focus management / ARIA labels / color contrast / reduced-motion" to the per-page finder checklist. A migration commonly drops focus traps, `aria-*`, and keyboard handlers that the old app had.
- **Verify (Phase 4):** run **axe-core** via Playwright over every route alongside the smoke test (`@axe-core/playwright`), fail on serious/critical violations. Specifically check: the DEWA green `#007560` meets **4.5:1** contrast on its surfaces (it does on white; verify on tinted/`variant="green"` backgrounds and in dark mode); every interactive control is keyboard-reachable with a visible focus ring; the F1-replay-style animations honor `prefers-reduced-motion`; icon-only buttons have labels.

## 5. Source-framework playbook (not everything is Vue)

The phases are framework-agnostic, but WHERE features hide differs by source:

| Source | Where the behavior lives / what to grep | Phase notes |
|---|---|---|
| **Vue 2/3 (+EZ)** | `.vue` SFCs, `composables/`, `<script setup>`, `v-if`/`v-model`, Pinia/Vuex | The worked example. Composables → hooks. |
| **Angular** | components + `*.service.ts`, RxJS streams, guards/resolvers, pipes, `NgModules`, two-way binding | Guards/resolvers → route loaders + the Chrome guard; RxJS polling → interval hook; pipes → format utils. Phase 2 grows. |
| **Static HTML / jQuery** | inline `<script>`, event handlers, templating; no component boundary | The audit unit = each PAGE/section; you're defining components from scratch. Phase 2 (shell) is most of the work. |
| **Legacy React + old DS** | already React — grep the old design-system component usage | Skip most of Phase 2 framework setup; the migration is component-swap + DEWA theme + the same feature audit. |
