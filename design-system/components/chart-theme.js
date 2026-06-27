/* ──────────────────────────────────────────────────────────────────────────
   EZ × Chart.js — theme bridge.

   Reads the design system's existing tokens (--chart-1…6, --chart-grid,
   --chart-label, --color-*, --font-*) so any chart inherits the warm-neutral
   identity and flips with light/dark automatically. Framework-agnostic:
   use it with the <Chart> Vue adjunct, or with vanilla Chart.js.

   Usage (vanilla):
     import { chartColors, chartBase } from "./chart-theme.js"
     const c = chartColors()
     new Chart(ctx, { type:"line", data, options: chartBase(c, { yFormat:v=>v+"%" }) })

   Re-read after a theme change (the <Chart> adjunct does this for you).
   ────────────────────────────────────────────────────────────────────────── */

function readVar(root, name, fallback = "") {
  const v = getComputedStyle(root).getPropertyValue(name).trim()
  return v || fallback
}

// color-mix lets one token become a translucent fill without a second token.
// Supported in Chrome 111+/Safari 16.2+/Firefox 113+ (canvas included).
export const alpha = (color, pct) => `color-mix(in oklab, ${color} ${pct}%, transparent)`

export function chartColors(root = document.documentElement) {
  return {
    // the sanctioned categorical sequence
    series: [1, 2, 3, 4, 5, 6].map((i) => readVar(root, `--chart-${i}`)),
    grid: readVar(root, "--chart-grid"),
    label: readVar(root, "--chart-label"),
    text: readVar(root, "--color-text"),
    surface: readVar(root, "--color-surface", "#ffffff"),
    border: readVar(root, "--color-border"),
    primary: readVar(root, "--color-primary"),
    fontSans: readVar(root, "--font-sans", "Inter, sans-serif"),
    fontMono: readVar(root, "--font-mono", "monospace"),
    alpha,
  }
}

/* Clean, chart-junk-free defaults in the EZ spirit: hairline gridlines, no
   plot border, restrained ticks, tabular-mono numerals, a card-styled tooltip,
   point-style legend. Pass { legend:false } or tick formatters to tweak. */
export function chartBase(c, { legend = true, yFormat, xFormat } = {}) {
  const mono = { family: c.fontMono, size: 11 }
  const sans = { family: c.fontSans, size: 12 }
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: legend
        ? { position: "bottom", align: "start",
            labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 7, boxHeight: 7,
              padding: 16, color: c.label, font: sans } }
        : { display: false },
      tooltip: {
        backgroundColor: c.surface, titleColor: c.label, bodyColor: c.text,
        borderColor: c.border, borderWidth: 1, padding: 10, cornerRadius: 8,
        boxPadding: 4, usePointStyle: true,
        titleFont: { ...sans, weight: "600" }, bodyFont: mono, displayColors: true,
      },
    },
    scales: {
      x: { stacked: false, grid: { display: false }, border: { display: false },
        ticks: { color: c.label, font: mono, maxRotation: 0, autoSkip: true, maxTicksLimit: 8,
          callback: xFormat || undefined } },
      y: { stacked: false, grid: { color: c.grid, drawTicks: false }, border: { display: false },
        ticks: { color: c.label, font: mono, maxTicksLimit: 5, padding: 8,
          callback: yFormat || undefined }, beginAtZero: true },
    },
  }
}

// Sensible dataset shapers so app code stays short.
export const lineSeries = (c, label, data, i) => ({
  label, data, borderColor: c.series[i], backgroundColor: c.alpha(c.series[i], 11),
  fill: true, tension: 0.35, borderWidth: 2, pointRadius: 0, pointHoverRadius: 4,
  pointBackgroundColor: c.series[i],
})
export const barSeries = (c, label, data, i, { stack } = {}) => ({
  label, data, backgroundColor: c.series[i], borderRadius: 4, borderSkipped: false,
  maxBarThickness: 28, ...(stack ? { stack } : {}),
})
