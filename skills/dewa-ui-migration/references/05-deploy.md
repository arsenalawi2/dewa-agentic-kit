# Phase 5 — Deploy (PII-safe, reversible, verified live)

**Goal:** ship the built app to production with no PII in the bundle, a one-command rollback, and live verification. Only deploy on explicit go-ahead.

## Deploy model (static-dist-behind-a-tunnel)

The DEWA leaderboard serves a static `dist/` directory from a container (bind-mounted, `StaticFiles`) behind a Cloudflare tunnel. **Deploy = swap the dist directory** — no restart, served live, reversible. Adapt to your host, but the shape is the same: build → back up current → swap → verify → keep rollback.

## The PII-safe production build

Real dev-fixtures (sample per-user data) and any bundled data file (e.g. a departments map with emails) end up in the downloadable JS. Fixtures are never *loaded* in prod (the resource layer gates the fallback on `import.meta.env.DEV || VITE_USE_FIXTURES`), but Rolldown still **bundles** the dynamic-import chunks. So:

- **Strip PII from bundled data files permanently** (e.g. remove `email`/`employee_name` from a departments JSON; keep only what the app actually reads, and make the code degrade — `x.email || x.name`).
- **Build with `assets/build-prod.mjs`, not `npm run build`.** It blanks the dev-fixtures on disk → `vite build` → restores them (so local dev keeps real fixtures). Result: fixtures excluded from the shipped bundle.
- **Verify** the built `dist/` per Phase 4's PII scan: 0 emails, 0 telemetry blobs.

## The swap

```bash
TS=$(date +%Y%m%d-%H%M%S)
LIVE=<path-to-served-dist>
rsync -a "$LIVE/" "$LIVE.bak-$TS/"                    # 1. backup current live
node scripts/build-prod.mjs                            # 2. PII-safe build → dist/
rsync -a --delete-after ./dist/ "$LIVE/"              # 3. swap (delete-after = no broken-asset window)
```

**`rsync --delete-after` GOTCHA (this broke the live site once):** it deletes files present in the old live dist but NOT in your new build — e.g. hook-generated files like `vibe-stats.json`, `journey-data.json`, `tech-stack.json` that live in the served dist but not in your `public/`. Carry them over: put them in your app's `public/` (so every build includes them) OR copy them into the live dist after the swap. Otherwise those pages 404.

## Verify live

- Poll the origin until it serves your new entry chunk: `curl -s <origin>/ | grep -oE 'index-[A-Za-z0-9_-]+\.js'` should match `dist/index.html` (allow a few seconds for macOS virtiofs to catch up).
- Run the `prod-verify.mjs`-style live check: admin-unlock, screenshot, assert `pageerror: none`.
- Eyeball the live hero pages: DEWA logo, DEWA green, restored features.

## Rollback (always record it)

```bash
rsync -a --delete-after <LIVE>.bak-<TS>/ <LIVE>/
```
Keep this line in your report and in memory. Also commit the source so `git` is a second rollback path.

## Deploy discipline

- Do NOT deploy until the user explicitly approves reviewing the result — offer a staging URL vs production.
- One backup per deploy, timestamped. Each is a rollback point.
- After deploy, update the auto-updating data files (`journey-data.json`, `vibe-stats.json`) so `/journey` and `/vibe-code` reflect the new stack + the migration itself.
