# Warm-Neutral Design System

A general-purpose, product-agnostic design system **distilled from the rammas-72k frontend** and generalized so it works for an app, a dashboard, a shopping site, a report, or a strategy HTML — anything.

It is plain CSS + design tokens. No build step, no framework, no JS required (a few components use ~10 lines for open/close behaviour). Write semantic HTML, add classes when you need a component.

```
design-system/
├── index.css         Single entrypoint — @imports the three layers in order + Inter (the DAK `~/design-system/index.css` contract)
├── tokens.css        Design tokens — colors, type, space, radius, elevation, motion, z, layout, currency (+ dark theme)
├── base.css          Reset + webfont + global document typography + utilities (.prose, .container, .u-label, .dirham-symbol, …)
├── components.css    Reusable class library (.btn, .card, .badge, .segmented, .sheet, .table, …)
├── fonts/            UAESymbol webfont (woff2/woff/ttf) — the UAE Dirham glyph, shipped so currency is self-contained
├── components/       Optional Vue adjuncts — Icon.vue (<Icon name> SVG icons), Aed.vue (<Aed :value> currency), Sparkline.vue (inline trend SVG),
│                      Chart.vue + chart-theme.js (token-themed Chart.js), motion.js (motion-v presets). Charts/motion need peer deps — see below.
├── preview.html      Living styleguide — open in a browser; doubles as the visual contract
├── showcase.html     App-shell demo — hover-expand rail + topbar + KPIs + table + sheet, the dashboard pattern in action
└── DESIGN_SYSTEM.md  This document
```

**Quickstart** — one import (pulls the three layers in order, plus Inter):

```html
<link rel="stylesheet" href="design-system/index.css">
```

```js
import "@ds/index.css"   // Vite, with @ds aliased to ~/design-system
```

Or hand-wire the three layers — **order matters** (tokens first):

```html
<link rel="stylesheet" href="design-system/tokens.css">
<link rel="stylesheet" href="design-system/base.css">
<link rel="stylesheet" href="design-system/components.css">
<!-- Inter (the UI family). Omit to fall back to the system sans stack. -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

Open `preview.html` to see everything rendered (with a light/dark toggle); open `showcase.html` for the full app shell with the hover-expand rail.

---

## Principles

1. **Warm paper, never glare.** The canvas is `#faf9f7`, ink is `#23221f`. No pure `#fff` / `#000` anywhere.
2. **Borders do the work; shadows are a whisper.** Structure comes from 1px hairlines. Shadows appear only on things that genuinely float (focus ring, FAB, sheet, media viewer).
3. **One accent, one secondary.** A single dark-green primary (`#0f4024`) carries actions and emphasis. A violet secondary marks a *parallel track* (a second mode, an upsell tier, an advisory voice) — use it sparingly.
4. **Color is semantic.** Green = primary/positive, violet = secondary, amber = warning/attention, red = danger. A reader should infer meaning from hue.
5. **One type family, real mono for data.** Inter for all UI and prose; a true monospace only for IDs, codes, and figures. "Micro-labels" are not a font — they're uppercase + letter-spacing on Inter (`.u-label`).
6. **Quiet motion.** ~120 ms ease-out transitions. Panels slide; nothing bounces, glows, or blurs.
7. **Panels, not modals.** Detail and navigation slide in from an edge and preserve context. Center-screen modals are avoided; the one full-screen overlay is the media viewer.
8. **Single reading column.** Long-form content sits at ~760px for legibility; dashboards widen to ~1100px.

---

## What was generalized away

This system is the *reusable substrate* of rammas-72k, not its RAG UI. The mapping:

| rammas-72k (specific) | here (general) |
|---|---|
| precise/strategic **mode toggle**, sonnet/opus **model picker** | `.segmented` control |
| "latest only" filter | `.toggle` pill |
| **source cards** (doc/rev/page) | `.card` / `.media-card` |
| inline **citation chips** `[1]` | *dropped* (domain-specific) |
| assistant card / user bubble | `.card` / generic message block |
| green=corpus / violet=strategic semantics | primary / secondary accent |
| analytics drilldown | `.sheet` (side panel) |
| image lightbox | `.viewer` |
| voice/mic recording button | `.btn-icon` with state classes |

The **foundations** (palette, type, spacing, elevation, motion) carried over unchanged — they were never RAG-specific.

---

## Foundations

### Color

Tokens come in three layers. **Components only ever touch the semantic layer**, so re-theming = re-pointing aliases.

- **Primitive ramps** — `--neutral-{0…900}`, `--green-{50…900}`, `--violet-{50…800}`, `--amber-{100…800}`, `--red-{50…700}`. Raw steps; don't use directly.
- **Semantic aliases** — `--color-bg`, `--color-surface`, `--color-text`, `--color-text-muted`, `--color-border`, `--color-primary`, `--color-secondary`, `--color-success|warning|danger|info` (each with `-soft` / `-border` companions).
- **Compat block** — the original rammas names (`--bg`, `--accent`, `--text-primary`, …) are aliased onto the semantic layer so the existing app adopts this file as a drop-in superset. Delete that block for a fresh project.

| Role | Light | Meaning |
|---|---|---|
| primary | `#0f4024` | actions, links, emphasis, "current/positive" |
| secondary | `#6d28d9` | a parallel mode / tier / category |
| warning | `#92400e` on `#fef3c7` | attention, superseded, privileged |
| danger | `#d64545` | errors, destructive |
| bg / surface | `#faf9f7` / `#ffffff` | canvas / raised |
| text / muted / subtle | `#23221f` / `#65635d` / `#a8a69f` | ink ladder |

### Typography

- **Family:** Inter (`--font-sans`, also `--font-display`); `--font-mono` is a real monospace stack for data.
- **Weights:** 400 / 500 / 600 / 700 / 800.
- **Scale:** `--text-2xs (10)` → `--text-4xl (28)`. Headings get tight tracking; the big display heading goes to `-0.02em`.
- **Micro-labels:** `.u-label` = 11px, uppercase, `0.05em` tracking, subtle color — the "engineering eyebrow" used above sections, stat tiles, and form fields.
- Inter glyph niceties are on (`font-feature-settings: 'cv11','ss01'`); `.u-mono` enables tabular figures.
- **Currency (AED is the default).** A third, glyph-only webfont — **UAESymbol** — ships in `fonts/` and is loaded by `base.css` (`@font-face`), so currency is self-contained; no extra `<link>` needed. Render the official UAE Dirham symbol by wrapping the glyph `ê` (U+00EA) in `.dirham-symbol` (or its alias `.currency-aed`): `<span class="dirham-symbol">&#xea;</span> 1,290`. Tokens: `--currency-symbol`, `--currency-code`, `--usd-to-aed` (the 3.6725 peg), and `--font-currency`. This does **not** break the "one type family" rule — UAESymbol is an icon glyph, not a text family; all surrounding figures stay in Inter/mono. **Vue:** an optional `components/Aed.vue` mirrors the global `~/design-system` `<Aed :value="1234" />` API (props: `decimals`, `fromUsd`, `compact`, `locale`) for projects that prefer a component over the class.

### Spacing, radius, elevation

- **Space:** 4px grid, `--space-1 (4)` → `--space-15 (60)`.
- **Radius:** `--radius-xs 3` (tags/code) · `sm 6` (chips/cards) · `md 8` (buttons/inputs, the default) · `lg 12` (large surfaces) · `xl 14` (hero/dropzone) · `pill 999`.
- **Elevation:** `--shadow-xs/sm/md/lg`, plus `--shadow-focus` (keyboard ring), `--shadow-panel-*` (sheets), `--shadow-overlay` (viewer). If you reach past `--shadow-md` for a resting element, reconsider — use a border.

### Motion

`--dur-base 0.12s` is the default; `--dur-panel 0.18s` for sliding sheets; `--ease-out` everywhere. Keyframes provided: `spin`, `dot-pulse`, `fade`, `slide-in-right/left`. All respect `prefers-reduced-motion`.

**JS motion (optional) — `components/motion.js`.** For interactive motion beyond CSS keyframes (spring/gesture/layout/presence), the kit ships **motion-v presets** pinned to these exact tokens, so motion stays *quiet* (no bounce/overshoot). `npm i motion-v`, then `import { riseIn, slideInRight, pressable, popIn } from "@ds/components/motion.js"` and spread onto a `<motion.*>` element (`<motion.div v-bind="riseIn">`). Presets: `fade`, `riseIn` (cards/rows), `slideInRight/Left` (panels — EZ prefers panels over modals), `popIn` (dialog/toast), `pressable`/`hoverLift` (interaction), `stagger(i)` (lists). Raw building blocks (`EZ_EASE`, `tFast/tBase/tPanel`, `springQuiet`) are exported too. motion-v does **not** auto-honor reduced motion — keep base.css's `prefers-reduced-motion` guard, or gate with motion-v's `useReducedMotion()`.

### Z-index & layout

Named ladder: `--z-sticky 50` · `--z-backdrop 90` · `--z-nav 100` · `--z-panel 200` · `--z-dropdown 300` (menus open above sheets) · `--z-modal 1000` · `--z-toast 1100` (a toast must survive an open modal) · `--z-tooltip 1200` (tooltips beat everything). Layout widths: `--layout-rail 64` (collapsed icon rail), `--layout-sidebar 240`, `--layout-reading 760`, `--layout-container 1100`, `--layout-sheet 560`. Breakpoints `--bp-sm 640`, `--bp-md 768`.

### Chart tokens

Charts use the **sanctioned categorical sequence** `--chart-1 … --chart-6`, plus `--chart-grid` (axes/gridlines) and `--chart-label` (axis text) — all dark-theme aware. Feed them to any library (Chart.js, echarts, d3, recharts, plain SVG) via `getComputedStyle(document.documentElement).getPropertyValue('--chart-1')` or inline `var()` in SVG. Never hand-pick hexes in app code.

**Chart.js adjunct (optional) — `components/Chart.vue` + `components/chart-theme.js`.** The kit ships a ready bridge so charts inherit the tokens above with zero hex-picking. `npm i chart.js`, then:

```vue
import Chart from "@ds/components/Chart.vue"
<Chart type="line"     :data="{ labels, datasets:[{label:'Opus', data:[…]}] }" :y-format="v => v+'B'" />
<Chart type="doughnut" :data="{ labels:['Opus','Sonnet','Haiku'], datasets:[{ data:[52,33,15] }] }" />
<Chart type="bar"      :data="…" :legend="false" />   <!-- single metric → one accent -->
```

`<Chart>` auto-colors datasets from `--chart-1…6`, applies clean defaults (hairline grid, no plot border, tabular-mono ticks, card tooltip, point-style legend), and **re-themes itself on light/dark switch** (it watches `<html>` for `class`/`data-theme`). Pass your own dataset colors or an `options` object to override. For vanilla (non-Vue) charts, import `chartColors()` + `chartBase()` from `chart-theme.js` and hand them to Chart.js directly. **Convention:** categorical palette for category *identity* (series/segments); a single accent (`--color-primary`) for a single-metric comparison (one green bar set) — don't rainbow a single metric.

---

## Component catalog

All in `components.css`. Grouped; see `preview.html` for every variant rendered.

- **Buttons** — `.btn` + `.btn-primary | -secondary | -ghost | -subtle | -danger`; sizes `.btn-sm/-lg`, `.btn-block`, `.btn-pill`, `.btn-icon` (circular), `.fab` (floating).
- **Selection** — `.segmented` + `.segmented-opt.is-active` (add `.alt` for the secondary tint); `.toggle.is-on`; `.tabs` + `.tab.is-active`.
- **Forms** — `.field` + `.label` + `.hint`; `.input`, `.textarea`, `.select`; `.input-group` (leading icon); `.dropzone.is-active`. **Validation:** `.field.is-invalid` (or `.input.is-invalid`) + a `.field-error` message line; `.label.required` adds the asterisk. Native checkboxes/radios/range follow the brand via `accent-color` (base.css) — never rebuild them.
- **Cards** — `.card` (`.card-sm`, `.card-hover`, `.is-selected`); `.card-head/-title/-sub`; `.stat-card` + `.stat-value/-label` (status tints `.is-success/-warning/-danger`); `.media-card` + `.thumb`.
- **Status & markers** — `.badge-*` (+`.badge-pill`), `.tag`, `.count`, `.chip` + `.chip-remove`, `.index-badge`, `.avatar`, `.dot-*`, `.pulse-dots`, `.spinner`.
- **Currency** — `.dirham-symbol` / `.currency-aed` renders the UAE Dirham glyph (`ê`); pair with mono figures for amounts. See Typography → Currency above.
- **Feedback** — in-flow: `.alert-success/-warning/-danger/-info`. Floating: one fixed `.toaster` per app holding `.toast.toast-success/-warning/-danger/-info` nodes (append + auto-remove from app JS; `preview.html` has the 8-line reference implementation).
- **Loading** — `.skeleton` / `.skeleton-text` / `.skeleton-circle` (shimmer) for page furniture; `.spinner` for in-button/action waits; `.pulse-dots` for streaming.
- **Tooltip** — `data-tooltip="…"` attribute = pure-CSS hover/focus tip; `.tooltip` = a styled surface your JS or chart library positions.
- **Menu** — `.menu` + `.menu-item` (`.is-active`, `.is-danger`) + `.menu-sep`: the dropdown/popover/search-results surface at `--z-dropdown`. Positioning is the app's job (wrapper with `position:relative`, your JS, or the native Popover API) — the system styles the box only.
- **Chat** — `.chat` (scrolling column) + `.bubble.bubble-user/-assistant/-error` + `.composer` (input bar). Typing = a `.bubble-assistant` containing `.pulse-dots`; markdown in a bubble = add `.prose`. This fleet builds AI chat UIs — bubbles are core vocabulary here.
- **Data** — base `<table>` is report-grade; `.table-card` frames it; `.num` right-aligns tabular figures; `.list` + `.list-row.is-active`; `.bars/.bar` chart; `.meter` + `.meter-fill` (`.is-warning/.is-danger`) for determinate progress. Interactive tables: `th.is-sortable` + `.is-sorted-asc/-desc` (sort logic stays in app JS), `.table-card--scroll` pins the header (`--table-max` sets the height), `.pagination` + `.pagination-info` + `.pagination-buttons` (fill with `.btn.btn-sm`).
- **Shell** — `.app-shell` (sidebar grid), `.sidebar` + `.sidebar-top/-scroll/-footer`, `.brand`, `.main`, `.topbar` + `.hamburger`.
- **Hover-expand rail** — add `.app-shell--rail` to the shell and the sidebar rests as a 64px icon rail that expands to 240px **as an overlay** when the pointer is on or near it (12px grace strip, 240ms collapse delay, `:focus-within` for keyboard). Content never reflows; no collapse button, no JS. Markup contract: put an **SVG icon** (an `<Icon name="…">` / inline `<svg>`, **never a Unicode glyph like ◆ ◇ ▤** — those render inconsistently) in `.rail-icon` and the text in `.rail-label` (labels fade out when collapsed). This is the **recommended default shell for new apps** — `showcase.html` runs on it, and the dak-template ships it by default.
- **Overlays** — `.scrim.to-right` + `.sheet` (detail panel), `.drawer.is-open` + `.drawer-scrim` (mobile nav), `.viewer` (full-screen media). Collapses to a drawer under `--bp-md`.
- **Dialog** — `.dialog-scrim` + `.dialog` + `.dialog-title/-actions`: the **sanctioned exception** to "no center modals", for tiny interrupts only (password gate, destructive confirm — one question, two buttons). Anything with content belongs in a `.sheet`. App JS owns Enter/Escape and returning focus.
- **Auth** — `.auth-shell` (centered viewport) + `.auth-card` + `.auth-brand`; error slot is an `.alert.alert-danger`, fields are normal `.field` blocks, submit is `.btn-primary.btn-block`. Stop rebuilding login screens.
- **Empty state** — `.empty` + `.empty-icon/-title/-sub`.
- **Icons** — `components/Icon.vue` is a dependency-free SVG line-icon set: `<Icon name="home" />` (24×24, `currentColor`, stroke 1.5, sizes via the `size` prop). Names: `home flag layers code clipboard dashboard chart users settings search file database bell inbox plus check close chevron sun moon spark`. Use these for nav/rail icons — **not** Unicode glyphs. Add an icon by appending a name→paths entry in `Icon.vue`.
- **Vue adjuncts** (optional, in `components/`) — `<Icon name>` (SVG icons), `<Aed :value>` (currency), `<Sparkline :values="[…]">` (inline trend SVG on `--chart-1`), `<Chart type :data>` (token-themed Chart.js — needs `npm i chart.js`), and `motion.js` presets (quiet motion-v transitions — needs `npm i motion-v`). The two engine-backed adjuncts are the only parts of the kit with peer dependencies; everything else is dependency-free. See Foundations → Motion / Chart tokens.

---

## Using it for any project

**A report / strategy HTML** — you barely touch components. Wrap content in `.container` (or `.card.prose`) and write semantic `<h1>…<table>`. `base.css` styles it. Use `.u-label` for eyebrows, `.badge-*` for status, `.stat-card` for headline numbers.

**A shopping site** — `.media-card` for products, `.tag` for "new"/"sale", `.badge-*` for stock status, `.btn-primary` for add-to-cart, `.segmented` for list/grid, `.toggle` for filters, `.sheet` for the cart drawer, `.table-card` for the order list. (All shown in `preview.html`.)

**An app / dashboard** — `.app-shell.app-shell--rail` + `.sidebar` for the frame (icon rail that expands on hover), `.stat-card` + `.bars` for metrics, `.list-row` for feeds, `.sheet` for detail drilldowns.

### Theming

Override the **semantic layer** in a scoped block — e.g. a blue primary:

```css
:root { --color-primary: #1e40af; --color-primary-hover: #1c3a96;
        --color-primary-soft: #dbeafe; --color-primary-soft-border: #bfdbfe; }
```

Nothing else changes; every component re-tints.

### Dark mode

First-class and built in (the source app shipped light-only — this adds the missing theme). Activate with `<html data-theme="dark">` (or the `html.dark` class — both selectors work) and toggle at runtime. There is **no automatic `prefers-color-scheme` switch** — the app owns its theme; opt in to OS-following with three lines of JS if you want it (`matchMedia("(prefers-color-scheme: dark)").matches && document.documentElement.setAttribute("data-theme","dark")`). The dark palette lifts the neutral ramp to a warm dark scale and brightens the brand hues for contrast.

### Accessibility

- Keyboard focus shows a visible ring everywhere via `:focus-visible` (`--shadow-focus`) — don't remove it.
- All motion collapses under `prefers-reduced-motion: reduce`.
- Color is never the *only* signal — pair status hues with text/icons (the alerts and badges in `preview.html` do this).
- Body text is 14–16px; the smallest type (10–11px) is reserved for non-essential labels.
- **Skip link:** sidebar-first layouts force keyboard users through the whole nav — add `<a class="skip-link" href="#main">Skip to content</a>` as the first element and `id="main"` on `.main`. It stays invisible until focused.
- **Focus discipline for overlays:** when a `.sheet`, `.drawer`, or `.dialog` opens, move focus into it; on close, return focus to the trigger. Escape closes. That's ~10 lines of app JS — the system deliberately ships no focus-trap machinery.

### Print

`base.css` ships an `@media print` block tuned for the report/strategy genre: app chrome (sidebar, topbar, buttons, toasts, pagination) disappears, the content column expands, cards/tables/headings avoid page breaks, and paper is plain white/black (the warm-neutral rule is a screen rule). A `.prose` report prints clean with zero work; check `Cmd+P` before shipping any exec-facing page.

### RTL / Arabic (readiness, not yet mirroring)

All directional CSS uses **logical properties** (`border-inline-start`, `inset-inline-end`, `text-align: start/end`), so `<html dir="rtl">` flips layout correctly today. Two caveats before shipping an Arabic app: **Inter has no Arabic glyphs** (text falls to system fonts — pick and load an Arabic family, e.g. Dubai or IBM Plex Sans Arabic, and extend `--font-sans`), and the slide-in animations (`slide-in-right/left`) are still physical — acceptable, but mirror them when the first Arabic app lands.

---

## Notes & normalization (vs. the source)

Things tightened while generalizing — relevant if you compare against the live rammas frontend:

- **Real monospace restored.** The source's `--font-mono` actually resolved to *Inter*; here it's a genuine monospace, and the "label" look is a utility (`.u-label`), not a font.
- **Color ramps tokenized.** The source hard-coded the violet/amber/red families inline (never as variables); here they're full ramps under the semantic layer, which is what makes dark mode and re-theming work.
- **Scales rationalized.** Half-pixel font sizes (12.5/13.5/14.5px) and ~11 ad-hoc radii were folded into clean `--text-*` and `--radius-*` scales.
- **Dark mode + reduced-motion + `:focus-visible` added** — none existed in the source.
- **One accent-hover, not two.** The source defined `--accent-hover` (`#14532d`) but components used `#0a2e1a`; standardized on the darker pressed green.

These are intentional improvements, not transcription drift — the visual identity (warm neutrals, the green, the spacing rhythm) is preserved exactly.
