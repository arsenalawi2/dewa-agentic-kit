<script setup>
// Worked-example reusable component — a labelled stat built from
// design-system classes (.card, .mono) and tokens. Copy this shape for
// your own components; keep each under the 250-line SFC cap.
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: "—" },
})
</script>

<template>
  <div class="card stat-card">
    <div class="stat-card__label">{{ label }}</div>
    <div class="stat-card__value mono">{{ value }}</div>
  </div>
</template>

<style scoped>
.stat-card { padding: 16px 18px; }
.stat-card__label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--text-tertiary);
}
.stat-card__value { font-size: 26px; font-weight: 700; margin-top: 4px; }
</style>
