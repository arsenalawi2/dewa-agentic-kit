// <Aed> — render an AED amount with the real UAE dirham glyph (requires
// currency.css to be loaded so the .dirham class resolves the UAESymbol font).
//
//   <Aed usd={1234} compact />   → ê 4.5K   (converts USD → AED)
//   <Aed aed={5000} />           → ê 5,000
//   <Aed usd={-50} signed />     → −ê 184
const DIRHAM = 'ê'
const USD_TO_AED = 3.6725

const short = (n) => {
  n = Math.abs(n)
  return n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K' : Math.round(n).toLocaleString('en-US')
}

export function Aed({ usd, aed, compact = false, decimals = 0, signed = false }) {
  const raw = usd !== undefined ? (usd || 0) * USD_TO_AED : (aed || 0)
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
