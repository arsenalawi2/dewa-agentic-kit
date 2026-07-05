// <Metric> — the DEWA default for any KPI-card / dashboard number.
//
// Wraps @number-flow/react: the figure rolls per-digit (odometer). NumberFlow
// only animates on value CHANGE, so by default <Metric> starts at 0 and rolls
// UP to the value on first mount (the "count up on load" effect) — otherwise a
// statically-rendered number would never move. Pass animateOnMount={false} to
// render the value immediately. Respects prefers-reduced-motion; Shadow-DOM so
// no StyleX collision. Tree-shaken out of apps that don't use it. Money → <Aed animated>.
//
//   <Metric value={41200000} />                              → rolls 0 → 41,200,000
//   <Metric value={104} />                                   → rolls 0 → 104
//   <Metric value={0.92} format={{ style: 'percent' }} />    → 92%
//   <Metric value={hrs} suffix=" h" />                       → 318 h
import { useEffect, useState } from 'react'
import NumberFlow from '@number-flow/react'

export function Metric({ value, format, locales = 'en-US', prefix, suffix, trend, className, animateOnMount = true, ...rest }) {
  const target = Number(value) || 0
  const [display, setDisplay] = useState(animateOnMount ? 0 : target)
  // Roll 0 → value on mount, then roll on any later change (e.g. data loading in).
  useEffect(() => { setDisplay(target) }, [target])
  return (
    <NumberFlow
      value={display}
      format={format}
      locales={locales}
      prefix={prefix}
      suffix={suffix}
      trend={trend}
      respectMotionPreference
      className={['dewa-metric', className].filter(Boolean).join(' ')}
      {...rest}
    />
  )
}
