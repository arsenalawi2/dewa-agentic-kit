# Phase 4 — Verify (green build ≠ working app)

**Goal:** prove the migrated app builds, runs without runtime crashes on every route, ships no PII, and looks right — BEFORE deploying.

## 1. Build

`npm run build`. A green build means all imports resolve + no syntax errors. It does **not** mean the app runs — React crashes at runtime (bad hook order, `undefined` passed to a styled component, invalid Astryx prop values). So build is a gate, not proof.

## 2. Headless route smoke test — the real gate

Run `assets/smoke.mjs` (Playwright). It:
- starts/uses the app in fixtures mode (`VITE_USE_FIXTURES=1 npm run dev`), so pages render with sample data and no backend;
- **admin-unlocks** (via the front-door admin flow) so admin-only routes actually render instead of redirecting;
- visits EVERY route, collecting `console` errors + `pageerror` (uncaught exceptions) + blank-page detection;
- screenshots the hero pages.

Read the output: **`pageerror` on any route = a real crash to fix.** Expected-and-fine: `401` on admin API endpoints (no backend in dev) — those are network, not crashes. A `styleq: … typeof undefined` error = an invalid Astryx prop value (commonly `<Avatar size="md">` → must be `medium`); fix and re-run.

Requirements: Playwright installed in the app (`node_modules/.bin/playwright`); run the script from inside the app dir so `import 'playwright'` resolves. Admin-unlock via the Welcome page's "Admin access" flow (fixtures demo password is usually `admin`).

## 2b. Prove features WORK + accessibility

The smoke test proves the app doesn't **crash** — not that a restored feature **works**. For a feature-preservation migration that's necessary, not sufficient. Add: **data-parity checks** (each KPI/metric: new value == old value on the same fixture), **interaction assertions** (select a month → top row changes; type → list filters; click Export → file downloads) for the controls the audit flagged as previously-dropped, and — mandatory for a DEWA/government app — an **axe-core accessibility pass** over every route (keyboard nav, focus rings, ARIA, DEWA-green contrast ≥ 4.5:1, `prefers-reduced-motion`). Full recipes in `references/06-hard-parts.md` §3–4.

## 3. PII scan of the BUILT bundle

Before any deploy, grep `dist/` for leaks:
```bash
grep -rl '@<org-email-domain>' dist/        # want 0 — emails
grep -rl 'daily_buckets\|<telemetry-key>' dist/  # want 0 real data (code property-names are OK)
grep -roE '"20[0-9]{2}-[0-9]{2}-[0-9]{2}":\{' dist/  # want 0 — real data blobs
```
Note: a couple of hits are usually **code** (a property-name string like `e.daily_buckets||{}`), not data — inspect context. Real PII = a big object of values. See Phase 5 for how to keep fixtures out of the bundle.

## 4. Visual check

Screenshot the hero/most-changed pages (fixtures mode) and actually LOOK: is the DEWA logo in the sidebar? Is the brand green DEWA (not the generic Astryx green)? Do the restored features render (the filter, the chart, the drawer)? Light AND dark mode.

## 5. Commit

Commit the verified state. Each phase is one reversible commit on top of the `baseline`.

## Reusable check scripts

`prod-verify.mjs`-style scripts (hit the live URL, admin-unlock, screenshot, report `pageerror`) are worth keeping in the app's `scripts/` for post-deploy verification too. Read the admin password from an existing script rather than hardcoding a new copy.
