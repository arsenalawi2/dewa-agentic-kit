<script setup>
/* ──────────────────────────────────────────────────────────────────────────
   <Chart> — EZ × Chart.js adjunct.

   A thin wrapper that themes Chart.js from the design tokens and auto-colors
   datasets from the sanctioned --chart-1…6 sequence. Re-themes itself when the
   app flips light/dark (watches <html> for class / data-theme changes), so you
   never hand-pick a hex in app code.

   Peer deps (the consuming app installs them):  npm i chart.js

   Usage:
     <Chart type="line" :data="{ labels, datasets:[{label:'A', data:[…]}] }" />
     <Chart type="doughnut" :data="{ labels:['Opus','Sonnet'], datasets:[{data:[60,40]}] }" :legend="true" />
     <Chart type="bar" :data="…" :y-format="v => v + 'B'" height="220px" />
   Datasets without colors are auto-assigned; pass your own to override.
   ────────────────────────────────────────────────────────────────────────── */
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from "vue"
import Chart from "chart.js/auto"
import { chartColors, chartBase, alpha } from "./chart-theme.js"

const props = defineProps({
  type: { type: String, default: "line" },
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({}) },
  legend: { type: Boolean, default: true },
  height: { type: String, default: "260px" },
  yFormat: { type: Function, default: null },
  xFormat: { type: Function, default: null },
})

const el = ref(null)
let chart = null
let observer = null

function isMixOf(t) { return t === "doughnut" || t === "pie" || t === "polarArea" }

// give every uncolored dataset a token color, by kind
function paint(data, c, type) {
  const out = { ...data, datasets: (data.datasets || []).map((d, i) => {
    const ds = { ...d }
    const col = c.series[i % c.series.length]
    if (isMixOf(type)) {
      if (!ds.backgroundColor) ds.backgroundColor = (data.labels || ds.data || []).map((_, k) => c.series[k % c.series.length])
      if (!ds.borderColor) ds.borderColor = c.surface
      if (ds.borderWidth == null) ds.borderWidth = 3
    } else if (type === "bar") {
      if (!ds.backgroundColor) ds.backgroundColor = col
      if (ds.borderRadius == null) ds.borderRadius = 4
      if (ds.borderSkipped == null) ds.borderSkipped = false
      if (ds.maxBarThickness == null) ds.maxBarThickness = 28
    } else { // line / area / radar
      if (!ds.borderColor) ds.borderColor = col
      if (!ds.backgroundColor) ds.backgroundColor = alpha(col, 11)
      if (ds.tension == null) ds.tension = 0.35
      if (ds.borderWidth == null) ds.borderWidth = 2
      if (ds.pointRadius == null) ds.pointRadius = 0
      if (ds.pointHoverRadius == null) ds.pointHoverRadius = 4
      if (ds.pointBackgroundColor == null) ds.pointBackgroundColor = col
      if (ds.fill == null) ds.fill = true
    }
    return ds
  }) }
  return out
}

// shallow+1 merge so callers can override plugins/scales without losing base
function merge(base, over) {
  const out = { ...base, ...over }
  for (const k of ["plugins", "scales", "elements", "interaction", "layout"]) {
    if (base[k] || over[k]) out[k] = { ...(base[k] || {}), ...(over[k] || {}) }
  }
  return out
}

function build() {
  const c = chartColors()
  let options = chartBase(c, { legend: props.legend, yFormat: props.yFormat, xFormat: props.xFormat })
  if (isMixOf(props.type)) { delete options.scales; options.cutout = options.cutout || "64%" }
  options = merge(options, props.options)
  return { type: props.type, data: paint(props.data, c, props.type), options }
}

function render() {
  if (chart) { chart.destroy(); chart = null }
  if (el.value) chart = new Chart(el.value, build())
}

onMounted(() => {
  nextTick(render)
  // re-theme on light/dark switch (EZ toggles html.dark or html[data-theme])
  observer = new MutationObserver(() => nextTick(render))
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "data-theme"] })
})
watch(() => [props.type, props.data, props.options], () => nextTick(render), { deep: true })
onBeforeUnmount(() => { if (observer) observer.disconnect(); if (chart) chart.destroy() })
</script>

<template>
  <div class="ez-chart" :style="{ height }"><canvas ref="el" /></div>
</template>

<style scoped>
.ez-chart { position: relative; width: 100%; }
.ez-chart canvas { max-width: 100%; }
</style>
