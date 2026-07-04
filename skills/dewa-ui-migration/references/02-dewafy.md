# Phase 2 — DEWA-fy (React + Astryx, branded DEWA)

**Goal:** a running React 19 + Astryx shell themed in DEWA brand, so the fix agents in Phase 3 build on real components + tokens.

## Stack

- **React 19 + Vite + React Router** (`createHashRouter` — the board is served as static files behind a tunnel, hash routing avoids server rewrites).
- **Astryx** — `@astryxdesign/core` (npm, MIT, React + StyleX). Components import one-per-subpath: `import { Button } from '@astryxdesign/core/Button'`. Shell = `AppShell` + `SideNav`.
- **Theme layers**, loaded in this order in `main.jsx`:
  ```js
  import '@astryxdesign/core/reset.css'
  import '@astryxdesign/core/astryx.css'
  import '@astryxdesign/theme-neutral/theme.css'   // base tokens (incl. a GENERIC green)
  import './styles/themes.css'                       // light/dark via data-astryx-mode
  import './styles/dewa.css'                          // ← DEWA brand override (assets/dewa.css)
  import './styles/currency.css'                      // AED dirham @font-face
  import './styles/app.css'                           // thin layout glue only
  ```
- `<html data-astryx-theme="dewa" data-astryx-mode="light">`. The app OWNS its mode (a JS toggle), no OS auto-switch.

## DEWA brand tokens — the whole point

Astryx's neutral theme ships a **generic** green (`--color-background-green: #c5e5c0`, `--color-text-green: #0c5700`, `--color-success: #007004`). If you only override the accent, every `variant="green"` surface, success badge, and green icon stays off-brand. **Override the whole green/success family too.** Copy `assets/dewa.css` — it sets, scoped to `html[data-astryx-theme]` with `!important`:

- Accent: `--color-accent`, `--color-accent-muted`, `--color-text-accent`, `--color-icon-accent` → DEWA green `light-dark(#007560, #33c2a4)`.
- Green/success family: `--color-success`, `--color-success-muted`, `--color-background-green`, `--color-border-green`, `--color-icon-green`, `--color-text-green` → the same DEWA green family.

The DEWA green is **#007560** (light) / **#33c2a4** (dark) — sampled from the "Enquire" button on dewa.gov.ae (NOT the documented `#00A651`; use the button color). Use `light-dark()` so dark mode gets the brighter green.

**Gotcha:** SVG `fill=` presentation ATTRIBUTES don't resolve CSS `var()`. Any categorical color used as an SVG fill attribute (e.g. a tier-color returned from a util and passed to `<circle fill={c}>`) must stay a **hex**, not a token. Use tokens for CSS `style`/`color-mix` contexts; hex for SVG attributes.

## Typography + currency + logo

- **Fonts:** Figtree for all UI text (display + body), JetBrains Mono for data/metrics. Preconnect Google Fonts in `index.html`.
- **Currency (AED):** the app is dirham-first. Ship `src/kit/Aed.jsx` (`<Aed usd={n} compact />` converts USD→AED at 3.6725 and renders the dirham glyph) + `currency.css` (`@font-face` for the UAESymbol font, glyph at codepoint `ê`). Never hardcode `$` or the letters "AED". In raw HTML use `<span class="dirham">ê</span>`.
- **Logo:** the DEWA assets live at `~/dewa-design-system/assets/` — `dewa-logo.png` (wordmark, 501×120, transparent) and `dewa-logo-small.png` (swirl mark, 440×440, transparent). Copy into `public/assets/`.
  - **Sidebar brand + favicon:** use the SWIRL MARK — it's multicolor-on-transparent, so it's legible on any surface in light AND dark. `<img src="/assets/dewa-mark.png" width=30 height=30 style="object-fit:contain">`.
  - **Login / letterhead:** the WORDMARK has black lettering → invisible on dark surfaces. Only use it on a **white chip** (`background:#fff; border-radius; padding`), never bare.

## Astryx component gotchas

- **`<Avatar size>` only accepts `small | medium | large` or a number** — NOT `sm/md/lg`. An invalid size returns `undefined` and StyleX throws `styleq: … typeof undefined is not "string" or "null"` at runtime (build stays green). `Button size="sm"` IS valid — don't blanket-replace.
- Prefer Astryx primitives (`Card`, `Table`, `Badge`, `Banner`, `SegmentedControl`, `HStack`/`VStack`, `Text`) over bespoke markup. Borders over shadows. Cool-neutral surfaces. No pure `#000`/`#fff` surfaces (white only as contrast text on filled color). No modals — slide-in panels.

## Scaffold shortcut

`dak init <name>` scaffolds a React+Astryx+DEWA app with all of the above already wired (theme, `<Aed>`, logo, the 5 auto-pages). If the target is greenfield, start there and skip most of this phase.
