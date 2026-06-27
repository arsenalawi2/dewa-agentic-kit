/* ──────────────────────────────────────────────────────────────────────────
   EZ × motion-v — sanctioned motion presets.

   The design system's motion rule is "quiet": ~120ms ease-out, panels slide,
   nothing bounces/glows. These presets encode that for motion-v so app code
   stays on-brand instead of hand-tuning springs. Mirrors the CSS tokens in
   tokens.css (--dur-*, --ease-out, --dur-panel).

   Peer deps (the consuming app installs them):  npm i motion-v

   Usage:
     import { motion } from "motion-v"
     import { riseIn, slideInRight, pressable, tBase } from "@ds/components/motion.js"

     <motion.div v-bind="riseIn">…</motion.div>            // subtle enter
     <motion.aside v-bind="slideInRight">…</motion.aside>  // panel / sheet
     <motion.button v-bind="pressable">Save</motion.button> // tactile press

   Accessibility: motion-v does NOT auto-honor reduced motion. Either gate with
   motion-v's useReducedMotion(), or rely on the CSS guard EZ ships — keep the
   reduced-motion @media block from base.css in place.
   ────────────────────────────────────────────────────────────────────────── */

// EZ ease-out (matches --ease-out: cubic-bezier(0.22, 1, 0.36, 1))
export const EZ_EASE = [0.22, 1, 0.36, 1]

// durations in seconds (mirror --dur-fast/base/slow/panel)
export const dur = { fast: 0.1, base: 0.12, slow: 0.15, panel: 0.18 }

// tween transitions — the default vocabulary (quiet, no overshoot)
export const tFast = { duration: dur.fast, ease: EZ_EASE }
export const tBase = { duration: dur.base, ease: EZ_EASE }
export const tSlow = { duration: dur.slow, ease: EZ_EASE }
export const tPanel = { duration: dur.panel, ease: EZ_EASE }

// a single restrained spring for the rare deliberate moment (no bounce)
export const springQuiet = { type: "spring", stiffness: 380, damping: 34 }

/* ── Enter / exit presets (spread with v-bind) ─────────────────────────── */

// fade only
export const fade = {
  initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 },
  transition: tSlow,
}

// subtle rise — the default for cards, rows, content blocks
export const riseIn = {
  initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 4 },
  transition: tBase,
}

// panel / sheet sliding from an edge (EZ prefers panels over modals)
export const slideInRight = {
  initial: { x: "100%" }, animate: { x: 0 }, exit: { x: "100%" }, transition: tPanel,
}
export const slideInLeft = {
  initial: { x: "-100%" }, animate: { x: 0 }, exit: { x: "-100%" }, transition: tPanel,
}

// dialog / toast — quiet pop (small, no overshoot)
export const popIn = {
  initial: { opacity: 0, y: 8, scale: 0.98 }, animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: 6, scale: 0.98 }, transition: springQuiet,
}

/* ── Interaction presets (prop bags) ───────────────────────────────────── */

// tactile press — spread onto any motion button/link
export const pressable = { whileTap: { scale: 0.98 }, transition: tFast }

// quiet hover lift for cards (pair with a shadow change in CSS)
export const hoverLift = { whileHover: { y: -2 }, transition: tBase }

/* Stagger helper for lists: pass index → a transition with a small delay. */
export const stagger = (i, step = 0.03) => ({ ...tBase, delay: i * step })
