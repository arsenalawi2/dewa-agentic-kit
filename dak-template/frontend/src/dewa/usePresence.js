// usePresence — animate a conditionally-rendered element OUT before it unmounts.
//
// The native View Transitions API covers route/DOM swaps, but a component that
// toggles on a boolean (a slide-in panel, a toast) needs a brief "closing" phase
// so it can animate away instead of vanishing. This is the ~1 KB local answer to
// that gap on stable React 19 — no animation library required.
//
//   const { mounted, motion } = usePresence(isOpen)
//   return mounted && <aside data-motion={motion} className="panel">…</aside>
//
// Style the phases in motion.css via [data-motion="exiting"] (already wired), or
// per-component. `motion` is 'entering' → 'entered' → 'exiting'.
import { useEffect, useState } from 'react'

export function usePresence(present, { duration = 220 } = {}) {
  const [mounted, setMounted] = useState(present)
  const [motion, setMotion] = useState(present ? 'entered' : 'exiting')

  useEffect(() => {
    if (present) {
      setMounted(true)
      setMotion('entering')
      const id = requestAnimationFrame(() => setMotion('entered'))
      return () => cancelAnimationFrame(id)
    }
    setMotion('exiting')
    const id = setTimeout(() => setMounted(false), duration)
    return () => clearTimeout(id)
  }, [present, duration])

  return { mounted, motion }
}
