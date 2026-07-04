// <DewaLogo /> — the DEWA wordmark logo. Point `src` at the bundled asset
// (assets/dewa-logo.png) or your app's public path.
export function DewaLogo({ src = '/assets/dewa-logo.png', height = 40, alt = 'Dubai Electricity & Water Authority', ...rest }) {
  return <img src={src} alt={alt} height={height} style={{ height, width: 'auto', display: 'block' }} {...rest} />
}

// <DewaMark /> — a compact DEWA green brand chip (swirl-inspired) for favicons /
// small rail marks where the full wordmark won't fit.
export function DewaMark({ size = 32 }) {
  return (
    <span style={{
      width: size, height: size, borderRadius: 8, display: 'inline-grid', placeItems: 'center', flex: 'none',
      background: 'radial-gradient(circle at 32% 30%, #33c2a4, #007560 62%, #005445)',
    }} aria-hidden>
      <svg viewBox="0 0 24 24" width={size * 0.6} height={size * 0.6} fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round">
        <path d="M6 18a8 8 0 1 1 11-11" />
        <path d="M18 8a6 6 0 1 1-9 7.5" opacity="0.75" />
      </svg>
    </span>
  )
}
