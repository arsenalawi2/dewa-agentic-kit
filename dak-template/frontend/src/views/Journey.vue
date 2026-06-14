<script setup>
// /journey — reads public/journey-data.json (unified schema; see
// ~/.claude/templates/journey.md). Renders the phases timeline (the always-
// present spine) plus optional rich blocks (hero stats / challenge / features /
// tech stats), each v-if-guarded so both old phases-only files and rich files
// render. Tolerant-rendering pattern, like Architecture.vue.
import { ref, computed, onMounted } from "vue"

const data = ref(null)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await fetch("/journey-data.json")
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = await res.json()
  } catch (e) {
    error.value = e.message
  }
})

const title = computed(() => data.value?.project_name || "Journey")
const tagline = computed(() => data.value?.tagline || "")
const heroStats = computed(() => data.value?.hero_stats || [])
const phases = computed(() => data.value?.phases || [])
const challenge = computed(() => data.value?.challenge || null)
const features = computed(() => data.value?.features || [])
const techStats = computed(() => {
  const t = data.value?.tech_stats
  return t && Object.keys(t).length ? Object.entries(t) : []
})
const updated = computed(() => {
  const u = data.value?.updated_at
  if (!u) return ""
  const d = new Date(u)
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString()
})
const isEmpty = computed(() =>
  !phases.value.length && !heroStats.value.length && !challenge.value &&
  !features.value.length && !techStats.value.length)
</script>

<template>
  <div class="page">
    <header class="head">
      <div class="eyebrow">Narrative</div>
      <h1>{{ title }}</h1>
      <p v-if="tagline" class="lead">{{ tagline }}</p>
    </header>

    <div v-if="error" class="state error">Couldn't load: {{ error }}</div>
    <div v-else-if="!data" class="state">Loading journey…</div>
    <div v-else-if="isEmpty" class="state">No journey yet.</div>
    <template v-else>
      <div v-if="heroStats.length" class="stats">
        <div v-for="(s, i) in heroStats" :key="i" class="stat">
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>

      <section v-if="challenge" class="block">
        <h2>{{ challenge.title || "The challenge" }}</h2>
        <p class="block-body">{{ challenge.description }}</p>
        <div v-if="challenge.stats && challenge.stats.length" class="stats sm">
          <div v-for="(s, i) in challenge.stats" :key="i" class="stat">
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </section>

      <section v-if="phases.length" class="block">
        <h2>How it came together</h2>
        <ol class="phases">
          <li v-for="p in phases" :key="p.number ?? p.title" class="phase">
            <div class="phase-num">{{ p.number }}</div>
            <div>
              <div class="phase-title">{{ p.title }}</div>
              <p class="phase-body">{{ p.body }}</p>
            </div>
          </li>
        </ol>
      </section>

      <section v-if="features.length" class="block">
        <h2>Features</h2>
        <div class="features">
          <div v-for="(f, i) in features" :key="i" class="feature">
            <div class="feature-title">{{ f.title }}</div>
            <p class="feature-desc">{{ f.description }}</p>
          </div>
        </div>
      </section>

      <section v-if="techStats.length" class="block">
        <h2>By the numbers</h2>
        <div class="stats sm">
          <div v-for="[k, v] in techStats" :key="k" class="stat">
            <div class="stat-value">{{ v }}</div>
            <div class="stat-label">{{ k.replace(/_/g, " ") }}</div>
          </div>
        </div>
      </section>

      <p v-if="updated" class="updated">Last updated {{ updated }}</p>
    </template>
  </div>
</template>

<style scoped>
.page { max-width: 760px; }
.head { margin-bottom: 24px; }
.eyebrow {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: var(--text-accent);
}
h1 { font-family: var(--font-display); font-size: 32px; margin: 6px 0 10px; }
.lead { opacity: 0.78; line-height: 1.5; }
.state { padding: 40px; text-align: center; opacity: 0.7; }
.state.error { color: #c44; }
.block { margin-top: 32px; }
.block h2 {
  font-family: var(--font-display);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--text-tertiary);
  margin: 0 0 14px;
}
.block-body { opacity: 0.85; line-height: 1.55; }
.stats { display: flex; flex-wrap: wrap; gap: 14px; }
.stat {
  flex: 1 1 120px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 14px 16px;
}
.stats.sm .stat { padding: 10px 12px; }
.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-accent);
}
.stats.sm .stat-value { font-size: 20px; }
.stat-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  opacity: 0.65;
  margin-top: 2px;
}
.phases { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 14px; margin: 0; }
.phase {
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--border-light);
  border-radius: 8px;
}
.phase-num { font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--text-accent); }
.phase-title { font-weight: 600; font-family: var(--font-display); }
.phase-body { margin-top: 6px; opacity: 0.82; line-height: 1.5; }
.features { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.feature { border: 1px solid var(--border-light); border-radius: 8px; padding: 14px; }
.feature-title { font-weight: 600; font-family: var(--font-display); }
.feature-desc { margin-top: 5px; opacity: 0.82; line-height: 1.5; font-size: 14px; }
.updated { margin-top: 28px; font-size: 12px; opacity: 0.55; }
</style>
