// useReducedMotionSafe — a live boolean for `prefers-reduced-motion: reduce`.
//
// The native motion layer (motion.css) and NumberFlow already honour reduced
// motion on their own. Reach for this only when you need to branch in JS — e.g.
// skip a bespoke rAF animation, or drop the shared-element name on a morph.
//
//   const reduced = useReducedMotionSafe()
//   if (!reduced) startFancyThing()
import { useSyncExternalStore } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

function subscribe(cb) {
  const mq = window.matchMedia(QUERY)
  mq.addEventListener('change', cb)
  return () => mq.removeEventListener('change', cb)
}

export function useReducedMotionSafe() {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(QUERY).matches,
    () => false, // SSR / no-window: assume motion is allowed
  )
}
