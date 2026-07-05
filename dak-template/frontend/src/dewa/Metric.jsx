// <Metric> — the DEWA default for any KPI-card / dashboard number.
//
// Wraps @number-flow/react: the figure rolls per-digit (odometer) when its value
// changes, formats through Intl, and respects prefers-reduced-motion out of the
// box. Renders in Shadow DOM, so it never collides with Astryx/StyleX classes.
// Tree-shaken out of any app that never imports it (only dashboard-ish apps pay
// the ~5 KB gz). For money, use <Aed animated> (Aed.jsx) — it composes the real
// dirham glyph with a <Metric>.
//
//   <Metric value={41200000} />                              → 41,200,000
//   <Metric value={104} />                                   → 104
//   <Metric value={0.92} format={{ style: 'percent' }} />    → 92%
//   <Metric value={3500} format={{ notation: 'compact' }} /> → 3.5K
//   <Metric value={hrs} suffix=" h" />                       → 318 h
import NumberFlow from '@number-flow/react'

export function Metric({ value, format, locales = 'en-US', prefix, suffix, trend, className, ...rest }) {
  return (
    <NumberFlow
      value={Number(value) || 0}
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
