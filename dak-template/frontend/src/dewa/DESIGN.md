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
| `Aed.jsx` | `<Aed>` money component + `<Dh />` (bare glyph). |
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
