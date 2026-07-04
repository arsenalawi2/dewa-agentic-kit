---
name: dewa-ui-migration
description: "Migrate any existing web UI (Vue, React, Angular, static HTML, or a legacy design system) to React 19 + the DEWA-themed Astryx design system — WITHOUT dropping features. A five-phase, agent-fanned-out playbook: audit → DEWA-fy → fix → verify → deploy. Use when re-skinning or rebuilding a DEWA app onto Astryx, or whenever someone says 'migrate this UI to Astryx' / 'DEWA-fy this app'. Keywords: UI migration, Astryx, DEWA, re-skin, design system migration, Vue to React."
user-invokable: true
metadata:
  author: DEWA
  version: "1.1.0"
  origin: "leaderboard.hadismac.com Vue/EZ → React/Astryx migration, 2026-07-04"
args:
  - name: source
    description: "Path to the OLD/source app (the UI being migrated from)"
    required: false
  - name: target
    description: "Path to the NEW React/Astryx app (the first-pass rewrite you are auditing + fixing)"
    required: false
---

# DEWA UI Migration — old UI → React 19 + DEWA-Astryx

Migrate a web UI onto **React 19 + Astryx** (an open-source React + StyleX design system, `@astryxdesign/core`, MIT) re-skinned in **DEWA brand** (green `#007560`, Figtree + JetBrains Mono, the DEWA logo, the AED dirham glyph) — **without losing features**. Built from the 35-page DEWA Fleet Leaderboard migration, where a one-shot rewrite silently dropped 64 features — so rule #1 is **audit before you celebrate**.

## When to use

- Re-skinning or rebuilding a DEWA app onto Astryx.
- Verifying a migration already done in one shot (find what it dropped).
- Any "migrate this UI to Astryx" / "DEWA-fy this app" / "port from Vue/Angular/HTML to our design system" request.

## Before you start (prerequisites)

- **Node 20+ / npm**, and the target app buildable with **Vite**.
- **`@astryxdesign/core`** from npm. It is **0.1.x (beta)** — pin the exact version and expect API churn between minors. `npm i @astryxdesign/core @astryxdesign/theme-neutral`.
- **The `Workflow` tool** — the audit + review phases fan out via the `Workflow` orchestration tool (see "How the audit runs" in `references/01-audit.md`). If your harness does NOT expose `Workflow`, use the documented **Task-based fallback** there (launch N parallel subagents by hand with the same find→verify structure). Nothing else in the skill needs `Workflow`.
- **Playwright** for the verify phase: `npm i -D playwright && npx playwright install chromium`.
- **DEWA brand assets**: the logo files live at `~/dewa-design-system/assets/` (`dewa-logo.png` = wordmark, `dewa-logo-small.png` = swirl mark). If that folder isn't present, ask the user for the DEWA logo.
- **`dak init <name>`** (optional) scaffolds a React+Astryx+DEWA app with the theme, `<Aed>`, logo and auto-pages already wired — start there for greenfield and skip most of Phase 2.

## Phase 0 — precondition + cutover strategy (decide before touching code)

**Precondition — what "audit" needs.** Phases 1/3 compare the OLD app against a **first-pass React/Astryx rewrite of the target** and restore what's missing. So the target app must already exist in rough form. Two entry points:
- **Verify-a-rewrite** (the leaderboard case): a first-pass rewrite exists → audit it against the old app, restore gaps. Run phases 1→5.
- **Greenfield**: no rewrite yet → do Phase 2 (stand up the shell) FIRST, treat the Phase-1 audit of the OLD app as your **full feature spec** (every feature is a "gap" to build), then fix/verify/deploy.

**Cutover strategy — big-bang vs incremental.**
- **Big-bang** (audit all → fix all → swap the whole dist at once): fine for small/medium apps you can feature-freeze during the migration. This is what the phases below describe.
- **Incremental / strangler**: for large apps or teams that can't freeze — split at the router or the tunnel so old and new run side-by-side, migrate route-by-route behind a flag, share session/auth. Run phases 1–5 per route-group instead of once.
- **Moving-target rule (critical):** if the old app keeps shipping during the migration, your audit + per-page specs go stale and you cut over to a spec that no longer matches production. So: **freeze the old app, or pin it to a git SHA, record that SHA in the audit report, and before cutover diff the old app since that SHA** and re-audit anything that changed.

## The core insight

A one-shot rewrite **looks** done but silently drops filters, drill-downs, charts, edge-case states, and interactions — the stuff not in the happy-path screenshot. This skill is **feature-preservation-first**: enumerate the old behavior exhaustively, fan out parallel agents to restore each page, and adversarially verify nothing is missing before declaring done.

## The five phases

| Phase | Goal | Reference | Key asset |
|---|---|---|---|
| **1. Audit** | Enumerate EVERY feature of the old UI, page-by-page + cross-cutting; produce a verified gap list | `references/01-audit.md` | `assets/audit-workflow.js` |
| **2. DEWA-fy** | Stand up React+Astryx + the DEWA theme (green, fonts, logo, AED) | `references/02-dewafy.md` | `assets/dewa.css` |
| **3. Fix** | Fan out one agent per page (disjoint files) to restore gaps + apply Astryx/DEWA | `references/03-fix.md` | — |
| **4. Verify** | Build green + smoke test (no crashes) + **feature-parity** + a11y + PII scan + visual | `references/04-verify.md` | `assets/smoke.mjs` |
| **5. Deploy** | PII-safe prod build + backup + swap + verify live + rollback | `references/05-deploy.md` | `assets/build-prod.mjs` |
| **The hard parts** | Global state, data-fetching, a changing backend, and accessibility | `references/06-hard-parts.md` | — |

## Non-negotiable principles (learned the hard way)

1. **Audit is fan-out, not a glance.** One agent per page + cross-cutting sweeps, each finding **adversarially re-verified** against the whole new codebase. A human read misses the dropped monthly filter; 40 agents don't.
2. **Parallel fix agents own DISJOINT files.** One page file each. Build + commit shared infra FIRST so page agents consume it. Namespace new components (`<Page>Thing.jsx`). Never two agents on one file.
3. **A green build is necessary, not sufficient.** It won't catch React runtime crashes (bad hook order, `undefined` styles, invalid Astryx props like `<Avatar size="md">`). Run the smoke test — and prove features *work*, not just render (Phase 4).
4. **DEWA-fy at the token layer.** Override Astryx's accent AND its generic-green family in one theme file (`assets/dewa.css`), then sweep stray hex greens. Don't recolor per-component.
5. **Never regress privacy on deploy.** `rsync --delete` wipes files the new build lacks (e.g. hook-generated `vibe-stats.json`) — carry them over. Production must NOT ship real fixtures/PII: `assets/build-prod.mjs` + strip emails from bundled data. Verify `dist/` is clean before shipping.
6. **git init the target first.** A `baseline` commit = one-command rollback + clean per-wave diffs. Commit after each phase.
7. **The old app is the spec.** Keep it readable side-by-side. Pin its SHA if it's still moving (Phase 0).

## Fast start (exact commands)

```bash
# Phase 1 — git init target + baseline; run the audit workflow (needs the Workflow tool)
git -C <target> init && git -C <target> commit -am baseline
#   Workflow({ scriptPath: '<skill>/assets/audit-workflow.js', args: { OLD, NEW, pages[] } })
#   → per-page confirmed-gap specs. No Workflow tool? Use the Task fallback in 01-audit.md.

# Phase 2 — Astryx + DEWA theme (or `dak init` for greenfield)
npm i @astryxdesign/core @astryxdesign/theme-neutral
cp <skill>/assets/dewa.css <target>/src/styles/dewa.css   # wire per 02-dewafy.md

# Phase 3 — build shared infra + commit; fan out 1 agent/page from the specs (see 03-fix.md)

# Phase 4 — verify. NOTE: the scripts use bare `playwright` imports, so run them FROM the app dir:
npm run build
cp <skill>/assets/smoke.mjs <target>/_smoke.mjs && ( cd <target> && VITE_USE_FIXTURES=1 npm run dev -- --port 3899 & sleep 4; node _smoke.mjs; rm _smoke.mjs )

# Phase 5 — PII-safe build + swap (run build-prod from the app dir; see 05-deploy.md)
cp <skill>/assets/build-prod.mjs <target>/scripts/build-prod.mjs
( cd <target> && node scripts/build-prod.mjs )   # blanks fixtures out of the bundle, then restores
#   back up the live dist, rsync --delete-after dist over it, verify live, record rollback.
```

Read each phase reference before running it — the gotchas there each cost real debugging time on the first migration. Scale the fan-out to the app: a 5-page app needs a handful of agents; a 35-page app needs ~40 in the audit and ~20 in the fix wave.
