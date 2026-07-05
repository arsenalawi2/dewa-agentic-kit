import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"

// ── DEWA-Astryx design system — CSS cascade (order matters) ──────────────
//  1. reset.css      — normalize
//  2. astryx.css     — Astryx design system (tokens + component CSS)
//  3. theme-dewa.css — the DEWA theme (Astryx neutral + DEWA green #007560),
//                      scoped to [data-astryx-theme="dewa"] (set on <html>)
//  4. currency.css   — the AED dirham glyph (.dirham / <Aed>)
//  5. themes.css     — light/dark via color-scheme (data-astryx-mode on <html>)
//  6. motion.css     — native motion layer (View Transitions + scroll reveals),
//                      reduced-motion by default, 0 KB JS
//  7. app.css        — thin app-level layout glue (never re-styles Astryx comps)
import "@astryxdesign/core/reset.css"
import "@astryxdesign/core/astryx.css"
import "./dewa/theme-dewa.css"
import "./dewa/currency.css"
import "./dewa/motion.css"
import "./dewa/rail.css"
import "./styles/themes.css"
import "./styles/app.css"

import { router } from "./app/router.jsx"
import { initTheme } from "./lib/theme.js"

initTheme()

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
