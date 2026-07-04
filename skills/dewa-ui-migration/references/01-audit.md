# Phase 1 — Audit (find everything the migration would drop)

**Goal:** a verified, per-page list of every feature in the OLD UI, and whether the NEW app reproduces it. This is the most important phase — a one-shot rewrite silently drops ~60% of the non-happy-path behavior.

## Why fan-out, not a read

On the leaderboard migration, a careful human read of the new app looked "basically complete." A 39-unit / 133-agent audit found **64 confirmed regressions** — monthly filters, per-player drill-downs, whole charts, dead-stub buttons, error states. You cannot eyeball this at scale. Fan out.

## The work-list

1. **git init the target** and make a `baseline` commit first.
2. Determine the SERVED file for each route. If the new app has variant folders (e.g. `faithful/` vs `redesign/`) resolve which one actually renders (read the router / page-registry + the default direction). Audit the *served* file, not a dormant variant.
3. Build the unit list:
   - **One unit per page/route.** Map each to `{oldFile, newServedFile}`.
   - **Cross-cutting units:** `routes & nav` (every old route + nav item vs new), `data layer` (old data hooks/composables/services vs new — a dropped data capability = a dead feature), `charts & shared components` (every old chart/viz vs new).

## How the audit runs — the Workflow tool (and a fallback)

`assets/audit-workflow.js` is a script for the **`Workflow` tool** — an orchestration tool that runs many subagents deterministically (fan-out, pipelines, adversarial-verify stages) and is available to Claude Code in this environment. The script uses these Workflow primitives: `agent(prompt, opts)` (spawn a subagent, `schema` forces structured output), `pipeline(items, stage1, stage2)` (run each item through stages with no barrier), `parallel(thunks)` (concurrent, barrier), `phase()`/`log()`, and `args` (the object you pass in). You run it with:
```
Workflow({ scriptPath: '<skill>/assets/audit-workflow.js', args: { OLD, NEW, pages, crosscuts } })
```
It returns `{confirmed, presentElsewhere, criticNotes, perUnit}` — read it and write a spec file per page.

**No `Workflow` tool in your harness?** Do the same by hand with plain subagents (the `Task`/`Agent` tool): for each unit, launch a **gap-finder** subagent (prompt = the Stage-1 prompt below, one per page, in parallel batches of ~8), collect their structured gap lists, then for each non-trivial gap launch an independent **verifier** subagent (Stage-2 prompt) to try to refute it. Keep the two-stage find→adversarially-verify structure — that's what matters; the Workflow tool just automates the fan-out.

## The audit workflow

`assets/audit-workflow.js` **pipelines** each unit through two stages:

- **Stage 1 — gap find:** an agent reads the old file(s) + follows its imports (old components/composables), reads the new served file + follows ITS imports, and greps the WHOLE new src to see if a feature moved. It returns structured gaps: `{title, category, severity, status, oldEvidence, newEvidence}` where `status ∈ missing | dead-stub | changed | moved-elsewhere`. **Dead-stub** = a control that renders but does nothing (state set but never read, button with no handler) — these are the sneakiest.
- **Stage 2 — adversarial verify:** for each non-trivial gap, an independent agent tries to REFUTE it — searches the entire new app (all variants + shared) for the feature. Verdict `∈ confirmed_gap | dead_stub_confirmed | present_elsewhere | false_positive | intentional_by_design`. Default to `confirmed_gap` only after searching. This is what kills false positives (on the real run, 29 of 93 candidate gaps were refuted).

Then a **completeness critic** agent looks for whole CLASSES the per-unit pass missed: dropped routes with no new equivalent, removed global controls (theme toggle, search, analytics), app-shell features, guard/auth behavior changes, and near-empty placeholder pages.

Invoke it:
```js
// args = { OLD: '/abs/old/src', NEW: '/abs/new/src', pages: [{name, oldFile, newFile}, ...] }
Workflow({ scriptPath: '<skill>/assets/audit-workflow.js', args })
```
Read the returned `{confirmed, presentElsewhere, criticNotes, perUnit}` and turn `confirmed` into a per-page spec file the fix agents will consume (Phase 3).

## What each finder MUST check per page

filters/toggles/period-or-month pickers · search boxes · sort controls · CSV/export · tabs · per-row actions · drawers/modals · tooltips · KPIs/metrics · table columns · charts/visualizations · empty/loading/error states · auto-refresh/polling · **who can see it** (player vs admin gating) · dead stubs.

## Output

- A markdown report (themes + per-page confirmed gaps + severity + fix hint).
- One spec file per page under a `specs/` dir — each fix agent reads its spec. Keep the fix hints concrete (`file:line` on both sides).

## Gotchas

- **Severity drift:** verifiers tend to cap at "medium". Read "medium" as "a real feature a user will notice is gone." Group by theme so the systemic losses (e.g. an entire Monthly dimension gone from 5 pages) are obvious.
- **One unit can crash the pipeline.** The data-layer cross-cut once failed its structured-output retries — fill that gap by hand (grep the old data hooks and check each has a new equivalent). Don't let one failed unit hide a whole class.
- **Token cost is real but worth it:** the leaderboard audit was ~6.75M subagent tokens for 133 agents. That bought certainty. Scale finder count to app size.
