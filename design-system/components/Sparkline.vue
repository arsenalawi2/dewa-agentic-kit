<script setup>
// <Sparkline :values="[3, 8, 5, 12]" /> — tiny inline trend chart.
//
// Vue adjunct to the design system (like Aed.vue). Dependency-free SVG:
// area + polyline + per-point dots with <title> tooltips. Colors come from
// the --chart-* tokens, so light/dark theming is automatic.
//
// Props:
//   values  number[]  required — raw series, normalized internally
//   labels  string[]  optional — per-point tooltip labels
//   format  Function  optional — formats the value inside the tooltip
//   height  Number    default 32 — rendered height in px (width fills parent)
import { computed } from "vue"

const props = defineProps({
  values: { type: Array, required: true },
  labels: { type: Array, default: null },
  format: { type: Function, default: null },
  height: { type: Number, default: 32 },
})

const W = 120
const H = 40
const PAD = 4

const pts = computed(() => {
  const vals = (props.values || []).map(Number)
  if (!vals.length) return []
  const min = Math.min(...vals)
  const max = Math.max(...vals)
  const span = max - min || 1
  return vals.map((v, i) => ({
    x: Math.round((vals.length > 1 ? i / (vals.length - 1) : 0.5) * W * 10) / 10,
    y: Math.round((H - PAD - ((v - min) / span) * (H - 2 * PAD)) * 10) / 10,
  }))
})

const polyline = computed(() => pts.value.map(p => `${p.x},${p.y}`).join(" "))

const areaPath = computed(() => {
  const p = pts.value
  if (!p.length) return ""
  const last = p[p.length - 1]
  return `M ${p.map(pt => `${pt.x},${pt.y}`).join(" L ")} L ${last.x},${H} L ${p[0].x},${H} Z`
})

function titleFor(i) {
  const v = props.format ? props.format(props.values[i]) : props.values[i]
  return props.labels?.[i] ? `${props.labels[i]}: ${v}` : String(v)
}
</script>

<template>
  <svg
    :viewBox="`0 0 ${W} ${H}`" :style="{ height: height + 'px' }"
    class="sparkline" preserveAspectRatio="none" role="img"
  >
    <path :d="areaPath" class="area" />
    <polyline :points="polyline" class="line" />
    <circle v-for="(p, i) in pts" :key="i" :cx="p.x" :cy="p.y" r="2.5" class="dot">
      <title>{{ titleFor(i) }}</title>
    </circle>
  </svg>
</template>

<style scoped>
.sparkline { display: block; width: 100%; overflow: visible; }
.area { fill: var(--chart-1); opacity: 0.12; }
.line {
  fill: none; stroke: var(--chart-1); stroke-width: 1.5;
  stroke-linejoin: round; stroke-linecap: round;
}
.dot { fill: var(--chart-1); stroke: var(--color-surface); stroke-width: 1; }
.dot:hover { r: 4; }
</style>
