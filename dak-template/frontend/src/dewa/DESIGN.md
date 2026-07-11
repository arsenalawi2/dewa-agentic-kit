# DEWA-Astryx Design System (this project)

This app is styled with **DEWA-Astryx** — the open-source [Astryx](https://www.npmjs.com/package/@astryxdesign/core)
design system (React + StyleX, MIT) re-skinned with DEWA's brand. Everything the
brand layer needs is bundled in **this folder** (`frontend/src/dewa/`), so the app
is self-contained — there is no external design-system dependency to install or mount.

## The 30-second version

- **Components** come from Astryx, one per subpath:
  `import { Button } from '@astryxdesign/core/Button'`. The app shell is
  `AppShell` + `SideNav` (see `src/app/App.jsx`).
- **Theme** is two attributes on `<html>` (set in `index.html`):
  `data-astryx-theme="dewa"` (the brand) and `data-astryx-mode="light|dark"` (the mode).
  **The app owns its mode** — toggle it in JS (`src/lib/theme.js`); there is no OS auto-switch.
- **Brand green** `#007560` (light) / `#33c2a4` (dark), wired as Astryx `--color-accent`.
- **Type**: Figtree for all UI text (display + body), JetBrains Mono for data/metrics.
- **Money**: always use `<Aed>` (below) — never hardcode `$` or the letters "AED".

## What's in this folder

| File | Purpose |
|---|---|
| `theme-dewa.css` | The DEWA Astryx theme — Astryx neutral with the accent swapped to DEWA green. `@scope`d to `[data-astryx-theme="dewa"]`. |
| `theme-atelier.css` | The **Atelier** Astryx theme — warm ivory studio + DEWA greens + Poppins. `@scope`d to `[data-astryx-theme="atelier"]`. Alternative skin; see below. |
| `atelier.css` | Atelier component primitives (`.a-*`): pill top-nav, section panels, pastel KPI chips, twin meters, outlined status pills, AI ask-bar. Only needed with the Atelier theme. |
| `dewa.css` | Accent-only override — turn a stock-neutral Astryx app DEWA-green without a full theme swap. |
| `currency.css` | `@font-face` for the dirham glyph + the `.dirham` / `.aed` classes. |
| `Aed.jsx` | `<Aed>` money component + `<Dh />` (bare glyph). `animated` prop rolls the number. |
| `Metric.jsx` | `<Metric>` — animated rolling number for KPI / dashboard figures (wraps NumberFlow). |
| `motion.css` | Native motion layer — View Transitions + scroll-reveal + reduced-motion, 0 KB JS. |
| `rail.css` | Hover-overlay collapsible side rail — desktop icon lane expands as an overlay on hover; touch gets a tap toggle. |
| `useReducedMotionSafe.js` | Hook — live `prefers-reduced-motion` boolean for JS branching. |
| `usePresence.js` | Hook — animate a conditionally-rendered element OUT before it unmounts. |
| `DewaLogo.jsx` | `<DewaLogo />` wordmark + `<DewaMark />` compact green chip (rails / favicons). |

The dirham font lives in `public/fonts` (plus `poppins-*.woff2` for Atelier); the logo in `public/assets`.

## The Atelier theme (alternative skin)

**Atelier** is the second bundled theme: a warm ivory studio dashboard look
(extracted from a reference shot Hadi picked, 2026-07-10) carrying the same two
DEWA greens — dark `#007560` as the exclusive action color (nav pill, buttons,
pagination), light `#33C2A4` as the companion accent (gradients, mint chips,
meter fills) — set in **Poppins**. Full token spec lives in the Atelier spec
artifact: https://claude.ai/code/artifact/01a73bb4-36e3-4978-b7c0-af75c4155589

To switch a project to Atelier (three edits):

1. `index.html`: `data-astryx-theme="atelier"`
2. `main.jsx`: replace the `theme-dewa.css` import with
   `import "./dewa/theme-atelier.css"` + `import "./dewa/atelier.css"`,
   and call `initTheme("atelier")`
3. Keep everything else — `<Aed>`, `currency.css`, motion, rail, mode toggling — unchanged.

Atelier-specific notes:

- **Warm neutrals are the point.** Atelier deliberately swaps the DAK
  cool-neutral rule for warm ivory surfaces; every other house rule still holds
  (borders over shadows, no pure #000/#fff surfaces, both modes shipped, no modals).
- Stock Astryx components re-skin automatically via the theme tokens; the `.a-*`
  primitives in `atelier.css` add the signature Atelier furniture. Both work in
  light **and** dark (`data-astryx-mode`).
- Charts: never use `#007560` as a categorical series color (it sits a hair
  under the chart chroma floor) — use `var(--a-chart-green)` (`#00806A`) for
  series marks; UI chrome keeps the true brand green.

## Currency

```jsx
import { Aed } from './dewa/Aed.jsx'

<Aed usd={1234.5} />            // ê 4,533   (converts USD → AED at 3.6725)
<Aed aed={5000} />             // ê 5,000
<Aed usd={1_200_000} compact />// ê 4.4M
<Aed usd={-50} signed />       // −ê 184
```
In raw HTML (not React), wrap the glyph directly: `<span class="dirham">ê</span>`.
`currency.css` must be loaded for the glyph to resolve (the template loads it in `main.jsx`).

## Motion

Motion is **browser-native and reduced-motion-first**. There is no animation library
in the kit floor — the platform now covers the two jobs the fleet wants, at 0 KB, and
`prefers-reduced-motion` is honoured by default (see `motion.css`). Keep it quiet:
short (~0.3s), ease-out, **no bounce / glow**.

**Dashboard numbers → `<Metric>`. Money → `<Aed animated>`.** Any KPI-card or dashboard
figure should roll rather than pop. Both respect reduced motion and render in Shadow DOM
(no StyleX collision). `<Metric>` (and thus NumberFlow) is tree-shaken out of apps that
never use it.

```jsx
import { Metric } from './dewa/Metric.jsx'
<Metric value={41200000} />                            // 41,200,000  (rolls per digit)
<Metric value={0.92} format={{ style: 'percent' }} />  // 92%
<Metric value={hrs} suffix=" h" />                     // 318 h
<Aed aed={512400} animated />                           // ê 512,400   (money, rolls)
```

**Route transitions** are automatic: navigate with the View Transitions flag and pages
cross-fade quietly (already wired in `App.jsx`):

```jsx
navigate(path, { viewTransition: true })   // imperative
<Link to={path} viewTransition>…</Link>    // declarative
```

**Shared-element morph** (a list card that *morphs* into its detail hero) — name the same
element on both views, only during the transition, via `useViewTransitionState`:

```jsx
import { Link, useViewTransitionState } from 'react-router-dom'
function Card({ to, title }) {
  const active = useViewTransitionState(to)                 // true while morphing to `to`
  return (
    <Link to={to} viewTransition>
      <h3 style={{ viewTransitionName: active ? 'dewa-morph' : 'none' }}>{title}</h3>
    </Link>
  )
}
// …and on the detail view's hero, name the matching element `dewa-morph` the same way.
```

**Scroll reveal** — add the class, that's it (pure CSS, off the main thread):

```jsx
<Card className="dewa-reveal">…</Card>   // fades + rises as it scrolls into view
```

**Exit animations** for a conditionally-rendered panel/toast (the one thing native
transitions don't cover on stable React) — `usePresence`:

```jsx
const { mounted, motion } = usePresence(isOpen)
return mounted && <aside data-motion={motion} className="panel">…</aside>
```

**Reduced motion** is automatic. Reach for `useReducedMotionSafe()` only when you must
branch in JS (e.g. gate a bespoke rAF animation).

> Heavier motion (a scrubbable timeline like an F1 replay, complex orchestration) is a
> **per-project opt-in**, not a kit dependency: reach for `anime.js` (MIT, ~9 KB) in that
> one project. Don't add Motion/anime.js to the kit floor.

## Navigation

The side menu is a **hover-overlay rail by default** (`rail.css` + the wiring in
`App.jsx`). On hover-capable devices it sits as a narrow **icon lane** and expands
as an **overlay** on hover / keyboard-focus — the page content never reflows. Touch
devices (no hover) get a **tap toggle** instead, and below the mobile breakpoint the
AppShell drawer takes over. Already wired in the template `App.jsx`:

- The `SideNav` carries `className="dewa-rail"` and a controlled `collapsible`
  driven by hover/focus state.
- `rail.css` pins the nav's lane to the icon width (`--dewa-rail-lane`, default 68px)
  and floats the nav above content so expanding it overlays rather than pushes.

**Custom footer/header content** that won't fit the collapsed lane should render only
when expanded — gate it on the collapse context:

```jsx
import { useSideNavCollapse } from '@astryxdesign/core/SideNav'
function ExpandedOnly({ children }) {
  const { isCollapsed } = useSideNavCollapse()
  return isCollapsed ? null : children
}
// then: <SideNav footer={<ExpandedOnly>{footerStuff}</ExpandedOnly>}>…</SideNav>
```

Tune the collapsed width with `--dewa-rail-lane`. To opt an app OUT, drop the
`dewa-rail` class + `collapsible` prop in `App.jsx` (the sidebar stays full-width).

## House rules

- **Borders over shadows.** Surfaces stay cool-tinted neutrals.
- **No pure black (#000) or pure white (#fff) surfaces** — cool neutrals only; `#fff` is
  reserved for contrast text on filled color.
- **No modals** — use slide-in panels.
- **Ship both modes.** Check light *and* dark before calling UI done.
- No glassmorphism, gradient text, glow borders, or bounce animations.

## Where to go deeper

- **Astryx component APIs** (props, variants, subpaths): the `@astryxdesign/core`
  package — each component is documented at its own subpath. This is the source of
  truth for how a given component behaves.
- **DEWA brand tokens** (the full green scale + semantic tokens): read `theme-dewa.css`.
- **The standalone brand fork** (React + Vue `<Aed>`, logo assets, `preview.html`) lives
  at `~/dewa-design-system` on the kit-maintainer's machine — not needed to build here.

> Source of the green: sampled live from `dewa.gov.ae` (the Enquire button, `#007560`),
> cross-checked against DEWA's brand guidelines (Pigment Green family).
