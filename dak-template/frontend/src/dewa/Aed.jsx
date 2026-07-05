// <Aed> — render an AED amount with the real UAE dirham glyph (requires
// currency.css to be loaded so the .dirham class resolves the UAESymbol font).
//
//   <Aed usd={1234} compact />       → ê 4.5K   (converts USD → AED)
//   <Aed aed={5000} />               → ê 5,000
//   <Aed usd={-50} signed />         → −ê 184
//   <Aed aed={5000} animated />      → ê 5,000  (rolls per-digit on change)
//
// `animated` composes the dirham glyph (kept in its own font) with <Metric>, so
// money in a KPI card rolls like every other dashboard number. For non-money
// figures use <Metric> directly.
import { Metric } from './Metric.jsx'

const DIRHAM = 'ê'
const USD_TO_AED = 3.6725

const short = (n) => {
  n = Math.abs(n)
  return n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : Math.round(n).toLocaleString('en-US')
}

export function Aed({ usd, aed, compact = false, decimals = 0, signed = false, animated = false }) {
  const raw = usd !== undefined ? (usd || 0) * USD_TO_AED : (aed || 0)

  // Animated: the dirham glyph stays in its own font; the number rolls in Metric.
  if (animated) {
    const format = compact
      ? { notation: 'compact', maximumFractionDigits: 1 }
      : { minimumFractionDigits: decimals, maximumFractionDigits: decimals }
    if (signed) format.signDisplay = 'always'
    return (
      <span className="aed">
        <span className="dirham" aria-hidden>{DIRHAM}</span>
        <Metric value={raw} format={format} />
      </span>
    )
  }

  const sign = signed ? (raw >= 0 ? '+' : '−') : raw < 0 ? '−' : ''
  const num = compact
    ? short(raw)
    : Math.abs(raw).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  return (
    <span className="aed">
      {sign}
      <span className="dirham" aria-hidden>{DIRHAM}</span>
      <span>{num}</span>
    </span>
  )
}

// Glyph only — keep your own number after it.
export const Dh = () => <span className="dirham" aria-hidden>{DIRHAM}</span>
