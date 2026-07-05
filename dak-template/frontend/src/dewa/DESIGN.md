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
| `dewa.css` | Accent-only override — turn a stock-neutral Astryx app DEWA-green without a full theme swap. |
| `currency.css` | `@font-face` for the dirham glyph + the `.dirham` / `.aed` classes. |
| `Aed.jsx` | `<Aed>` money component + `<Dh />` (bare glyph). `animated` prop rolls the number. |
| `Metric.jsx` | `<Metric>` — animated rolling number for KPI / dashboard figures (wraps NumberFlow). |
| `motion.css` | Native motion layer — View Transitions + scroll-reveal + reduced-motion, 0 KB JS. |
| `useReducedMotionSafe.js` | Hook — live `prefers-reduced-motion` boolean for JS branching. |
| `usePresence.js` | Hook — animate a conditionally-rendered element OUT before it unmounts. |
| `DewaLogo.jsx` | `<DewaLogo />` wordmark + `<DewaMark />` compact green chip (rails / favicons). |

The dirham font lives in `public/fonts`; the logo in `public/assets`.

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
