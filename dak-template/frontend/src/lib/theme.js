// DEWA-Astryx theme + light/dark. Two bundled themes:
//   "dewa"    — Astryx neutral + DEWA green (the default)
//   "atelier" — warm ivory studio + DEWA greens + Poppins (import
//               ./dewa/theme-atelier.css + ./dewa/atelier.css in main.jsx,
//               then initTheme("atelier"))
// Only light/dark toggles at runtime. The app owns the mode (no OS switch).
const MODE_KEY = "dewa-mode"

export function getMode() {
  const m = localStorage.getItem(MODE_KEY)
  return m === "dark" || m === "light" ? m : "light"
}
export function applyMode(mode) {
  document.documentElement.setAttribute("data-astryx-mode", mode)
  localStorage.setItem(MODE_KEY, mode)
}
export function toggleMode() {
  const next = getMode() === "dark" ? "light" : "dark"
  applyMode(next)
  return next
}
export function initTheme(theme = "dewa") {
  document.documentElement.setAttribute("data-astryx-theme", theme)
  applyMode(getMode())
}
