<script setup>
// <Aed :value="1234" /> → ê 1,234 — rendered in the UAESymbol font so the
// official UAE Dirham glyph shows correctly in any browser.
//
// The Vue counterpart to the .dirham-symbol CSS utility. Same public API as the
// global ~/design-system component, so markup ports between the two systems.
// Requires the design system's CSS (tokens.css + base.css) to be loaded — that's
// where the UAESymbol @font-face and --font-currency token live.
//
// Usage:
//   <Aed :value="1234" />                   → ê 1,234
//   <Aed :value="1234.50" :decimals="2" />  → ê 1,234.50
//   <Aed :value="0.4" :from-usd="true" />   → ê 1.47   (USD → AED at 3.6725)
//   <Aed :value="999" compact />            → ê 999     (no space)
//   <Aed :value="999" locale="ar-AE" />     → ê ٩٩٩     (Arabic digits)
//
// import Aed, { USD_TO_AED } from "@ds/components/Aed.vue"
import { computed } from "vue"

const props = defineProps({
  value:    { type: Number,  required: true },
  /** 0 for summaries (integer), 2 for line items. */
  decimals: { type: Number,  default: 0 },
  /** Multiply `value` by USD_TO_AED before display. */
  fromUsd:  { type: Boolean, default: false },
  /** Omit the space between symbol and number. */
  compact:  { type: Boolean, default: false },
  /** JS Intl locale, e.g. "en-AE" (default), "ar-AE". */
  locale:   { type: String,  default: "en-AE" },
})

const formatted = computed(() => {
  const v = props.fromUsd ? props.value * USD_TO_AED : props.value
  return v.toLocaleString(props.locale, {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  })
})
</script>

<script>
// UAE central-bank peg, constant since 1997. Keep in sync with tokens.css
// --usd-to-aed (CSS vars aren't readable from JS at compute time).
// Lives in a plain <script> block — top-level `export` is illegal inside
// <script setup> (the Vue compiler rejects the whole component).
export const USD_TO_AED = 3.6725
</script>

<template>
  <span class="aed" :class="{ compact }">
    <span class="aed-symbol" aria-label="AED">&#234;</span>
    <span class="aed-value">{{ formatted }}</span>
  </span>
</template>

<style scoped>
.aed {
  display: inline-flex;
  align-items: baseline;
  gap: 0.3em;
  white-space: nowrap;
}
.aed.compact { gap: 0.15em; }
.aed-symbol {
  /* Pulls the system's glyph font; falls back if used outside the DS. */
  font-family: var(--font-currency, "UAESymbol", sans-serif);
  font-weight: 700;
  color: inherit;
  /* The glyph is optically heavier than Latin digits — trim it a touch. */
  font-size: 0.92em;
}
.aed-value {
  font-family: inherit;
  font-variant-numeric: tabular-nums;
}
</style>
